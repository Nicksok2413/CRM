"""
Кастомные миксины для использования в представлениях (Views).
"""

from typing import Any, Callable

from django.core.exceptions import PermissionDenied
from django.db.models import Model
from django.http import HttpRequest, HttpResponseBase
from django.views.generic.base import View


class CheckLeadPermissionMixin(View):
    """
    Миксин для проверки объектных прав на связанного лида.

    Этот миксин должен использоваться вместе с классами, которые наследуются
    от `SingleObjectMixin` (например, DetailView, UpdateView, DeleteView),
    так как он ожидает наличия метода `self.get_object()`.

    Проверяет, есть ли у текущего пользователя право `leads.view_potentialclient`
    на объект `self.object.potential_client`.
    """

    # Аннотируем `self.object` на уровне класса, чтобы mypy знал о его существовании.
    # `Any` - это компромисс, так как миксин может использоваться с разными моделями.
    object: Any

    # `get_object` - это метод из `SingleObjectMixin`, который наследуют DetailView, UpdateView и DeleteView.
    # Мы должны его вызвать, чтобы получить объект, с которым работаем (ActiveClient).
    # Явная аннотация `self.get_object` подсказывает mypy, что этот метод существует.
    get_object: Callable[..., Any]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """
        Перехватываем запрос до его дальнейшей обработки.
        """
        # Получаем объект (ActiveClient).
        self.object = self.get_object()

        # Получаем связанного лида.
        lead = getattr(self.object, "potential_client", None)

        # Проверяем, есть ли у пользователя права на этого лида.

        # `has_perm` - метод `guardian`, он может отсутствовать на стандартном пользователе,
        # поэтому используем `getattr` для безопасности.
        def default_perm_checker(perm: str, obj: Model) -> bool:
            """
            Вложенная функция-заглушка на случай, если у пользователя нет метода `has_perm`.
            Всегда возвращает False.
            """
            return False

        user_has_permission = getattr(request.user, "has_perm", default_perm_checker)

        if not lead or not user_has_permission("leads.view_potentialclient", lead):
            # Если прав нет - вызываем ошибку 403.
            raise PermissionDenied

        # Если права есть, продолжаем выполнение стандартного dispatch из родительского View.
        return super().dispatch(request, *args, **kwargs)
