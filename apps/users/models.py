"""
Модуль содержит кастомную модель пользователя.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.common.utils import create_dynamic_upload_path
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
        Приоритет: Полное ФИО -> Фамилия и Имя -> username.
        """
        # Собираем части имени, которые не являются пустыми строками
        full_name_parts = [self.last_name, self.first_name, self.patronymic]
        valid_parts = [part for part in full_name_parts if part]

        # Если есть хотя бы Фамилия и Имя, соединяем их
        if len(valid_parts) >= 2:
            return " ".join(valid_parts)

        # В противном случае возвращаем username
        return self.username


class Profile(models.Model):
    """
    Модель профиля пользователя. Хранит всю дополнительную информацию,
    не связанную напрямую с аутентификацией.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="profile",
        verbose_name="Пользователь",
    )

    # Добавляем необязательное поле "Должность"
    position = models.CharField(max_length=200, blank=True, verbose_name="Должность")

    photo = models.ImageField(
        upload_to=create_dynamic_upload_path,
        blank=True,
        null=True,
        verbose_name="Фото",
        validators=[
            validate_image_size,
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"]),
        ],
    )

    def __str__(self) -> str:
        return f"Профиль пользователя {self.user.username}"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"
