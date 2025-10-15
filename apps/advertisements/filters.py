"""
Фильтры для приложения advertisements.
"""

from typing import Any

from django_filters import FilterSet, OrderingFilter

from .models import AdCampaign

# Определяем поля для сортировки в виде кортежа кортежей
# (значение_в_url, Человекочитаемая_метка)
# Базовые опции сортировки, доступные на всех страницах
BASE_ORDERING_CHOICES = (
    ("name", "Название (А-Я)"),
    ("-name", "Название (Я-А)"),
    ("budget", "Бюджет (по возрастанию)"),
    ("-budget", "Бюджет (по убыванию)"),
)

# Дополнительные опции, доступные только на странице статистики
STATS_ORDERING_CHOICES = (
    ("profit", "Рентабельность (по возрастанию)"),
    ("-profit", "Рентабельность (по убыванию)"),
)


class AdCampaignFilter(FilterSet):
    """
    Фильтр для рекламных кампаний.
    Включает динамическую логику для добавления опций сортировки
    в зависимости от того, на какой странице он используется.
    """

    # Создаем поле для сортировки с базовым набором опций
    sort = OrderingFilter(choices=BASE_ORDERING_CHOICES, empty_label="Сортировка по умолчанию", label="Сортировка")

    def __init__(self, *args: Any, **kwargs: Any):
        """
        Переопределяем конструктор, чтобы проверить, содержит ли queryset
        аннотацию 'profit', и если да - добавить опции сортировки по ней.
        """
        super().__init__(*args, **kwargs)

        # `self.queryset` - это тот queryset, который был передан из представления (View).
        # `self.queryset.query.annotations` - это словарь со всеми аннотациями.
        if "profit" in self.queryset.query.annotations:
            # Если аннотация 'profit' существует, мы расширяем список доступных опций для сортировки.
            self.filters["sort"].extra["choices"] += STATS_ORDERING_CHOICES

    class Meta:
        model = AdCampaign
        # Фильтры по каналу (выпадающий список) и услуге (выпадающий список)
        fields = ["channel", "service"]
