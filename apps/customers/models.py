"""
Модели для приложения customers (активные клиенты).
"""

from django.db import models

from apps.common.models import BaseModel
from apps.contracts.models import Contract
from apps.leads.models import PotentialClient


class ActiveClient(BaseModel):
    """
    Модель активного клиента.
    Связывает Потенциального клиента с Контрактом.
    Один клиент может иметь несколько таких записей (текущий и архивные контракты).
    """
    potential_client = models.ForeignKey(
        PotentialClient,
        on_delete=models.CASCADE,  # Если лид удален (даже мягко), запись об активности теряет смысл
        related_name='contracts_history',  # Уникальное имя для обратной связи
        verbose_name="Потенциальный клиент"
    )
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,  # Если контракт удален, клиент перестает быть активным по этому контракту
        related_name='active_client',
        verbose_name="Контракт"
    )

    def __str__(self) -> str:
        return str(self.potential_client)

    class Meta:
        verbose_name: str = "Активный клиент"
        verbose_name_plural: str = "Активные клиенты"
