"""
Базовые, переиспользуемые классы представлений (Views) для всего проекта.

Эти классы инкапсулируют общую логику:
- Требование аутентификации (`LoginRequiredMixin`).
- Проверку глобальных или объектных прав доступа.
- Исправление несовместимости типов для `mypy` между Django и `django-guardian`.
- Наследование от базовых CBV (Class-Based Views) и `django-filter`.

Использование этих классов вместо прямого наследования от встроенных
`View` Django делает код приложений (`apps`) более чистым, сухим (DRY)
и легким для чтения и поддержки.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Model
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView
from guardian.mixins import PermissionRequiredMixin as ObjectPermissionRequiredMixin

# ==============================================================================
# БАЗОВЫЕ КЛАССЫ ДЛЯ ПРЕДСТАВЛЕНИЙ С ГЛОБАЛЬНЫМИ ПРАВАМИ
#
# Эти классы используют стандартный `PermissionRequiredMixin` от Django.
# Они подходят для `View`, где права доступа не зависят от конкретного
# объекта (например, право на просмотр общего списка).
# ==============================================================================


class BaseListView(LoginRequiredMixin, FilterView):
    """
    Базовый класс для всех списков с фильтрацией, пагинацией и сортировкой.

    - `LoginRequiredMixin`: Требует, чтобы пользователь был аутентифицирован.
    - `FilterView`: Интегрирует `django-filter` для фильтрации queryset.
    """

    # Явная аннотация для mypy, чтобы он знал о существовании этого атрибута
    # в дочерних классах, использующих пагинацию.
    paginate_by: int | None = None


class BaseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Базовый класс для представлений создания объектов с проверкой ГЛОБАЛЬНЫХ прав.
    """

    # Исправляем ошибку mypy о несовместимости `login_url`.
    login_url: str | None = None
    object: Model  # Явная аннотация для mypy


class BaseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Базовый класс для представлений обновления объектов с проверкой ГЛОБАЛЬНЫХ прав.
    """

    login_url: str | None = None
    object: Model


class BaseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Базовый класс для представлений удаления объектов с проверкой ГЛОБАЛЬНЫХ прав.
    """

    login_url: str | None = None
    object: Model


# ==============================================================================
# БАЗОВЫЕ КЛАССЫ ДЛЯ ПРЕДСТАВЛЕНИЙ С ОБЪЕКТНЫМИ ПРАВАМИ
#
# Эти классы используют `ObjectPermissionRequiredMixin` от `django-guardian`.
# Они подходят для `View`, где права доступа зависят от конкретного
# объекта (например, право на просмотр, изменение или удаление "своего" лида).
# ==============================================================================


class BaseObjectDetailView(LoginRequiredMixin, ObjectPermissionRequiredMixin, DetailView):
    """
    Базовый класс для детального просмотра с проверкой ОБЪЕКТНЫХ прав.
    """

    login_url: str | None = None
    object: Model


class BaseObjectUpdateView(LoginRequiredMixin, ObjectPermissionRequiredMixin, UpdateView):
    """
    Базовый класс для редактирования с проверкой ОБЪЕКТНЫХ прав.
    """

    login_url: str | None = None
    object: Model


class BaseObjectDeleteView(LoginRequiredMixin, ObjectPermissionRequiredMixin, DeleteView):
    """
    Базовый класс для удаления с проверкой ОБЪЕКТНЫХ прав.
    """

    login_url: str | None = None
    object: Model
