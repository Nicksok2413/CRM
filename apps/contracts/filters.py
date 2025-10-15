"""
Фильтры для приложения contracts.
"""

from django.forms import DateInput
from django_filters import DateFilter

from apps.common.filters import BaseOrderingFilter

from .models import Contract


class ContractFilter(BaseOrderingFilter):
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
        # Определяем поля для сортировки
        _ordering_fields = {
            "start_date": "Дата заключения (старые)",
            "-start_date": "Дата заключения (новые)",
            "end_date": "Дата окончания (ближайшие)",
            "-end_date": "Дата окончания (дальние)",
            "amount": "Сумма (по возрастанию)",
            "-amount": "Сумма (по убыванию)",
        }
