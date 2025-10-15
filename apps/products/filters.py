"""
Фильтры для приложения products.
"""

from django_filters import CharFilter, FilterSet, OrderingFilter

from .models import Service

# Определяем поля для сортировки в виде кортежа кортежей
# (значение_в_url, Человекочитаемая_метка)
PRODUCT_ORDERING_CHOICES = (
    ("name", "Название (А-Я)"),
    ("-name", "Название (Я-А)"),
    ("cost", "Стоимость (по возрастанию)"),
    ("-cost", "Стоимость (по убыванию)"),
)


class ServiceFilter(FilterSet):
    # Сортировка
    sort = OrderingFilter(choices=PRODUCT_ORDERING_CHOICES, empty_label="Сортировка по умолчанию", label="Сортировка")

    # Поиск по части названия или описания
    name_or_description = CharFilter(field_name="name", lookup_expr="icontains", label="Название или описание содержит")

    class Meta:
        model = Service
        # Фильтр по части названия или описания
        fields = ["name_or_description"]
