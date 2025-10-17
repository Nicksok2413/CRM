"""
Представления (Views) для приложения leads.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import ProtectedError, QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from .filters import LeadFilter
from .forms import PotentialClientForm
from .models import PotentialClient


class LeadListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """Представление для отображения списка лидов с фильтрацией, пагинацией и сортировкой."""

    model = PotentialClient
    template_name = "leads/leads-list.html"
    context_object_name = "leads"
    permission_required = "leads.view_potentialclient"

    # Подключаем класс фильтра
    filterset_class = LeadFilter
    # Устанавливаем пагинацию
    paginate_by = 25

    def get_queryset(self) -> QuerySet[PotentialClient]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные рекламные кампании одним запросом, избегая проблемы "N+1".
        """
        # queryset будет содержать лидов + данные по их рекламным кампаниям
        return super().get_queryset().select_related("ad_campaign")


class LeadDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра лида."""

    model = PotentialClient
    template_name = "leads/leads-detail.html"
    permission_required = "leads.view_potentialclient"

    def get_queryset(self) -> QuerySet[PotentialClient]:
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
        return super().get_queryset().select_related("ad_campaign__service")


class LeadCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Представление для создания нового лида."""

    model = PotentialClient
    object: PotentialClient  # Явная аннотация для mypy
    form_class = PotentialClientForm
    template_name = "leads/leads-create.html"
    # Право на добавление будет только у Оператора
    permission_required = "leads.add_potentialclient"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse("leads:detail", kwargs={"pk": self.object.pk})


class LeadUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Представление для редактирования лида."""

    model = PotentialClient
    object: PotentialClient  # Явная аннотация для mypy
    form_class = PotentialClientForm
    template_name = "leads/leads-edit.html"
    # Право на изменение будет только у Оператора
    permission_required = "leads.change_potentialclient"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse("leads:detail", kwargs={"pk": self.object.pk})


class LeadDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Представление для "мягкого" удаления лида."""

    model = PotentialClient
    template_name = "leads/leads-delete.html"
    success_url = reverse_lazy("leads:list")
    # Право на удаление будет только у Оператора
    permission_required = "leads.delete_potentialclient"

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.

        Проверяем на защищенные связанные объекты перед "мягким" удалением.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().

        Raises:
            ProtectedError: Если найдены связанные объекты, прерывая удаление.
        """
        try:
            # Проверяем историю контрактов лида.
            if self.object.contracts_history.all_objects.exists():
                raise ProtectedError(
                    "Невозможно удалить лида: у него есть история контрактов.",
                    self.object.contracts_history.all_objects.all(),
                )

            # Если проверка пройдена, выполняем "мягкое" удаление.
            self.object.soft_delete()
            messages.success(self.request, f'Лид "{self.object}" успешно перемещен в архив.')
            return HttpResponseRedirect(self.get_success_url())

        except ProtectedError:
            # Если поймали ошибку, показываем пользователю сообщение.
            messages.error(self.request, "Этого лида нельзя удалить, так как у него есть история контрактов.")
            # Возвращаем пользователя на детальную страницу.
            return HttpResponseRedirect(reverse("leads:detail", kwargs={"pk": self.object.pk}))


class UpdateLeadStatusView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Базовый View для смены статуса лида.
    Принимает рекламную кампанию лида и новый статус из URL.
    """

    permission_required = "leads.change_potentialclient"

    def post(self, request, pk, status):
        lead = get_object_or_404(PotentialClient, pk=pk)

        # Проверяем, что переданный статус валиден
        valid_statuses = [status[0] for status in PotentialClient.Status.choices]

        if status in valid_statuses:
            lead.status = status
            lead.save(update_fields=["status"])
            messages.success(request, f'Статус клиента "{lead}" изменен на "{lead.get_status_display()}".')
        else:
            messages.error(request, "Некорректный статус.")

        # Возвращаемся на детальную страницу лида
        return redirect("leads:detail", pk=lead.pk)
