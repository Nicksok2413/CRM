"""
Представления (Views) для приложения leads.
"""

import logging
from datetime import timedelta
from typing import cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, ProtectedError, QuerySet
from django.db.models.functions import TruncDay
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django_filters.views import FilterView
from guardian.shortcuts import get_objects_for_user

from apps.common.views import (
    BaseCreateView,
    BaseObjectDeleteView,
    BaseObjectDetailView,
    BaseObjectUpdateView,
)
from apps.customers.models import ActiveClient

from .filters import LeadFilter
from .forms import PotentialClientForm
from .models import PotentialClient

# Получаем логгер для приложения.
logger = logging.getLogger("apps.leads")


class LeadListView(LoginRequiredMixin, FilterView):
    """
    Представление для отображения списка лидов с фильтрацией, пагинацией и сортировкой.

    Имеет кастомную логику queryset для учета прав доступа.
    """

    model = PotentialClient
    template_name = "leads/leads-list.html"
    context_object_name = "leads"

    # Подключаем класс фильтра
    filterset_class = LeadFilter
    # Устанавливаем пагинацию
    paginate_by = 25

    def get_queryset(self) -> QuerySet[PotentialClient]:
        """
        Возвращает queryset, отфильтрованный в соответствии с правами пользователя.
        - Пользователи с глобальным правом `view_potentialclient` видят всех.
        - Остальные (Менеджеры) видят только их лидов.
        """
        # Получаем пользователя из запроса.
        user = self.request.user

        # Получаем базовый queryset с оптимизацией.
        # Он будет содержать лидов + данные по их рекламным кампаниям + менеджера.
        base_queryset = PotentialClient.objects.select_related("ad_campaign", "manager")

        # Проверяем, есть ли у пользователя глобальное право на просмотр всех лидов.
        # Это право обычно есть у суперпользователей, администраторов.
        if user.has_perm("leads.view_potentialclient"):
            # Если право есть - возвращаем всех лидов.
            return base_queryset

        # Если глобального права нет, возвращаем только те объекты,
        # на которые у пользователя есть объектное право.
        return get_objects_for_user(user, "leads.view_potentialclient", klass=base_queryset)


class LeadDetailView(BaseObjectDetailView):
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
        queryset = super().get_queryset().select_related("ad_campaign__service")

        # Оборачиваем результат в `cast`, чтобы mypy был уверен в типе
        return cast(QuerySet[PotentialClient], queryset)


class LeadCreateView(BaseCreateView):
    """Представление для создания нового лида."""

    model = PotentialClient
    object: PotentialClient  # Явная аннотация для mypy
    form_class = PotentialClientForm
    template_name = "leads/leads-create.html"
    permission_required = "leads.add_potentialclient"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse("leads:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Переопределяем метод для логирования успешного создания объекта.
        """
        response = super().form_valid(form)

        logger.info(
            f"Пользователь '{self.request.user.username}' создал нового лида: '{self.object}' (PK={self.object.pk})."
        )
        messages.success(self.request, f'Лид "{self.object}" успешно создан.')
        return response


class LeadUpdateView(BaseObjectUpdateView):
    """Представление для редактирования лида."""

    model = PotentialClient
    object: PotentialClient  # Явная аннотация для mypy
    form_class = PotentialClientForm
    template_name = "leads/leads-edit.html"
    permission_required = "leads.change_potentialclient"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse("leads:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Переопределяем метод для логирования успешного редактирования объекта.
        """
        response = super().form_valid(form)

        logger.info(f"Пользователь '{self.request.user.username}' обновил лида: '{self.object}' (PK={self.object.pk}).")
        messages.success(self.request, f'Лид "{self.object}" успешно обновлен.')
        return response


class LeadDeleteView(BaseObjectDeleteView):
    """Представление для "мягкого" удаления лида."""

    model = PotentialClient
    object: PotentialClient  # Явная аннотация для mypy
    template_name = "leads/leads-delete.html"
    success_url = reverse_lazy("leads:list")
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
            contracts_history = ActiveClient.all_objects.filter(potential_client=self.object)

            if contracts_history.exists():
                raise ProtectedError(
                    "Невозможно удалить лида: у него есть история контрактов.",
                    set(contracts_history),
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


class UpdateLeadStatusView(LoginRequiredMixin, View):
    """
    Базовый View для смены статуса лида.

    Принимает id и новый статус из URL.
    Проверяет объектные права вручную.
    """

    def post(self, request: HttpRequest, pk: int, status: str) -> HttpResponse:
        # Получаем лида.
        lead = get_object_or_404(PotentialClient, pk=pk)

        # Проверяем, есть ли у пользователя право 'change_potentialclient' на конкретный объект 'lead'.
        if not request.user.has_perm("leads.change_potentialclient", lead):
            logger.warning(
                f"Пользователь '{request.user.username}' пытался изменить статус лида PK={pk}, не имея на это прав."
            )
            # Если прав нет - вызываем ошибку 403.
            raise PermissionDenied

        # Запоминаем старый статус для лога.
        old_status = lead.get_status_display()

        # Проверяем, что переданный статус валиден.
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

        # Возвращаемся на детальную страницу лида.
        return redirect("leads:detail", pk=lead.pk)


def get_lead_creation_stats(request: HttpRequest) -> JsonResponse:
    """
    API-endpoint, возвращающий статистику создания лидов
    за последние 30 дней в формате JSON.
    """

    # Проверяем аутентификацию пользователя.
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)

    # Определяем диапазон дат.
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Выполняем "тяжелый" запрос к БД.
    # Группируем лидов по дню создания и считаем их количество.
    stats_from_db = (
        PotentialClient.objects.filter(created_at__gte=thirty_days_ago)
        .annotate(day=TruncDay("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    # Создаем словарь для быстрого поиска: {дата: количество}
    stats_dict = {stat["day"].date(): stat["count"] for stat in stats_from_db}

    # Генерируем полный список дат за последние 30 дней.
    today = timezone.now().date()
    date_range = [today - timedelta(days=i) for i in range(29, -1, -1)]

    # Форматируем данные для Chart.js, подставляя 0 там, где не было лидов.
    # Нам нужны два массива: labels (даты) и data (количества).
    labels = [day.strftime("%d-%m") for day in date_range]
    data = [stats_dict.get(day, 0) for day in date_range]

    response_data = {
        "labels": labels,
        "data": data,
    }

    return JsonResponse(response_data)
