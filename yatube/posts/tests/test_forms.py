"""
Модуль предназначен для тестирования страниц с формами.
"""
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

TEST_USER_USERNAME = 'amogus'
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
TEST_IMAGE_NAME = 'small.gif'
TEST_IMAGE_TYPE = 'image/gif'
TEST_DIR = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username=TEST_USER_USERNAME)
        cls.group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            description=TEST_GROUP_DESC,
            slug=TEST_GROUP_SLUG
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_DIR, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """
        Тест проверяет, работает ли форма для создания поста.
        """
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name=TEST_IMAGE_NAME,
            content=TEST_IMAGE,
            content_type=TEST_IMAGE_TYPE
        )
        group = PostCreateFormTests.group.pk
        form_data = {
            'text': TEST_POST_TEXT,
            'group': group,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.get(
            text=TEST_POST_TEXT,
            group_id=group,
            image='posts/' + TEST_IMAGE_NAME,
            author_id=1))

    def test_edit_post(self):
        """
        Тест проверяет, работает ли форма для редактирования поста.
        """
        form_data = {
            'text': 'Обновленный текст',
            'group-id': 1
        }
        Post.objects.create(text='Текст',
                            group=PostCreateFormTests.group,
                            author=PostCreateFormTests.user)
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'username': 'amogus', 'post_id': 1}),
            data=form_data
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'username': 'amogus', 'post_id': 1}))

        self.assertEqual(Post.objects.get(pk=1).text, form_data['text'])
