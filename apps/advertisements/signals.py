"""
Сигналы для приложения advertisements.
"""

from typing import Any

from django.db.models import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import AdCampaign


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
    if instance.leads.all_objects.exists():
        raise ProtectedError(
            "Невозможно удалить рекламную кампанию: от нее были получены лиды.",
            instance.leads.all_objects.all()
        )