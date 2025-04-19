from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from foodgram.constants import (
    USER_AVATAR_UPLOAD_TO,
    USER_EMAIL_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
    USER_USERNAME_MAX_LENGTH,
    USER_USERNAME_REGEX
)


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    email = models.EmailField(
        verbose_name="Электронная почта",
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
        }
    )
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=USER_USERNAME_MAX_LENGTH,
        unique=True,
        db_index=True,
        validators=[RegexValidator(regex=USER_USERNAME_REGEX)],
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=USER_FIRST_NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=USER_LAST_NAME_MAX_LENGTH,
    )
    avatar = models.ImageField(
        verbose_name="Аватар пользователя",
        upload_to=USER_AVATAR_UPLOAD_TO,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"],
                name="unique_user_following"
            )
        ]
        ordering = ("user",)

    def __str__(self):
        return f"{self.user} подписчик автора - {self.following}"
