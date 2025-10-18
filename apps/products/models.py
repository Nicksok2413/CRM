"""
Модели для приложения products (услуги).
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel

# Этот блок импортируется только во время статической проверки типов.
# Он предотвращает ошибки циклического импорта во время выполнения.
if TYPE_CHECKING:
    from apps.advertisements.models import AdCampaign


class Service(BaseModel):
    """
    Модель для хранения информации об услугах компании.
    """

    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Стоимость",
        validators=[MinValueValidator(Decimal("0.00"))],  # Стоимость не может быть отрицательной
    )

    # Явная аннотация для обратной связи.
    # PyCharm и mypy теперь знают, что у `Service` есть
    # менеджер `ad_campaigns`, который возвращает QuerySet объектов `AdCampaign`.
    ad_campaigns: models.Manager["AdCampaign"]

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ["name"]

        # Добавляем кастомное ограничение.
        constraints = [
            # Уникальность для названия.
            # Поле `name` должно быть уникальным только для тех записей,
            # у которых is_deleted=False (т.е. тех, которые не были 'мягко удалены').
            models.UniqueConstraint(
                fields=["name"], condition=models.Q(is_deleted=False), name="unique_service_name_if_not_deleted"
            )
        ]
