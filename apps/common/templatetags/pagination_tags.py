"""
Кастомные шаблонные теги для рендеринга продвинутой пагинации.

Эти теги позволяют создавать удобную навигацию по страницам, которая
сохраняет все текущие GET-параметры (фильтрацию, сортировку) и отображает
"скользящее окно" страниц вокруг текущей.
"""

from typing import Any

from django import template

# Создаем экземпляр Library, чтобы зарегистрировать наши теги.
register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs: Any):
    """
    Кастомный тег для модификации GET-параметров текущего URL.

    Сохраняет все существующие GET-параметры (например, от фильтрации или
    сортировки) и добавляет/изменяет/удаляет те, что переданы в тег.
    Это критически важно для корректной работы пагинации вместе с фильтрами.

    Использование в шаблоне:
    {% query_transform page=1 sort="-name" as new_url %}
    <a href="?{{ new_url }}">...</a>

    Args:
        context: Контекст шаблона, автоматически передается благодаря `takes_context=True`.
                 Из него мы извлекаем объект `request`.
        **kwargs: Словарь с GET-параметрами, которые нужно изменить.
                  - Если значение не None, параметр будет добавлен/обновлен.
                  - Если значение None, параметр будет удален из URL.

    Returns:
        Строка с закодированными GET-параметрами для использования в URL.
    """

    # Получаем request из контекста.
    request = context["request"]

    # Копируем текущие GET-параметры, чтобы не изменять исходный объект.
    updated_params = request.GET.copy()

    # Итерируемся по аргументам, переданным в тег.
    for key, value in kwargs.items():
        if value is not None:
            # Если значение предоставлено, добавляем/обновляем параметр.
            updated_params[key] = value
        else:
            # Если значение None, удаляем параметр (если он существует).
            updated_params.pop(key, 0)

    # Возвращаем закодированную строку параметров (например, 'page=2&sort=name').
    return updated_params.urlencode()


@register.inclusion_tag("common/pagination.html", takes_context=True)
def render_pagination(context, page_obj, page_range_window=2):
    """
    Рендерит HTML-блок с продвинутой пагинацией.

    Использует "скользящее окно" для отображения номеров страниц, а также
    ссылки на первую, последнюю, предыдущую и следующую страницы.
    Делегирует рендеринг HTML-кода шаблону 'common/pagination.html'.

    Использование в шаблоне:
    {% render_pagination page_obj %}
    Или с кастомным размером "окна":
    {% render_pagination page_obj page_range_window=3 %}

    Args:
        context: Контекст шаблона для доступа к `request`.
        page_obj: Объект Page из Django Paginator, который передается
                  из представления (View).
        page_range_window (int): Количество страниц, отображаемых слева и
                                 справа от текущей страницы. По умолчанию 2.

    Returns:
        Словарь с контекстом, который будет использован для рендеринга
        шаблона 'common/pagination.html'.
    """

    # Получаем request из контекста.
    request = context["request"]

    # Вычисляем "окно" страниц для отображения.
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages

    # Определяем начальную и конечную страницы "окна".
    start_page = max(1, current_page - page_range_window)
    end_page = min(total_pages, current_page + page_range_window)

    # Создаем диапазон страниц для итерации в шаблоне.
    # +1, так как range() не включает верхнюю границу.
    page_range = range(start_page, end_page + 1)

    # Возвращаем контекст, который будет доступен в `common/pagination.html`.
    return {
        "request": request,
        "page_obj": page_obj,
        "page_range": page_range,
    }
