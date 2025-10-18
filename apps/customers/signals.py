"""
Сигналы для приложения customers.
"""

import logging
from typing import Any

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.leads.models import PotentialClient

from .models import ActiveClient

# Получаем логгер для приложения
logger = logging.getLogger("apps.customers")


@receiver(pre_save, sender=ActiveClient)
def update_lead_status_on_deactivation(sender: type[ActiveClient], instance: ActiveClient, **kwargs: Any):
    """
    Сигнал для обновления статуса лида перед "мягком удалении" (деактивации) записи ActiveClient.

    Если менеджер деактивирует клиента, его лид автоматически вернется со статусом "В работе".

    Args:
        sender: Класс модели, отправившей сигнал (ActiveClient).
        instance: Экземпляр модели ActiveClient, который собираются "мягко" удалить.
        **kwargs: Дополнительные аргументы.
    """

    # Если у объекта еще нет PK, значит, он только создается. Выходим.
    if instance.pk is None:
        return

    try:
        # Получаем "старую" версию объекта из базы данных.
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return  # На всякий случай, если объект уже удален.

    # Сравниваем старое и новое значения поля is_deleted.
    # Нас интересует момент, когда оно меняется с False на True.
    if not old_instance.is_deleted and instance.is_deleted:
        # Получаем связанного лида
        lead = instance.potential_client

        # Логируем, что сигнал сработал.
        logger.debug(
            f"Сигнал: Запущен `update_lead_status_on_deactivation` для ActiveClient PK={instance.pk}, "
            f"связанного с лидом '{lead}' (PK={lead.pk})."
        )

        # Если лид был "Конвертирован", возвращаем его в статус "В работе".
        if lead.status == PotentialClient.Status.CONVERTED:
            lead.status = PotentialClient.Status.IN_PROGRESS
            lead.save(update_fields=["status"])

            # Логируем успешное изменение статуса.
            logger.info(
                f"Сигнал: Статус лида '{lead}' (PK={lead.pk}) автоматически изменен на 'В работе' "
                f"из-за деактивации записи ActiveClient (PK={instance.pk})."
            )
