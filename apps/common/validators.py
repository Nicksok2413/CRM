"""
Кастомные валидаторы для всего проекта.
"""

import phonenumbers

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class FileSizeValidator:
    """
    Кастомный класс-валидатор для проверки максимального размера файла.

    Args:
        max_size_mb (int): Максимальный размер файла в мегабайтах.
        message (str, optional): Кастомное сообщение об ошибке.
    """
    def __init__(self, max_size_mb: int, message: str = None):
        self.max_size_mb = max_size_mb
        self.message = message or f"Максимальный размер файла не должен превышать {self.max_size_mb} МБ."

    def __call__(self, file):
        """
        Вызывается Django для выполнения валидации.
        """
        if file.size > self.max_size_mb * 1024 * 1024:
            raise ValidationError(self.message)

    def __eq__(self, other):
        """
        Необходимо для сравнения объектов валидатора при создании миграций.
        """
        return (
            isinstance(other, self.__class__) and
            self.max_size_mb == other.max_size_mb and
            self.message == other.message
        )

# Создаем конкретные экземпляры валидаторов
validate_image_size = FileSizeValidator(max_size_mb=settings.MAX_IMAGE_SIZE_MB)
validate_document_size = FileSizeValidator(max_size_mb=settings.MAX_DOCUMENT_SIZE_MB)

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