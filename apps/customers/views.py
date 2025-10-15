"""
Представления (Views) для приложения customers.
"""

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponseBase, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from apps.leads.models import PotentialClient

from .filters import ActiveClientFilter
from .forms import ActiveClientCreateForm, ActiveClientUpdateForm
from .models import ActiveClient


class ActiveClientListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """Представление для отображения списка всех активных клиентов с фильтрацией, пагинацией и сортировкой."""

    model = ActiveClient
    template_name = "customers/customers-list.html"
    context_object_name = "customers"
    permission_required = "customers.view_activeclient"

    # Подключаем класс фильтра
    filterset_class = ActiveClientFilter
    # Устанавливаем пагинацию
    paginate_by = 25

    def get_queryset(self) -> QuerySet[ActiveClient]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные лиды одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related("potential_client")


class ActiveClientDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра активного клиента."""

    model = ActiveClient
    template_name = "customers/customers-detail.html"
    permission_required = "customers.view_activeclient"

    def get_queryset(self) -> QuerySet[ActiveClient]:
        """
        Переопределяем queryset для оптимизации на детальной странице.
        select_related подгружает данные из двух связанных моделей
        (лида и контракта) одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related("potential_client", "contract")


class ActiveClientUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Представление для редактирования записи об активном клиенте.
    Позволяет привязать клиента к другому контракту.
    """

    model = ActiveClient
    object: ActiveClient  # Явная аннотация для mypy
    form_class = ActiveClientUpdateForm  # Используем специальную форму для редактирования
    template_name = "customers/customers-edit.html"
    permission_required = "customers.change_activeclient"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        messages.success(self.request, "Данные активного клиента успешно обновлены.")
        return reverse("customers:detail", kwargs={"pk": self.object.pk})


class ActiveClientDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Представление для "мягкого" удаления записи об активном клиенте.
    Деактивирует клиента, но не удаляет его данные из системы.
    """

    model = ActiveClient
    template_name = "customers/customers-delete.html"
    success_url = reverse_lazy("customers:list")
    permission_required = "customers.delete_activeclient"

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().
        """
        self.object.soft_delete()
        messages.success(self.request, f'Активный клиент "{self.object}" был успешно удален.')
        return HttpResponseRedirect(self.get_success_url())


class ActiveClientCreateFromLeadView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Специализированное представление для ключевого бизнес-процесса:
    "активации" Потенциального клиента.
    """

    model = ActiveClient
    form_class = ActiveClientCreateForm  # Используем специальную форму для создания
    template_name = "customers/customers-create.html"
    permission_required = "customers.add_activeclient"

    # Явно аннотируем self.lead для mypy, так как он создается в dispatch
    lead: PotentialClient

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Переопределяем метод `dispatch` для выполнения проверок до того, как будет показана форма."""
        # Извлекаем PK лида из URL (например, /customers/new/from-lead/15/)
        lead_pk = self.kwargs.get("lead_pk")
        # Получаем объект лида или возвращаем ошибку 404, если лид не найден
        self.lead = get_object_or_404(PotentialClient, pk=lead_pk)

        # Проверяем, не является ли лид уже активным клиентом.
        # Если да - перенаправляем обратно с сообщением об ошибке.
        if self.lead.get_current_status():
            messages.error(request, f'Клиент "{self.lead}" уже является активным.')
            return HttpResponseRedirect(reverse("leads:list"))  # Возвращаемся в список лидов

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> dict[str, Any]:
        """
        Передаем начальные данные в форму.
        Это скрытое поле с ID лида, которого мы активируем.
        """
        initial = super().get_initial()
        initial["potential_client"] = self.lead
        return initial

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Добавляем в контекст шаблона объект лида для отображения информации о нем.
        """
        context = super().get_context_data(**kwargs)
        context["lead"] = self.lead
        return context

    def get_success_url(self) -> str:
        """
        Перенаправляем на список активных клиентов после активации.
        """
        messages.success(self.request, f'Клиент "{self.lead}" успешно активирован.')
        return reverse("customers:list")
