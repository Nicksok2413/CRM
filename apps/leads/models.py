"""
Модели для приложения leads (потенциальные клиенты).
"""

from django.db import models

from apps.advertisements.models import AdCampaign
from apps.common.models import BaseModel


class PotentialClient(BaseModel):
    """
    Модель для хранения данных о потенциальных клиентах (лидах).
    """
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")

    ad_campaign = models.ForeignKey(
        AdCampaign,
        on_delete=models.SET_NULL,  # Если кампания удалена, мы не хотим терять лида
        null=True,
        blank=True,
        related_name='leads',
        verbose_name="Рекламная кампания"
    )

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name: str = "Потенциальный клиент"
        verbose_name_plural: str = "Потенциальные клиенты"
        ordering = ['-created_at']
