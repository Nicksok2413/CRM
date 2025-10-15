"""
Фильтры для приложения products.
"""

from django_filters import CharFilter

from apps.common.filters import BaseOrderingFilter

from .models import Service


class ServiceFilter(BaseOrderingFilter):
    # Поиск по части названия или описания
    name_or_description = CharFilter(field_name="name", lookup_expr="icontains", label="Название или описание содержит")

    class Meta:
        model = Service
        # Фильтр по части названия или описания
        fields = ["name_or_description"]
        # Определяем поля для сортировки
        _ordering_fields = {
            "name": "Название (А-Я)",
            "-name": "Название (Я-А)",
            "cost": "Стоимость (по возрастанию)",
            "-cost": "Стоимость (по убыванию)",
        }
