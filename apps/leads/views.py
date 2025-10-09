"""
Представления (Views) для приложения leads.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import PotentialClientForm
from .models import PotentialClient


class LeadListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Представление для отображения списка лидов."""
    model = PotentialClient
    template_name = 'leads/leads-list.html'
    context_object_name = 'leads'
    # Право на просмотр будет и у Оператора, и у Менеджера
    permission_required = 'leads.view_potentialclient'

    def get_queryset(self):
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные рекламные кампании одним запросом, избегая проблемы "N+1".
        """
        # queryset будет содержать лидов + данные по их рекламным кампаниям
        return super().get_queryset().select_related('ad_campaign')


class LeadDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра лида."""
    model = PotentialClient
    template_name = 'leads/leads-detail.html'
    permission_required = 'leads.view_potentialclient'

    def get_queryset(self):
        """
        Переопределяем queryset для оптимизации на детальной странице.

        **Почему это полезно?**
        Если на детальной странице лида нужно показать
        не только название рекламной кампании (`object.ad_campaign.name`),
        но и название услуги, ради которой эта кампания была запущена (`object.ad_campaign.service.name`),
        этот двойной `JOIN` (`ad_campaign__service`)
        позволит получить все три сущности (Лид, Кампания, Услуга) одним запросом.
        """
        # queryset будет содержать лида + данные по РК + данные по услуге
        return super().get_queryset().select_related('ad_campaign__service')


class LeadCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Представление для создания нового лида."""
    model = PotentialClient
    form_class = PotentialClientForm
    template_name = 'leads/leads-create.html'
    # Право на добавление будет только у Оператора
    permission_required = 'leads.add_potentialclient'

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse('leads:detail', kwargs={'pk': self.object.pk})


class LeadUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Представление для редактирования лида."""
    model = PotentialClient
    form_class = PotentialClientForm
    template_name = 'leads/leads-edit.html'
    # Право на изменение будет только у Оператора
    permission_required = 'leads.change_potentialclient'

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse('leads:detail', kwargs={'pk': self.object.pk})


class LeadDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Представление для "мягкого" удаления лида."""
    model = PotentialClient
    template_name = 'leads/leads-delete.html'
    success_url = reverse_lazy('leads:list')
    # Право на удаление будет только у Оператора
    permission_required = 'leads.delete_potentialclient'

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().
        """
        self.object.soft_delete()
        return HttpResponseRedirect(self.get_success_url())
