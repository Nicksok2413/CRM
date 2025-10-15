"""
Фильтры для приложения advertisements.
"""

from django_filters import FilterSet, OrderingFilter

from .models import AdCampaign

# Определяем поля для сортировки в виде кортежа кортежей
# (значение_в_url, Человекочитаемая_метка)
AD_CAMPAIGN_ORDERING_CHOICES = (
    ("name", "Название (А-Я)"),
    ("-name", "Название (Я-А)"),
    ("budget", "Бюджет (по возрастанию)"),
    ("-budget", "Бюджет (по убыванию)"),
)


class AdCampaignFilter(FilterSet):
    # Сортировка
    sort = OrderingFilter(
        choices=AD_CAMPAIGN_ORDERING_CHOICES, empty_label="Сортировка по умолчанию", label="Сортировка"
    )

    class Meta:
        model = AdCampaign
        # Фильтры по каналу (выпадающий список) и услуге (выпадающий список)
        fields = ["channel", "service"]
