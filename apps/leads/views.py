"""
Представления (Views) для приложения leads.
"""

import logging

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

from apps.customers.models import ActiveClient

from .filters import LeadFilter
from .forms import PotentialClientForm
from .models import PotentialClient

# Получаем логгер для приложения
logger = logging.getLogger("apps.leads")


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
            history = ActiveClient.all_objects.filter(potential_client=self.object)

            if history.exists():
                raise ProtectedError(
                    "Невозможно удалить лида: у него есть история контрактов.",
                    set(history),
                )

            # Если проверка пройдена, выполняем "мягкое" удаление.
            self.object.soft_delete()

            logger.info(
                f"Лид '{self.object}' (PK={self.object.pk}) был 'мягко' удален (перемещен в архив) "
                f"пользователем '{self.request.user.username}'."
            )
            messages.success(self.request, f'Лид "{self.object}" успешно перемещен в архив.')
            return HttpResponseRedirect(self.get_success_url())

        except ProtectedError as exc:
            # Если поймали ошибку, логируем и показываем пользователю сообщение.
            logger.warning(
                f"Заблокирована попытка удаления лида '{self.object}' (PK={self.object.pk}) "
                f"пользователем '{self.request.user.username}', так как он защищен связанными объектами: {exc.protected_objects}"
            )
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
        old_status = lead.get_status_display()  # Запоминаем старый статус для лога

        # Проверяем, что переданный статус валиден
        valid_statuses = [status[0] for status in PotentialClient.Status.choices]

        if status in valid_statuses:
            lead.status = status
            lead.save(update_fields=["status"])

            logger.info(
                f"Статус лида '{lead}' (PK={pk}) изменен с '{old_status}' на '{lead.get_status_display()}' "
                f"пользователем '{request.user.username}'."
            )
            messages.success(request, f'Статус клиента "{lead}" изменен на "{lead.get_status_display()}".')
        else:
            logger.error(
                f"Попытка установить некорректный статус '{status}' для лида с PK={pk} "
                f"пользователем '{request.user.username}'."
            )
            messages.error(request, "Некорректный статус.")

        # Возвращаемся на детальную страницу лида
        return redirect("leads:detail", pk=lead.pk)
