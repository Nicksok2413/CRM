"""
Сигналы для приложения contracts.
"""

import logging
from typing import Any

from django.db.models import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Contract

# Получаем логгер для приложения
logger = logging.getLogger("apps.contracts")


@receiver(pre_delete, sender=Contract)
def prevent_hard_delete_contract_in_use(sender: type[Contract], instance: Contract, **kwargs: Any) -> None:
    """
    Сигнал срабатывает перед **реальным** удалением объекта Contract из БД.

    Запрещает удаление контракта, если он привязан к истории клиента.

    Args:
        sender: Класс модели, отправившей сигнал (Contract).
        instance: Экземпляр модели, который собираются удалить (Contract).
        **kwargs: Дополнительные аргументы.

    Raises:
        ProtectedError: Если найдены связанные объекты, прерывая удаление.
    """
    # Связь `contract` -> `active_client` является `OneToOne`, поэтому проверяем ее наличие напрямую.
    # `hasattr` - безопасный способ проверить наличие обратной связи,
    # которая может отсутствовать, если объект еще не был сохранен полностью.
    # Дополнительно проверяем, что связанный объект не "мягко удален".
    if (
        hasattr(instance, "active_client")
        and instance.active_client is not None
        and not instance.active_client.is_deleted
    ):
        # Логируем заблокированное действие.
        logger.warning(
            f"Сигнал: Заблокирована попытка физического удаления контракта '{instance}' (PK={instance.pk}), "
            f"так как он привязан к активному клиенту (ActiveClient PK={instance.active_client.pk})."
        )

        # Выбрасываем исключение ProtectedError. Django Admin умеет красиво его
        # обрабатывать, показывая пользователю список защищенных объектов.
        raise ProtectedError("Невозможно удалить контракт: он привязан к истории клиента.", {instance.active_client})
