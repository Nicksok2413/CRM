"""
Фильтры для приложения products.
"""

from django_filters import CharFilter, FilterSet

from .models import Service


class ServiceFilter(FilterSet):
    # Поиск по части названия или описания
    name_or_description = CharFilter(field_name="name", lookup_expr="icontains", label="Название или описание содержит")

    class Meta:
        model = Service
        fields = ["name_or_description"]
