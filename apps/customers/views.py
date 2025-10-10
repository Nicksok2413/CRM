"""
Представления (Views) для приложения customers.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView

from .forms import ActiveClientForm
from .models import ActiveClient
from apps.leads.models import PotentialClient


class ActiveClientCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Представление для создания Активного клиента из Потенциального.
    """
    model = ActiveClient
    form_class = ActiveClientForm
    template_name = 'customers/customers-create.html'
    permission_required = 'customers.add_activeclient'

    def dispatch(self, request, *args, **kwargs):
        """
        Переопределяем dispatch для выполнения проверок до отображения формы.
        """
        # Получаем лида из URL или возвращаем 404
        lead_pk = self.kwargs.get('lead_pk')
        self.lead = get_object_or_404(PotentialClient, pk=lead_pk)

        # Проверяем, не является ли лид уже активным клиентом.
        # Если да - перенаправляем обратно с сообщением об ошибке.
        if hasattr(self.lead, 'active_client_status'):
            messages.error(request, f'Клиент "{self.lead}" уже является активным.')
            return HttpResponseRedirect(reverse('leads:list'))

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> dict:
        """
        Передаем начальные данные в форму.
        Это скрытое поле с ID лида.
        """
        initial = super().get_initial()
        initial['potential_client'] = self.lead
        return initial

    def get_context_data(self, **kwargs) -> dict:
        """
        Добавляем в контекст шаблона объект лида для отображения информации о нем.
        """
        context = super().get_context_data(**kwargs)
        context['lead'] = self.lead
        return context

    def get_success_url(self) -> str:
        """
        Перенаправляем на детальную страницу лида после активации.
        """
        messages.success(self.request, f'Клиент "{self.lead}" успешно активирован.')
        return reverse('leads:detail', kwargs={'pk': self.lead.pk})
