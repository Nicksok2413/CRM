"""
Сигналы для приложения customers.
"""

from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.leads.models import PotentialClient

from .models import ActiveClient


@receiver(post_save, sender=ActiveClient)
def update_lead_status_on_deactivation(sender: type[ActiveClient], instance: ActiveClient, **kwargs: Any):
    """
    Сигнал для обновления статуса лида при "мягком удалении" (деактивации) записи ActiveClient.

    Если менеджер деактивирует клиента, его лид автоматически вернется со статусом "В работе".

    Args:
        sender: Класс модели, отправившей сигнал (ActiveClient).
        instance: Экземпляр модели ActiveClient, который собираются "мягко" удалить.
        **kwargs: Дополнительные аргументы.
    """

    # `update_fields` содержит список полей, которые были изменены.
    update_fields = kwargs.get("update_fields") or set()

    # Нас интересует ситуация, когда "мягко" удаляется запись (флаг is_deleted станет True).
    if instance.is_deleted and "is_deleted" in update_fields:
        # Получаем связанного лида
        lead = instance.potential_client

        # Если лид был "Конвертирован", возвращаем его в статус "В работе".
        if lead.status == PotentialClient.Status.CONVERTED:
            lead.status = PotentialClient.Status.IN_PROGRESS
            lead.save(update_fields=["status"])
