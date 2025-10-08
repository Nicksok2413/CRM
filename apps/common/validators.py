"""
Кастомные валидаторы для всего проекта.
"""

import phonenumbers

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def create_file_size_validator(max_size_mb: int):
    """
    Фабричная функция, которая создает и возвращает валидатор размера файла.
    """

    def validate_file_size(file):
        if file.size > max_size_mb * 1024 * 1024:
            raise ValidationError(f"Максимальный размер файла не должен превышать {max_size_mb} МБ.")

    return validate_file_size


# Создаем конкретные валидаторы с помощью фабрики
validate_image_size = create_file_size_validator(max_size_mb=settings.MAX_IMAGE_SIZE_MB)
validate_document_size = create_file_size_validator(max_size_mb=settings.MAX_DOCUMENT_SIZE_MB)

# Валидатор для полей, где должны быть только буквы и дефис (ФИО)
validate_letters_and_hyphens = RegexValidator(
    r'^[а-яА-ЯёЁa-zA-Z\s-]+$',
    message='Это поле может содержать только буквы, пробелы и дефисы.'
)


def validate_international_phone_number(value: str):
    """
    Валидирует международный телефонный номер с помощью библиотеки phonenumbers.
    Проверяет, является ли номер валидным для региона по умолчанию или
    если он указан в международном формате.
    """
    try:
        # Пытаемся распарсить номер. Регион по умолчанию берем из настроек.
        parsed_phone = phonenumbers.parse(value, settings.DEFAULT_PHONE_REGION)

        # Проверяем, является ли номер валидным.
        # is_possible_number() - быстрая проверка по длине.
        # is_valid_number() - полная, более медленная проверка по шаблонам.
        if not phonenumbers.is_valid_number(parsed_phone):
            raise ValidationError("Введен некорректный телефонный номер.")

    except phonenumbers.phonenumberutil.NumberParseException as exc:
        # Если библиотека не смогла распарсить номер, он невалиден.
        raise ValidationError(f"Не удалось распознать телефонный номер: {exc}")