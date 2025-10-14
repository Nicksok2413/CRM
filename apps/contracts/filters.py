"""
Фильтры для приложения contracts.
"""

from django import forms
from django_filters import DateFilter, FilterSet

from .models import Contract


class ContractFilter(FilterSet):
    # Фильтр по дате "после указанной"
    start_date_after = DateFilter(
        field_name="start_date",
        lookup_expr="gte",
        label="Дата заключения после",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    # Фильтр по дате "до указанной"
    end_date_before = DateFilter(
        field_name="end_date",
        lookup_expr="lte",
        label="Дата окончания до",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Contract
        fields = ["service", "start_date_after", "end_date_before"]
