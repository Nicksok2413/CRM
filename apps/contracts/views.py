"""
Представления (Views) для приложения contracts.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ContractForm
from .models import Contract


class ContractListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Представление для отображения списка контрактов."""
    model = Contract
    template_name = 'contracts/contracts-list.html'
    context_object_name = 'contracts'
    permission_required = 'contracts.view_contract'

    def get_queryset(self):
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные услуги одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related('service')


class ContractDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра контракта."""
    model = Contract
    template_name = 'contracts/contracts-detail.html'
    permission_required = 'contracts.view_contract'

    def get_queryset(self):
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанную услугу одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related('service')


class ContractCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Представление для создания нового контракта."""
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contracts-create.html'
    permission_required = 'contracts.add_contract'

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse('contracts:detail', kwargs={'pk': self.object.pk})


class ContractUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Представление для редактирования контракта."""
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contracts-edit.html'
    permission_required = 'contracts.change_contract'

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse('contracts:detail', kwargs={'pk': self.object.pk})


class ContractDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Представление для "мягкого" удаления контракта."""
    model = Contract
    template_name = 'contracts/contracts-delete.html'
    success_url = reverse_lazy('contracts:list')
    permission_required = 'contracts.delete_contract'

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().
        """
        self.object.soft_delete()
        return HttpResponseRedirect(self.get_success_url())
