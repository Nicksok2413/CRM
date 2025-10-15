"""
Общие, переиспользуемые классы фильтров для всего проекта.
"""

from typing import Any

from django_filters import FilterSet, OrderingFilter


class BaseOrderingFilter(FilterSet):
    """
    Базовый класс фильтра, который автоматически добавляет возможность сортировки.

    Для использования нужно унаследовать от этого класса и определить
    вложенный класс `Meta`, указав в нем `model` и `fields`,
    а также добавить атрибут `_ordering_fields` со списком полей для сортировки.
    """

    # Создаем поле для сортировки. `fields` - это словарь, где ключ - имя поля
    # в URL (например, `?sort=name`), а значение - человекочитаемая метка.
    # `empty_label` - текст по умолчанию.
    sort = OrderingFilter(
        fields=(),  # Поля будут добавлены динамически
        empty_label="Сортировка по умолчанию",
        label="Сортировка",
    )

    def __init__(self, *args: Any, **kwargs: Any):
        """
        Переопределяем конструктор для динамического добавления полей в OrderingFilter.
        """
        super().__init__(*args, **kwargs)

        # Получаем поля для сортировки из атрибута `_ordering_fields` дочернего класса
        ordering_fields = getattr(self.Meta, "_ordering_fields", {})

        # Устанавливаем эти поля для фильтра сортировки
        self.filters["sort"].extra["fields"] = ordering_fields
