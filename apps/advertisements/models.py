"""
Модели для приложения advertisements (рекламные кампании).
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.products.models import Service

# Этот блок импортируется только во время статической проверки типов.
# Он предотвращает ошибки циклического импорта во время выполнения.
if TYPE_CHECKING:
    from apps.leads.models import PotentialClient


class AdCampaign(BaseModel):
    """
    Модель для хранения информации о рекламных кампаниях.
    """

    name = models.CharField(max_length=200, verbose_name="Название")
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,  # Если услуга удаляется, кампании по ней теряют смысл
        related_name="ad_campaigns",
        verbose_name="Рекламируемая услуга",
    )
    channel = models.CharField(max_length=100, verbose_name="Канал продвижения")
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Бюджет",
        validators=[MinValueValidator(Decimal("0.00"))],  # Бюджет не может быть отрицательным
    )

    # Явная аннотация для обратной связи.
    # PyCharm и mypy теперь знают, что у `AdCampaign` есть
    # менеджер `leads`, который возвращает QuerySet объектов `PotentialClient`.
    leads: models.Manager["PotentialClient"]

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Рекламная кампания"
        verbose_name_plural = "Рекламные кампании"
        ordering = ["-created_at"]
