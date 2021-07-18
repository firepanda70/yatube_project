from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Title', max_length=200)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Description')

    class Meta:
        verbose_name = 'Group'

    def __str__(self):
        return str(self.title)


class Post(models.Model):
    text = models.TextField('Text')
    pub_date = models.DateTimeField('Publication day', auto_now_add=True)
    author = models.ForeignKey(
        User,
        verbose_name='Author',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts'
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Post'

    def __str__(self):
        return str(self.text)
