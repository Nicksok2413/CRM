"""
Кастомные миксины для использования в представлениях (Views).
"""

from django.core.exceptions import PermissionDenied


class CheckLeadPermissionMixin:
    """
    Миксин для проверки объектных прав на связанного лида.

    Предполагается, что у `View` есть атрибут `self.object`,
    и у этого объекта есть поле `potential_client`.

    Проверяет, есть ли у текущего пользователя право `leads.view_potentialclient`
    на объект `self.object.potential_client`.
    """

    def dispatch(self, request, *args, **kwargs):
        # Сначала получаем объект, с которым работает View (ActiveClient).
        self.object = self.get_object()

        # Получаем связанного с ним лида.
        lead = getattr(self.object, "potential_client", None)

        # Проверяем, есть ли у пользователя права на этого лида.
        if not lead or not request.user.has_perm("leads.view_potentialclient", lead):
            # Если прав нет - вызываем ошибку 403.
            raise PermissionDenied

        # Если права есть, продолжаем выполнение стандартного dispatch.
        return super().dispatch(request, *args, **kwargs)
