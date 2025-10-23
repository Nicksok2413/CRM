"""
Сигналы для приложения leads.
"""

import logging
from typing import Any

from django.db.models import ProtectedError
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from guardian.shortcuts import assign_perm

from apps.customers.models import ActiveClient

from .models import PotentialClient
from .tasks import notify_manager_about_new_lead

# Получаем логгер для приложения
logger = logging.getLogger("apps.leads")


@receiver(post_save, sender=PotentialClient)
def assign_lead_permissions_on_save(
    sender: type[PotentialClient], instance: PotentialClient, created: bool, **kwargs: Any
) -> None:
    """
    Сигнал для автоматического назначения объектных прав на лида.

    Срабатывает каждый раз после сохранения объекта PotentialClient.
    - Если у лида назначен менеджер, сигнал выдает ему права на просмотр,
      изменение и удаление этого **конкретного** лида.

    Args:
    sender: Класс модели, отправившей сигнал (PotentialClient).
    instance: Экземпляр сохраняемого лида (PotentialClient).
    created: Флаг, указывающий, была ли запись создана.
    **kwargs: Дополнительные аргументы.
    """

    # Если у лида есть ответственный менеджер.
    if instance.manager:
        # Список прав, которые нужно выдать.
        permissions = [
            "leads.view_potentialclient",
            "leads.change_potentialclient",
            "leads.delete_potentialclient",
        ]

        # Назначаем права.
        # `assign_perm` - основная функция django-guardian.
        # Она говорит: "Дай пользователю `instance.manager` права из списка `permissions` на объект `instance`".
        for permission in permissions:
            assign_perm(permission, instance.manager, instance)

        logger.info(
            f"Сигнал: Менеджеру (username={instance.manager.username}) "
            f"назначены права на управление лидом '{instance}' (PK={instance.pk}), "
        )

        # Если лид только что создан и ему назначен менеджер.
        if created and instance.manager:
            logger.info(
                f"Сигнал: Запуск задачи на уведомление менеджера '{instance.manager}' о новом лиде '{instance}'."
            )
            # Вызываем задачу асинхронно.
            # .delay() - стандартный способ запуска.
            notify_manager_about_new_lead.delay(lead_id=instance.pk, manager_id=instance.manager.pk)


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
    contracts_history = ActiveClient.all_objects.filter(potential_client=instance)

    if contracts_history.exists():
        # Логируем заблокированное действие.
        logger.warning(
            f"Сигнал: Заблокирована попытка физического удаления лида '{instance}' (PK={instance.pk}), "
            f"так как у него есть история контрактов: {[contract.pk for contract in contracts_history]}."
        )

        # Выбрасываем исключение ProtectedError. Django Admin умеет красиво его
        # обрабатывать, показывая пользователю список защищенных объектов.
        raise ProtectedError("Невозможно удалить лида: у него есть история контрактов.", set(contracts_history))
