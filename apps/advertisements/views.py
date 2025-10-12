"""
Представления (Views) для приложения advertisements.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Case, Count, DecimalField,  ExpressionWrapper, F, Q, QuerySet, Sum, When
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
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

    def get_queryset(self):
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные услуги одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related('service')


class AdCampaignDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра рекламной кампании."""
    model = AdCampaign
    template_name = 'ads/ads-detail.html'
    permission_required = 'advertisements.view_adcampaign'

    def get_queryset(self):
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанную услугу одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related('service')


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
        Переопределяем метод form_valid для выполнения "мягкого" удаления.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().
        """
        self.object.soft_delete()
        return HttpResponseRedirect(self.get_success_url())


class AdCampaignStatisticView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Представление для отображения статистики по рекламным кампаниям.
    """
    model = AdCampaign
    template_name = 'ads/ads-statistic.html'
    context_object_name = 'ads'
    # Согласно ТЗ, все роли могут смотреть статистику
    permission_required = 'advertisements.view_adcampaign'

    def get_queryset(self) -> QuerySet[AdCampaign]:
        """
        Переопределяем queryset для добавления вычисляемых полей (аннотаций).
        """
        # 1. Сначала получаем базовый queryset
        queryset = super().get_queryset()

        # 2. Добавляем аннотации
        annotated_queryset = queryset.annotate(
            # Количество уникальных лидов для каждой кампании
            leads_count=Count('leads', distinct=True),

            # Количество активных клиентов.
            # Мы считаем только те записи `ActiveClient`, которые не были "мягко" удалены.
            customers_count=Count(
                'leads__contracts_history',
                filter=Q(leads__contracts_history__is_deleted=False),
                distinct=True
            ),

            # Суммарный доход от контрактов активных клиентов.
            # Coalesce(..., 0) заменяет NULL на 0, если у кампании нет дохода.
            total_revenue=Coalesce(
                Sum(
                    'leads__contracts_history__contract__amount',
                    filter=Q(leads__contracts_history__is_deleted=False)
                ),
                0,
                output_field=DecimalField()
            ),

            # # Рассчитываем соотношение дохода к бюджету.
            # # Используем Case/When, чтобы избежать деления на ноль, если бюджет равен 0.
            # profit_ratio=Case(
            #     When(budget=0, then=None),  # Если бюджет 0, оставляем поле пустым
            #     default=(F('total_revenue') / F('budget')),
            #     output_field=DecimalField(decimal_places=2)
            # )

            # Используем ExpressionWrapper, чтобы явно указать Django,
            # что результат деления должен быть DecimalField.
            # Это решает проблемы с типами данных на уровне базы данных.
            profit_ratio=Case(
                When(budget=0, then=None),  # По-прежнему избегаем деления на ноль
                default=ExpressionWrapper(
                    (F('total_revenue') / F('budget')) * 100,  # Умножаем на 100, чтобы получить проценты
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
        )

        return annotated_queryset
