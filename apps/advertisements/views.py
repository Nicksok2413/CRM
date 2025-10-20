"""
Представления (Views) для приложения advertisements.
"""

import logging
from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import (
    Case,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Prefetch,
    ProtectedError,
    Q,
    QuerySet,
    Sum,
    When,
)
from django.db.models.functions import Coalesce
from django.forms.models import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from apps.customers.models import ActiveClient
from apps.leads.models import PotentialClient

from .filters import AdCampaignFilter
from .forms import AdCampaignForm, LeadStatusFilterForm
from .models import AdCampaign

# Получаем логгер для приложения
logger = logging.getLogger("apps.products")


class AdCampaignListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """Представление для отображения списка рекламных кампаний с фильтрацией, пагинацией и сортировкой."""

    model = AdCampaign
    template_name = "ads/ads-list.html"
    # Переименуем переменную контекста, чтобы соответствовать шаблону (ads)
    context_object_name = "ads"
    permission_required = "advertisements.view_adcampaign"

    # Подключаем класс фильтра
    filterset_class = AdCampaignFilter
    # Устанавливаем пагинацию
    paginate_by = 20

    def get_queryset(self) -> QuerySet[AdCampaign]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные услуги одним запросом, избегая проблемы "N+1".
        """
        queryset = super().get_queryset().select_related("service")

        # Оборачиваем результат в `cast`, чтобы mypy был уверен в типе
        return cast(QuerySet[AdCampaign], queryset)


class AdCampaignDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра рекламной кампании."""

    model = AdCampaign
    template_name = "ads/ads-detail.html"
    permission_required = "advertisements.view_adcampaign"

    def get_queryset(self) -> QuerySet[AdCampaign]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанную услугу одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related("service")


class AdCampaignCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Представление для создания новой рекламной кампании."""

    model = AdCampaign
    object: AdCampaign  # Явная аннотация для mypy
    form_class = AdCampaignForm
    template_name = "ads/ads-create.html"
    permission_required = "advertisements.add_adcampaign"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse("ads:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Переопределяем метод для логирования успешного создания объекта.
        """
        response = super().form_valid(form)

        logger.info(
            f"Пользователь '{self.request.user.username}' создал новую рекламную кампанию: '{self.object}' (PK={self.object.pk})."
        )
        messages.success(self.request, f'Рекламная кампания "{self.object}" успешно создана.')
        return response


class AdCampaignUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Представление для редактирования рекламной кампании."""

    model = AdCampaign
    object: AdCampaign  # Явная аннотация для mypy
    form_class = AdCampaignForm
    template_name = "ads/ads-edit.html"
    permission_required = "advertisements.change_adcampaign"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse("ads:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Переопределяем метод для логирования успешного редактирования объекта.
        """
        response = super().form_valid(form)

        logger.info(
            f"Пользователь '{self.request.user.username}' обновил рекламную кампанию: '{self.object}' (PK={self.object.pk})."
        )
        messages.success(self.request, f'Рекламная кампания "{self.object}" успешно обновлена.')
        return response


class AdCampaignDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Представление для "мягкого" удаления рекламной кампании."""

    model = AdCampaign
    template_name = "ads/ads-delete.html"
    success_url = reverse_lazy("ads:list")
    permission_required = "advertisements.delete_adcampaign"

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.

        Проверяем на защищенные связанные объекты перед "мягким" удалением.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().

        Raises:
            ProtectedError: Если найдены связанные объекты, прерывая удаление.
        """
        try:
            # Ищем всех лидов, полученных от этой рекламной кампании.
            protected_leads = PotentialClient.all_objects.filter(ad_campaign=self.object)

            if protected_leads.exists():
                raise ProtectedError("Невозможно удалить кампанию, от нее были получены лиды.", set(protected_leads))

            # Если проверка пройдена, выполняем "мягкое" удаление.
            self.object.soft_delete()

            logger.info(
                f"Рекламная кампании '{self.object}' (PK={self.object.pk}) была 'мягко' удалена (перемещена в архив) "
                f"пользователем '{self.request.user.username}'."
            )
            messages.success(self.request, f'Рекламная кампания "{self.object}" успешно перемещена в архив.')
            return HttpResponseRedirect(self.get_success_url())

        except ProtectedError as exc:
            # Если поймали ошибку, логируем и показываем пользователю сообщение.
            logger.warning(
                f"Заблокирована попытка удаления рекламной кампании '{self.object}' (PK={self.object.pk}) "
                f"пользователем '{self.request.user.username}', так как она защищена связанными объектами: {exc.protected_objects}"
            )

            messages.error(self.request, "Эту кампанию нельзя удалить, так как от нее были получены лиды.")
            # Возвращаем пользователя на детальную страницу.
            return HttpResponseRedirect(reverse("ads:detail", kwargs={"pk": self.object.pk}))


class AdCampaignStatisticView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """
    Представление для отображения статистики по рекламным кампаниям.
    """

    model = AdCampaign
    template_name = "ads/ads-statistic.html"
    context_object_name = "ads"
    # Согласно ТЗ, все роли могут смотреть статистику
    permission_required = "advertisements.view_adcampaign"

    # Подключаем класс фильтра
    filterset_class = AdCampaignFilter
    # Устанавливаем пагинацию
    paginate_by = 20

    def get_queryset(self) -> Any:
        """
        Переопределяем queryset для добавления вычисляемых полей (аннотаций).
        """
        # 1. Сначала получаем базовый queryset
        queryset = super().get_queryset()

        # 2. Добавляем аннотации
        annotated_queryset = queryset.annotate(
            # Количество уникальных лидов для каждой кампании, которые не были "мягко" удалены.
            leads_count=Count("leads", filter=Q(leads__is_deleted=False), distinct=True),
            # Количество активных клиентов для каждой кампании, которые не были "мягко" удалены.
            customers_count=Count(
                "leads__contracts_history", filter=Q(leads__contracts_history__is_deleted=False), distinct=True
            ),
            # Суммарный доход от контрактов активных клиентов.
            # Coalesce(..., 0) заменяет NULL на 0, если у кампании нет дохода.
            total_revenue=Coalesce(
                Sum("leads__contracts_history__contract__amount", filter=Q(leads__contracts_history__is_deleted=False)),
                0,
                output_field=DecimalField(),
            ),
            # Рассчитываем соотношение дохода к бюджету.
            # Используем Case/When, чтобы избежать деления на ноль, если бюджет равен 0.
            # Используем ExpressionWrapper, чтобы явно указать Django,
            # что результат деления должен быть DecimalField.
            # Это решает проблемы с типами данных на уровне базы данных.
            profit=Case(
                When(budget=0, then=None),  # Если бюджет 0, оставляем поле пустым
                default=ExpressionWrapper(
                    (F("total_revenue") / F("budget")) * 100,  # Умножаем на 100, чтобы получить проценты
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                ),
            ),
        )

        return annotated_queryset


class AdCampaignDetailStatisticView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Представление для детальной статистики по одной рекламной кампании.
    """

    model = AdCampaign
    template_name = "ads/ads-detail-statistic.html"  # Новый шаблон
    context_object_name = "ad"
    permission_required = "advertisements.view_adcampaign"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Переопределяем метод для добавления в контекст детальной статистики.
        Реализована логика кэширования для "тяжелых" вычислений.
        """
        # 1. Подготовка.

        # Получаем стандартный контекст и объект кампании.
        context = super().get_context_data(**kwargs)
        campaign = self.get_object()

        # Получаем значение фильтра из GET-параметров (например, 'active' или '').
        status_filter = self.request.GET.get("status", "")

        # 2. Работа с кэшем.

        # Создаем уникальный ключ кэша, который зависит от:
        # - ID рекламной кампании
        # - Выбранного фильтра по статусу
        cache_key = f"ad_campaign_stats_{campaign.pk}_status_{status_filter}"

        # Пытаемся получить вычисленные данные из кэша.
        computed_data = cache.get(cache_key)

        # Если данные нашлись в кэше.
        if computed_data:
            # Добавляем их в контекст и возвращаем результат.
            context.update(computed_data)
            return context

        # 3. "Тяжелые" вычисления (если данных в кэше нет).

        # Получаем всех лидов этой кампании, предзагружая историю контрактов.
        # И внутри этой предзагрузки также подтягиваем данные самих контрактов.
        leads_query = campaign.leads.all().prefetch_related(
            # Prefetch - для обратной связи (может быть много записей).
            Prefetch("contracts_history", queryset=ActiveClient.objects.select_related("contract"))
        )

        # Копируем queryset в список.
        leads_list = list(leads_query)

        # Форма фильтрации по статусу.
        status_filter_form = LeadStatusFilterForm(self.request.GET)

        # Логика фильтрации.
        if status_filter_form.is_valid():
            status = status_filter_form.cleaned_data.get("status")

            if status == "active":
                leads_list = [lead for lead in leads_list if lead.active_contract]
            elif status == "archived":
                leads_list = [
                    lead for lead in leads_list if not lead.active_contract and lead.contracts_history.exists()
                ]
            elif status == "in_work":
                leads_list = [lead for lead in leads_list if not lead.contracts_history.exists()]

        # Рассчитываем общую статистику на основе отфильтрованного списка.
        active_clients = [lead.active_contract for lead in leads_list if lead.active_contract is not None]
        total_revenue = sum(active_client.contract.amount for active_client in active_clients)

        # 4. Сохранение в кэш и возврат результата

        # Собираем все вычисленные данные в словарь.
        computed_data = {
            "leads_list": leads_list,
            "status_filter_form": status_filter_form,
            "total_leads": len(leads_list),
            "total_active_clients": len(active_clients),
            "total_revenue": total_revenue,
            "profit": (total_revenue / campaign.budget) * 100 if campaign.budget > 0 else None,
        }

        # Сохраняем словарь в кэш на 15 минут.
        # В следующий раз, когда кто-то запросит эту же страницу с этим же фильтром, возьмем данные отсюда.
        cache.set(cache_key, computed_data, timeout=60 * 15)

        # Добавляем вычисленные данные в контекст.
        context.update(computed_data)

        # Возвращаем контекст.
        return context
