"""
Кастомные валидаторы для всего проекта.
"""

from django.core.exceptions import ValidationError


def validate_image_size(file):
    """
    Валидатор для проверки размера файла изображения.
    """
    MAX_IMAGE_SIZE_MB = 2
    file_size = file.size

    if file_size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Максимальный размер файла не должен превышать {MAX_IMAGE_SIZE_MB} МБ.")