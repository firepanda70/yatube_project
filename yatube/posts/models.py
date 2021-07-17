from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField('Text')
    pub_date = models.DateTimeField('Publication day', auto_now_add=True)
    author = models.ForeignKey(
        User,
        verbose_name='Author',
        on_delete=models.CASCADE,
        related_name='posts'
    )

    class Meta:
        ordering = ['pub_date']

    def __str__(self):
        return 'Post #' + self.pk
