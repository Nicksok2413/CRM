"""
Сигналы для приложения leads.
"""

from typing import Any

from django.db.models import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.customers.models import ActiveClient

from .models import PotentialClient


@receiver(pre_delete, sender=PotentialClient)
def prevent_hard_delete_lead_with_history(
    sender: type[PotentialClient], instance: PotentialClient, **kwargs: Any
) -> None:
    """
    Сигнал срабатывает перед **реальным** удалением объекта PotentialClient из БД.

    Запрещает удаление лида, если у него есть история контрактов.
    Это защищает финансовую историю и историю взаимоотношений с клиентом.

    Args:
        sender: Класс модели, отправившей сигнал (PotentialClient).
        instance: Экземпляр модели, который собираются удалить (PotentialClient).
        **kwargs: Дополнительные аргументы.

    Raises:
        ProtectedError: Если найдены связанные объекты, прерывая удаление.
    """
    # Проверяем через `all_objects`, так как даже архивные контракты важны.
    history = ActiveClient.all_objects.filter(potential_client=instance)

    if history.exists():
        raise ProtectedError("Невозможно удалить лида: у него есть история контрактов.", set(history))
