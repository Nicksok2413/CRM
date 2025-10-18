"""
Сигналы для приложения leads.
"""

import logging
from typing import Any

from django.db.models import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.customers.models import ActiveClient

from .models import PotentialClient

# Получаем логгер для приложения
logger = logging.getLogger("apps.leads")


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
        # Логируем заблокированное действие.
        logger.warning(
            f"Сигнал: Заблокирована попытка физического удаления лида '{instance}' (PK={instance.pk}), "
            f"так как у него есть история контрактов: {[h.pk for h in history]}."
        )

        # Выбрасываем исключение ProtectedError. Django Admin умеет красиво его
        # обрабатывать, показывая пользователю список защищенных объектов.
        raise ProtectedError("Невозможно удалить лида: у него есть история контрактов.", set(history))
