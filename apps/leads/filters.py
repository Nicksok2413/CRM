"""
Фильтры для приложения leads.
"""

from apps.common.filters import BaseOrderingFilter

from .models import PotentialClient


class LeadFilter(BaseOrderingFilter):
    class Meta:
        model = PotentialClient
        # Фильтр по рекламной кампании (выпадающий список)
        fields = ["ad_campaign"]
        # Определяем поля для сортировки
        _ordering_fields = {
            "last_name": "Фамилия (А-Я)",
            "-last_name": "Фамилия (Я-А)",
            "created_at": "Дата добавления (старые)",
            "-created_at": "Дата добавления (новые)",
        }
