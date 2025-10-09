"""
Представления (Views) для приложения products.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, DeleteView, ListView, UpdateView

from .forms import ServiceForm
from .models import Service


class ServiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Представление для отображения списка услуг."""
    model = Service
    template_name = 'products/products-list.html'
    context_object_name = 'products'
    permission_required = 'products.view_service'


class ServiceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра услуги."""
    model = Service
    template_name = 'products/products-detail.html'
    permission_required = 'products.view_service'


class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Представление для создания новой услуги."""
    model = Service
    form_class = ServiceForm
    template_name = 'products/products-create.html'
    success_url = reverse_lazy('products:list')
    permission_required = 'products.add_service'


class ServiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Представление для редактирования услуги."""
    model = Service
    form_class = ServiceForm
    template_name = 'products/products-edit.html'
    success_url = reverse_lazy('products:detail')
    permission_required = 'products.change_service'


class ServiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Представление для "мягкого" удаления услуги.
    """
    model = Service
    template_name = 'products/products-delete.html'
    success_url = reverse_lazy('products:list')
    permission_required = 'products.delete_service'

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().
        """
        self.object.soft_delete()
        return HttpResponseRedirect(self.get_success_url())
