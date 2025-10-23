"""
Сигналы для приложения advertisements.
"""

import logging
from typing import Any

from django.db.models import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.leads.models import PotentialClient

from .models import AdCampaign

# Получаем логгер для приложения.
logger = logging.getLogger("apps.products")


@receiver(pre_delete, sender=AdCampaign)
def prevent_hard_delete_adcampaign_with_leads(sender: type[AdCampaign], instance: AdCampaign, **kwargs: Any) -> None:
    """
    Сигнал срабатывает перед **реальным** удалением объекта AdCampaign из БД.

    Запрещает удаление рекламной кампании, если от нее были получены лиды.
    Это защищает исторические данные и статистику от случайной потери.

    Args:
        sender: Класс модели, отправившей сигнал (AdCampaign).
        instance: Экземпляр модели, который собираются удалить (AdCampaign).
        **kwargs: Дополнительные аргументы.

    Raises:
        ProtectedError: Если найдены связанные объекты, прерывая удаление.
    """
    # Даже если лид был "мягко удален", он все равно является частью истории
    # и статистики, поэтому мы проверяем через `all_objects`.
    protected_leads = PotentialClient.all_objects.filter(ad_campaign=instance)

    if protected_leads.exists():
        # Логируем заблокированное действие.
        logger.warning(
            f"Сигнал: Заблокирована попытка физического удаления рекламной кампании '{instance}' (PK={instance.pk}), "
            f"так как она защищена связанными лидами: {[lead.pk for lead in protected_leads]}."
        )

        # Выбрасываем исключение ProtectedError. Django Admin умеет красиво его
        # обрабатывать, показывая пользователю список защищенных объектов.
        raise ProtectedError("Невозможно удалить рекламную кампанию: от нее были получены лиды.", set(protected_leads))
