"""
Фильтры для приложения leads.
"""

from django_filters import FilterSet, OrderingFilter

from .models import PotentialClient

# Определяем поля для сортировки в виде кортежа кортежей
# (значение_в_url, Человекочитаемая_метка).
LEAD_ORDERING_CHOICES = (
    ("last_name", "Фамилия (А-Я)"),
    ("-last_name", "Фамилия (Я-А)"),
    ("status", "Статус (А-Я)"),
    ("-status", "Статус (Я-А)"),
    ("created_at", "Дата добавления (старые)"),
    ("-created_at", "Дата добавления (новые)"),
)


class LeadFilter(FilterSet):
    # Сортировка.
    sort = OrderingFilter(choices=LEAD_ORDERING_CHOICES, empty_label="Сортировка по умолчанию", label="Сортировка")

    class Meta:
        model = PotentialClient
        # Фильтр по рекламной кампании (выпадающий список) и по статусу (выпадающий список).
        fields = ["ad_campaign", "status"]
