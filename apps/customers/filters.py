"""
Фильтры для приложения customers.
"""

from apps.common.filters import BaseOrderingFilter

from .models import ActiveClient


class ActiveClientFilter(BaseOrderingFilter):
    class Meta:
        model = ActiveClient
        # Фильтруем по связанной модели
        fields = {
            "contract__service": ["exact"],
        }
        # Определяем поля для сортировки
        _ordering_fields = {
            "potential_client__last_name": "Фамилия (А-Я)",
            "-potential_client__last_name": "Фамилия (Я-А)",
            "contract__end_date": "Дата окончания контракта",
        }
