"""
Фильтры для приложения advertisements.
"""

from apps.common.filters import BaseOrderingFilter

from .models import AdCampaign


class AdCampaignFilter(BaseOrderingFilter):
    class Meta:
        model = AdCampaign
        # Фильтры по каналу (выпадающий список) и услуге (выпадающий список)
        fields = ["channel", "service"]
        # Определяем поля для сортировки
        _ordering_fields = {
            "name": "Название (А-Я)",
            "-name": "Название (Я-А)",
            "budget": "Бюджет (по возрастанию)",
            "-budget": "Бюджет (по убыванию)",
        }
