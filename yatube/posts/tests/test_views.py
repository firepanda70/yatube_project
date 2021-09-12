"""
Модуль предназначен для тестирования view-функций.
"""
import datetime as dt
import shutil
import tempfile
from math import ceil

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User

UTF_OFFSET = dt.datetime.utcnow()
# меньше 1 рабоать не будет :)
POSTS_COUNT = 15
POST_PER_PAGE_COUNT = 10

TEST_USER1_USERNAME = 'amogus1'
TEST_USER2_USERNAME = 'amogus2'
TEST_GROUP_TITLE = 'Заголовок'
TEST_GROUP_SLUG = 'test-slug'
TEST_GROUP_DESC = 'Описание'
TEST_POST_TEXT = 'Текст'
TEST_EMPTY_GROUP_SLUG = 'empty_group'
TEST_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)
TEST_IMAGE_NAME = 'small1.gif'
TEST_IMAGE_TYPE = 'image/gif'
TEST_DIR = tempfile.mkdtemp(dir=settings.BASE_DIR)

REQUEST_TEMPLATE_DICT = {
    'homepage': (reverse('posts:index'), 'posts/index.html'),
    'new_post': (reverse('posts:post_create'), 'posts/create_post.html'),
    'group': (reverse('posts:group',
                      kwargs={
                          'slug': TEST_GROUP_SLUG
                      }), 'posts/group.html'),
    'empty_group': (reverse('posts:group',
                            kwargs={
                                'slug': TEST_EMPTY_GROUP_SLUG
                            }), 'posts/group.html'),
    'profile': (reverse('posts:profile',
                        kwargs={
                            'username': TEST_USER1_USERNAME
                        }), 'posts/profile.html'),
    'post_edit': (reverse('posts:post_edit',
                          kwargs={
                              'username': TEST_USER1_USERNAME,
                              'post_id': POSTS_COUNT
                          }), 'posts/create_post.html'),
    'post_detail': (reverse('posts:post_detail',
                            kwargs={
                                'username': TEST_USER1_USERNAME,
                                'post_id': POSTS_COUNT
                            }), 'posts/post_detail.html'),
    'follow': (reverse('posts:profile_follow',
                       kwargs={
                           'username': TEST_USER1_USERNAME
                       }), 'posts/folllow.html'),
    'follow_yourself': (reverse('posts:profile_follow',
                                kwargs={
                                    'username': TEST_USER2_USERNAME
                                }), 'posts/folllow.html'),
    'unfollow': (reverse('posts:profile_unfollow',
                         kwargs={
                             'username': TEST_USER1_USERNAME
                         }), 'posts/folllow.html'),
    'feed': (reverse('posts:follow_index'), 'posts/folllow.html'),
}


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user1 = User.objects.create_user(username=TEST_USER1_USERNAME)
        cls.user2 = User.objects.create_user(username=TEST_USER2_USERNAME)
        cls.group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            description=TEST_GROUP_DESC,
            slug=TEST_GROUP_SLUG
        )
        cls.empty_group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            description=TEST_GROUP_DESC,
            slug=TEST_EMPTY_GROUP_SLUG
        )

        cls.uploaded = SimpleUploadedFile(
            name=TEST_IMAGE_NAME,
            content=TEST_IMAGE,
            content_type=TEST_IMAGE_TYPE
        )
        posts = [Post(author=cls.user1,
                 group=cls.group,
                 text=TEST_POST_TEXT,
                 image=cls.uploaded
                      )] * POSTS_COUNT
        Post.objects.bulk_create(posts)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_DIR, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_is_correct_template(self):
        """
        Тест проверяет, что view-функции используют правильные html шаблоны.
        """
        cache.clear()

        view_names = (
            'homepage',
            'group',
            'profile',
            'post_detail',
            'new_post',
            'post_edit',
        )

        for view_name in view_names:
            reverse_name, template = REQUEST_TEMPLATE_DICT[view_name]
            with self.subTest(template=template):
                response = self.authorized_client1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_form(self):
        """
        Тест проверяет, что форма создания поста имеет ожидаемые поля ввода.
        """
        request = REQUEST_TEMPLATE_DICT['new_post'][0]
        response = self.authorized_client1.get(request)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

        for field_name, value in form_fields.items():
            with self.subTest(field_name=field_name):
                field = response.context['form'].fields[field_name]
                self.assertIsInstance(field, value)

    def test_post_edit_form(self):
        """
        Тест проверяет, что форма редактирования поста заполнена
        актуальными значениями.
        """
        request = REQUEST_TEMPLATE_DICT['post_edit'][0]
        response = self.authorized_client1.get(request)
        form_fields = {
            'text': (forms.fields.CharField, TEST_POST_TEXT),
            'group': (forms.fields.ChoiceField, PostPagesTest.group.pk),
            'image': (forms.fields.ImageField, 'posts/' + TEST_IMAGE_NAME)
        }

        for field_name, values in form_fields.items():
            with self.subTest(field_name=field_name):
                field = response.context['form'].fields[field_name]
                initial = response.context['form'].initial[field_name]
                self.assertIsInstance(field, values[0])
                self.assertEqual(initial, values[1])

    def test_paginator(self):
        """
        Тест проверяет, что страица содержит ожидаемое количество
        элементов.
        """
        left = POSTS_COUNT

        def reqests(page):
            view_names = (
                'homepage',
                'group',
            )
            for view_name in view_names:
                request = REQUEST_TEMPLATE_DICT[view_name][0] + f'?page={page}'
                with self.subTest(request=request):
                    response = self.authorized_client1.get(request)
                    self.assertEqual(
                        len(response.context['page'].object_list),
                        min(left, POST_PER_PAGE_COUNT)
                    )
        reqests(1)
        if left % POST_PER_PAGE_COUNT != 0:
            last_page = ceil(left / POST_PER_PAGE_COUNT)
            left = left % POST_PER_PAGE_COUNT
            reqests(last_page)
        else:
            last_page = left / POST_PER_PAGE_COUNT
            left = POST_PER_PAGE_COUNT
            reqests(last_page)

    def test_pages_context(self):
        """
        Тест проверяет контекст страниц паджинатора.
        """
        cache.clear()

        view_names = (
            'homepage',
            'group',
            'profile',
        )
        for view_name in view_names:
            request = REQUEST_TEMPLATE_DICT[view_name][0]
            with self.subTest(request=request):
                response = self.authorized_client1.get(request)
                post = response.context['page'].object_list[0]
                self.assertEqual(post.text, TEST_POST_TEXT)
                self.assertEqual(post.group.title, TEST_GROUP_TITLE)
                self.assertEqual(post.author.username, TEST_USER1_USERNAME)
                self.assertEqual(post.pub_date.date(),
                                 dt.datetime.utcnow().date())
                self.assertEqual(post.image.name, 'posts/' + TEST_IMAGE_NAME)

    def test_detail_post_info(self):
        """
        Тест проверяет контекст страницы детальной информации поста.
        """
        request = REQUEST_TEMPLATE_DICT['post_detail'][0]
        response = self.authorized_client1.get(request)
        post = response.context['post']
        self.assertEqual(post.text, TEST_POST_TEXT)
        self.assertEqual(post.group.title, TEST_GROUP_TITLE)
        self.assertEqual(post.author.username, TEST_USER1_USERNAME)
        self.assertEqual(post.pub_date.date(),
                         dt.datetime.utcnow().date())
        self.assertEqual(post.image.name, 'posts/' + TEST_IMAGE_NAME)

    def test_empty_group(self):
        """
        Тест проверяет, что в пустой группе нет постов.
        """
        request = REQUEST_TEMPLATE_DICT['empty_group'][0]
        response = self.authorized_client1.get(request)
        self.assertEqual(
            len(response.context['page'].object_list), 0
        )

    def test_cache_duration(self):
        """
        Тест проверяет длительность хранения кешированных значений.
        """
        request = REQUEST_TEMPLATE_DICT['homepage'][0]
        response = self.authorized_client1.get(request)
        self.assertEqual(response['cache-control'], 'max-age=20')

    def test_follow_unfollow(self):
        """
        Тест проверяет работу функции подписки/отписки
        """
        request = REQUEST_TEMPLATE_DICT['follow'][0]
        self.authorized_client2.get(request)
        feed_request = REQUEST_TEMPLATE_DICT['feed'][0]
        response = self.authorized_client2.get(feed_request)
        self.assertEqual(len(response.context['page']),
                         min(POSTS_COUNT, POST_PER_PAGE_COUNT))
        request = REQUEST_TEMPLATE_DICT['unfollow'][0]
        self.authorized_client2.get(request)
        response = self.authorized_client1.get(feed_request)
        self.assertFalse(len(response.context['page']), 0)

    def test_is_empty_feed(self):
        """
        Тест проверяет, что в ленте подписок не появляются лишние записи
        """
        request = REQUEST_TEMPLATE_DICT['follow'][0]
        self.authorized_client2.get(request)
        request = REQUEST_TEMPLATE_DICT['feed'][0]
        response = self.authorized_client1.get(request)
        self.assertEqual(len(response.context['page']), 0)
        self.authorized_client2.get(REQUEST_TEMPLATE_DICT['unfollow'][0])

    def test_follow_yourself_forbidden(self):
        """
        Тест проверяет, что нельзя подписаться на себя
        """
        request = REQUEST_TEMPLATE_DICT['follow_yourself'][0]
        self.authorized_client2.get(request)
        user2 = PostPagesTest.user1
        self.assertFalse(Follow.objects.filter(
                         user=user2, author=user2).exists())
