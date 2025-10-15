"""
Фильтры для приложения customers.
"""

from django_filters import FilterSet, OrderingFilter

from .models import ActiveClient

# Определяем поля для сортировки в виде кортежа кортежей
# (значение_в_url, Человекочитаемая_метка)
CUSTOMER_ORDERING_CHOICES = (
    ("potential_client__last_name", "Фамилия (А-Я)"),
    ("-potential_client__last_name", "Фамилия (Я-А)"),
    ("contract__end_date", "Дата окончания контракта"),
)


class ActiveClientFilter(FilterSet):
    # Сортировка
    sort = OrderingFilter(choices=CUSTOMER_ORDERING_CHOICES, empty_label="Сортировка по умолчанию", label="Сортировка")

    class Meta:
        model = ActiveClient
        # Фильтруем по связанной модели
        fields = {
            "contract__service": ["exact"],
        }
