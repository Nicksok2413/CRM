"""
Модели для приложения products (услуги).
"""

from django.db import models

from apps.common.models import BaseModel


class Service(BaseModel):
    """
    Модель для хранения информации об услугах компании.
    """
    name = models.CharField(max_length=200, unique=True, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость")

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name: str = "Услуга"
        verbose_name_plural: str = "Услуги"
        ordering = ['name']
