"""
Представления (Views) для приложения contracts.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet, ProtectedError
from django.forms.models import BaseModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from .filters import ContractFilter
from .forms import ContractForm
from .models import Contract


class ContractListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """Представление для отображения списка контрактов с фильтрацией, пагинацией и сортировкой."""

    model = Contract
    template_name = "contracts/contracts-list.html"
    context_object_name = "contracts"
    permission_required = "contracts.view_contract"

    # Подключаем класс фильтра
    filterset_class = ContractFilter
    # Устанавливаем пагинацию
    paginate_by = 25

    def get_queryset(self) -> QuerySet[Contract]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные услуги одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related("service")


class ContractDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра контракта."""

    model = Contract
    template_name = "contracts/contracts-detail.html"
    permission_required = "contracts.view_contract"

    def get_queryset(self) -> QuerySet[Contract]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанную услугу одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related("service")


class ContractCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Представление для создания нового контракта."""

    model = Contract
    object: Contract  # Явная аннотация для mypy
    form_class = ContractForm
    template_name = "contracts/contracts-create.html"
    permission_required = "contracts.add_contract"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse("contracts:detail", kwargs={"pk": self.object.pk})


class ContractUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Представление для редактирования контракта."""

    model = Contract
    object: Contract  # Явная аннотация для mypy
    form_class = ContractForm
    template_name = "contracts/contracts-edit.html"
    permission_required = "contracts.change_contract"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse("contracts:detail", kwargs={"pk": self.object.pk})


class ContractDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Представление для "мягкого" удаления контракта."""

    model = Contract
    template_name = "contracts/contracts-delete.html"
    success_url = reverse_lazy("contracts:list")
    permission_required = "contracts.delete_contract"

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.

        Проверяем на защищенные связанные объекты перед "мягким" удалением.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().

        Raises:
            ProtectedError: Если найдены связанные объекты, прерывая удаление.
        """
        try:
            # Проверяем не связан ли контракт с клиентом.
            if hasattr(self.object, 'active_client') and self.object.active_client is not None:
                raise ProtectedError(
                    "Невозможно удалить контракт: он привязан к истории клиента.",
                    {self.object.active_client}
                )

            # Если проверка пройдена, выполняем "мягкое" удаление.
            self.object.soft_delete()
            messages.success(self.request, f'Контракт "{self.object}" успешно перемещен в архив.')
            return HttpResponseRedirect(self.get_success_url())

        except ProtectedError:
            # Если поймали ошибку, показываем пользователю сообщение.
            messages.error(self.request, "Этот контракт нельзя удалить, так как он привязан к истории клиента.")
            # Возвращаем пользователя на детальную страницу.
            return HttpResponseRedirect(reverse('contracts:detail', kwargs={'pk': self.object.pk}))
