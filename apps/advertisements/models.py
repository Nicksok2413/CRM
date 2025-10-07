"""
Модели для приложения advertisements (рекламные кампании).
"""

from django.db import models

from apps.common.models import BaseModel
from apps.products.models import Service


class AdCampaign(BaseModel):
    """
    Модель для хранения информации о рекламных кампаниях.
    """
    name = models.CharField(max_length=200, verbose_name="Название")
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,  # Если услуга удаляется, кампании по ней теряют смысл
        related_name='ad_campaigns',
        verbose_name="Рекламируемая услуга"
    )
    channel = models.CharField(max_length=100, verbose_name="Канал продвижения")
    budget = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Бюджет")

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name: str = "Рекламная кампания"
        verbose_name_plural: str = "Рекламные кампании"
        ordering = ['-created_at']
