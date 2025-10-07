"""
Вспомогательные утилиты и функции для всего проекта.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import Model


def create_image_directory_path(instance: "Model", filename: str) -> str:
    """
    Создает унифицированный, динамический путь для сохранения изображений.

    Файлы будут сохраняться по пути:
    MEDIA_ROOT/<app_label>/<model_name>s/<instance_id>/<filename>

    Args:
        instance: Экземпляр модели изображения (ProductImage, Avatar, или CategoryImage).
        filename: Исходное имя файла.

    Returns:
        Сгенерированный путь к файлу.
    """
    app_label = instance.__class__._meta.app_label
    model_name = instance.__class__.__name__.lower()

    return f"{app_label}/{model_name}s/{instance.pk}/{filename}"