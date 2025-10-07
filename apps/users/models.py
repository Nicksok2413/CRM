"""
Модуль содержит кастомную модель пользователя.
"""
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.common.utils import create_image_directory_path
from apps.common.validators import validate_image_size


class User(AbstractUser):
    """
    Кастомная модель пользователя.

    Наследуется от AbstractUser, сохраняя всю стандартную функциональность
    аутентификации Django, но позволяет добавлять дополнительные поля.
    Отвечает только за аутентификацию и базовую идентификацию (ФИО, email).
    """
    # Добавляем необязательное поле "Отчество"
    patronymic = models.CharField(max_length=150, blank=True, verbose_name="Отчество")

    def __str__(self) -> str:
        """
        Возвращает строковое представление пользователя.
        Если ФИО заполнено, возвращает его, иначе - username.
        """
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        return self.username


class Profile(models.Model):
    """
    Модель профиля пользователя. Хранит всю дополнительную информацию,
    не связанную напрямую с аутентификацией.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )

    # Добавляем необязательное поле "Должность"
    position = models.CharField(max_length=200, blank=True, verbose_name="Должность")

    photo = models.ImageField(
        upload_to=create_image_directory_path,
        blank=True,
        null=True,
        verbose_name="Фото",
        validators=[
            validate_image_size,
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
        ]
    )

    def __str__(self) -> str:
        return f"Профиль пользователя {self.user.username}"

    class Meta:
        verbose_name: str = "Профиль"
        verbose_name_plural: str = "Профили"