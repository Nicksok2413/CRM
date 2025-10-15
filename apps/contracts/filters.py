"""
Фильтры для приложения contracts.
"""

from django.forms import DateInput
from django_filters import DateFilter, FilterSet, OrderingFilter

from .models import Contract

# Определяем поля для сортировки в виде кортежа кортежей
# (значение_в_url, Человекочитаемая_метка)
CONTRACT_ORDERING_CHOICES = (
    ("start_date", "Дата заключения (старые)"),
    ("-start_date", "Дата заключения (новые)"),
    ("end_date", "Дата окончания (ближайшие)"),
    ("-end_date", "Дата окончания (дальние)"),
    ("amount", "Сумма (по возрастанию)"),
    ("-amount", "Сумма (по убыванию)"),
)


class ContractFilter(FilterSet):
    # Сортировка
    sort = OrderingFilter(choices=CONTRACT_ORDERING_CHOICES, empty_label="Сортировка по умолчанию", label="Сортировка")

    # Фильтр по дате "после указанной"
    start_date_after = DateFilter(
        field_name="start_date",
        lookup_expr="gte",
        label="Дата заключения после",
        widget=DateInput(attrs={"type": "date"}),
    )
    # Фильтр по дате "до указанной"
    end_date_before = DateFilter(
        field_name="end_date",
        lookup_expr="lte",
        label="Дата окончания до",
        widget=DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Contract
        # Фильтры по услуге (выпадающий список) и датам
        fields = ["service", "start_date_after", "end_date_before"]
