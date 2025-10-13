"""
Базовая абстрактная модель для "мягкого удаления".
"""

from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Кастомный менеджер моделей, для реализации "мягкого удаления".
    Предоставляет доступ только к тем записям, которые не были "удалены".
    """

    def get_queryset(self) -> models.QuerySet:
        """Возвращает QuerySet, исключая удаленные записи."""
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    """
    Абстрактная базовая модель, предоставляющая функциональность "мягкого удаления".
    Включает общие поля is_deleted, created_at, deleted_at и updated_at.
    И два менеджера:
        - objects: возвращает только активные (не удаленные) записи.
        - all_objects: возвращает все записи, включая удаленные.
    """

    is_deleted = models.BooleanField(default=False, verbose_name="Удалено")

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")

    # Менеджеры
    objects = SoftDeleteManager()  # Это менеджер по умолчанию для всех моделей, наследующих BaseModel.
    all_objects = models.Manager()  # Полезно для восстановления данных.

    class Meta:
        # Указываем, что эта модель является абстрактной.
        # Для нее не будет создаваться отдельная таблица в базе данных.
        abstract = True

    def soft_delete(self) -> None:
        """
        Выполняет "мягкое удаление" объекта.
        Устанавливает флаг is_deleted в True и сохраняет время удаления.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self) -> None:
        """
        Восстанавливает "мягко удаленный" объект.
        Устанавливает флаг is_deleted в False и сбрасывает время удаления.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save()
