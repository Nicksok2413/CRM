"""
Модели для приложения leads (потенциальные клиенты).
"""

from typing import TYPE_CHECKING

import phonenumbers
from django.conf import settings
from django.db import models

from apps.advertisements.models import AdCampaign
from apps.common.models import BaseModel
from apps.common.validators import validate_international_phone_number, validate_letters_and_hyphens

# Этот блок импортируется только во время статической проверки типов.
# Он предотвращает ошибки циклического импорта во время выполнения.
if TYPE_CHECKING:
    from apps.customers.models import ActiveClient


class PotentialClient(BaseModel):
    """
    Модель для хранения данных о потенциальных клиентах (лидах).
    """

    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя",
        validators=[validate_letters_and_hyphens],  # Валидатор для имени
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия",
        validators=[validate_letters_and_hyphens],  # Валидатор для фамилии
    )
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,  # Разрешаем хранить в БД NULL вместо пустой строки
        unique=True,  # Безопасно добавляем уникальность
        verbose_name="Телефон",
        validators=[validate_international_phone_number],  # Валидатор для телефона
        help_text="Введите номер в любом удобном формате, включая международный.",
    )

    ad_campaign = models.ForeignKey(
        AdCampaign,
        on_delete=models.SET_NULL,  # Если кампания удалена, мы не хотим терять лида
        null=True,
        blank=True,
        related_name="leads",
        verbose_name="Рекламная кампания",
    )

    # Явная аннотация для обратной связи.
    # PyCharm и mypy теперь знают, что у `PotentialClient` есть
    # менеджер `contracts_history`, который возвращает QuerySet объектов `ActiveClient`.
    contracts_history: models.Manager["ActiveClient"]

    def get_current_status(self):
        """
        Возвращает текущую запись об активности клиента.
        Ищет в истории контрактов запись, которая не помечена как удаленная.
        """
        return self.contracts_history.filter(is_deleted=False).first()

    def save(self, *args, **kwargs):
        """
        Переопределяем метод save для нормализации телефонного номера
        к международному стандарту E.164 (+375291234567).
        """
        if self.phone:
            try:
                # Парсим номер, используя регион по умолчанию из настроек
                parsed_phone = phonenumbers.parse(self.phone, settings.DEFAULT_PHONE_REGION)

                # Форматируем номер в стандарт E.164
                self.phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
            except phonenumbers.phonenumberutil.NumberParseException:
                # Этот блок, по идее, никогда не должен сработать,
                # так как валидатор уже проверил номер.
                # Но мы оставляем его для дополнительной надежности.
                pass  # Оставляем номер как есть, если что-то пошло не так

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name: str = "Потенциальный клиент"
        verbose_name_plural: str = "Потенциальные клиенты"
        ordering = ["-created_at"]
