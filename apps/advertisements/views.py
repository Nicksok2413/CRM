"""
Представления (Views) для приложения advertisements.
"""

import logging
from typing import Any, cast

from django.contrib import messages
from django.core.cache import cache
from django.db.models import ProtectedError, QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from apps.common.views import (
    BaseCreateView,
    BaseListView,
    BaseObjectDeleteView,
    BaseObjectDetailView,
    BaseObjectUpdateView,
)
from apps.leads.models import PotentialClient

from .filters import AdCampaignFilter
from .forms import AdCampaignForm, LeadStatusFilterForm
from .models import AdCampaign
from .selectors import get_campaigns_with_stats, get_detailed_stats_for_campaign

# Получаем логгер для приложения.
logger = logging.getLogger("apps.products")


class AdCampaignListView(BaseListView):
    """Представление для отображения списка рекламных кампаний с фильтрацией, пагинацией и сортировкой."""

    model = AdCampaign
    template_name = "ads/ads-list.html"
    # Переименуем переменную контекста, чтобы соответствовать шаблону (ads).
    context_object_name = "ads"
    permission_required = "advertisements.view_adcampaign"

    # Подключаем класс фильтра, который включает логику фильтрации и сортировки.
    filterset_class = AdCampaignFilter
    # Устанавливаем пагинацию.
    paginate_by = 20

    def get_queryset(self) -> QuerySet[AdCampaign]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные услуги одним запросом, избегая проблемы "N+1".
        """
        queryset = super().get_queryset().select_related("service")

        # Оборачиваем результат в `cast`, чтобы mypy был уверен в типе
        return cast(QuerySet[AdCampaign], queryset)


class AdCampaignDetailView(BaseObjectDetailView):
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


class AdCampaignCreateView(BaseCreateView):
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


class AdCampaignUpdateView(BaseObjectUpdateView):
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


class AdCampaignDeleteView(BaseObjectDeleteView):
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


class AdCampaignStatisticView(BaseListView):
    """
    Представление для отображения статистики по рекламным кампаниям.
    """

    model = AdCampaign
    template_name = "ads/ads-statistic.html"
    context_object_name = "ads"
    permission_required = "advertisements.view_adcampaign"

    # Подключаем класс фильтра, который включает логику фильтрации и сортировки.
    filterset_class = AdCampaignFilter
    # Устанавливаем пагинацию.
    paginate_by = 20

    def get_queryset(self) -> QuerySet[AdCampaign]:
        """
        Делегирует получение аннотированного queryset селектору `get_campaigns_with_stats`.
        """
        return get_campaigns_with_stats()


class AdCampaignDetailStatisticView(BaseObjectDetailView):
    """
    Представление для детальной статистики по одной рекламной кампании.
    Использует кэширование для повышения производительности.
    """

    model = AdCampaign
    template_name = "ads/ads-detail-statistic.html"  # Шаблон детальной статистики
    context_object_name = "ad"
    permission_required = "advertisements.view_adcampaign"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Переопределяем метод для сбора и кэширования контекста для детальной страницы статистики.
        Делегирует вычисления данных селектору `get_detailed_stats_for_campaign`.
        """
        # 1. Подготовка.

        # Получаем стандартный контекст и объект кампании.
        context = super().get_context_data(**kwargs)
        campaign = self.get_object()

        # Создаем экземпляр формы фильтрации по статусу с данными из GET-запроса.
        status_filter_form = LeadStatusFilterForm(self.request.GET)

        # 2. Валидируем форму.

        # Если данные в GET некорректны, is_valid() вернет False.
        if not status_filter_form.is_valid():
            # На случай, если кто-то подделает GET-параметр.
            # Просто сбрасываем фильтр до значения по умолчанию.
            status_filter = ""
        else:
            # Если все в порядке, берем очищенное значение.
            status_filter = status_filter_form.cleaned_data.get("status", "")

        # 3. Работа с кэшем.

        # Создаем уникальный ключ кэша, который зависит от:
        # - ID рекламной кампании
        # - Выбранного фильтра по статусу
        cache_key = f"ad_campaign_stats_{campaign.pk}_status_{status_filter}"

        # Пытаемся получить вычисленные данные из кэша.
        computed_data = cache.get(cache_key)

        # Если данных в кэше нет.
        if not computed_data:
            logger.debug(f"Кэш для ключа '{cache_key}' не найден. Выполняем вычисления.")

            # Вызываем селектор для вычисления данных.
            # Передаем в селектор кампанию и значение фильтра.
            computed_data = get_detailed_stats_for_campaign(campaign=campaign, status_filter=status_filter)

            # Сохраняем результат в кэш на 15 минут.
            # В следующий раз, когда кто-то запросит эту же страницу с этим же фильтром, возьмем данные отсюда.
            cache.set(cache_key, computed_data, timeout=60 * 1)

        # Добавляем данные и форму в контекст.
        context.update(computed_data)
        context["status_filter_form"] = status_filter_form

        # Возвращаем контекст.
        return context
