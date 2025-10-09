"""
Представления (Views) для приложения advertisements.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import AdCampaignForm
from .models import AdCampaign


class AdCampaignListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Представление для отображения списка рекламных кампаний."""
    model = AdCampaign
    template_name = 'ads/ads-list.html'
    # Переименуем переменную контекста, чтобы соответствовать шаблону (ads)
    context_object_name = 'ads'
    permission_required = 'advertisements.view_adcampaign'


class AdCampaignDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра рекламной кампании."""
    model = AdCampaign
    template_name = 'ads/ads-detail.html'
    permission_required = 'advertisements.view_adcampaign'


class AdCampaignCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Представление для создания новой рекламной кампании."""
    model = AdCampaign
    form_class = AdCampaignForm
    template_name = 'ads/ads-create.html'
    permission_required = 'advertisements.add_adcampaign'

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse('ads:detail', kwargs={'pk': self.object.pk})



class AdCampaignUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Представление для редактирования рекламной кампании."""
    model = AdCampaign
    form_class = AdCampaignForm
    template_name = 'ads/ads-edit.html'
    permission_required = 'advertisements.change_adcampaign'

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse('ads:detail', kwargs={'pk': self.object.pk})


class AdCampaignDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Представление для "мягкого" удаления рекламной кампании."""
    model = AdCampaign
    template_name = 'ads/ads-delete.html'
    success_url = reverse_lazy('ads:list')
    permission_required = 'advertisements.delete_adcampaign'

    def form_valid(self, form) -> HttpResponseRedirect:
        """
        Переопределяем метод для выполнения "мягкого" удаления.
        """
        self.object.soft_delete()
        return HttpResponseRedirect(self.get_success_url())

# Примечание: Представление для страницы статистики (ads-statistic.html)
# создам позже, так как оно требует более сложной логики с аннотациями.
# Пока фокусируюсь на стандартном CRUD.
