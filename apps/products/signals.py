"""
Сигналы для приложения products.
"""

import logging
from typing import Any

from django.db.models import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Service

# Получаем логгер для приложения
logger = logging.getLogger("apps.products")


@receiver(pre_delete, sender=Service)
def prevent_hard_delete_service_with_campaigns(sender: type[Service], instance: Service, **kwargs: Any) -> None:
    """
    Сигнал срабатывает перед **реальным** удалением объекта Service из БД.

    Запрещает удаление услуги, если с ней связана хотя бы одна активная (не "мягко удаленная") рекламная кампания.
    Это защищает исторические данные и статистику от случайной потери.

    Args:
        sender: Класс модели, отправившей сигнал (Service).
        instance: Экземпляр модели, который собираются удалить (Service).
        **kwargs: Дополнительные аргументы.

    Raises:
        ProtectedError: Если найдены связанные активные объекты, прерывая удаление.
    """
    # `instance.ad_campaigns` - это обратная связь (related_name) от AdCampaign.
    # Ищем связанные кампании, у которых флаг `is_deleted` равен False.
    active_campaigns = instance.ad_campaigns.filter(is_deleted=False)

    # Если queryset не пустой, значит, связанные объекты существуют.
    if active_campaigns.exists():
        # Логируем заблокированное действие.
        logger.warning(
            f"Сигнал: Заблокирована попытка физического удаления услуги '{instance}' (PK={instance.pk}), "
            f"так как она защищена активными рекламными кампаниями: {[campaign.pk for campaign in active_campaigns]}."
        )

        # Выбрасываем исключение ProtectedError. Django Admin умеет красиво его
        # обрабатывать, показывая пользователю список защищенных объектов.
        raise ProtectedError(
            "Невозможно удалить эту услугу, так как с ней связаны следующие активные рекламные кампании:",
            set(active_campaigns),
        )
