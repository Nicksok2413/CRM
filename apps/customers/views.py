"""
Представления (Views) для приложения customers.
"""

import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseBase, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from apps.leads.models import PotentialClient

from .filters import ActiveClientFilter
from .forms import ActiveClientCreateForm, ActiveClientUpdateForm
from .models import ActiveClient

# Получаем логгер для приложения.
logger = logging.getLogger("apps.customers")


class ActiveClientListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """Представление для отображения списка всех активных клиентов с фильтрацией, пагинацией и сортировкой."""

    model = ActiveClient
    template_name = "customers/customers-list.html"
    context_object_name = "customers"
    permission_required = "customers.view_activeclient"

    # Подключаем класс фильтра.
    filterset_class = ActiveClientFilter
    # Устанавливаем пагинацию.
    paginate_by = 25

    def get_queryset(self) -> QuerySet[ActiveClient]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает данные из двух связанных моделей
        (лида и контракта) одним запросом, избегая проблемы "N+1".
        """
        # Получаем пользователя из запроса.
        user = self.request.user

        # Получаем базовый queryset с оптимизацией.
        # Он будет содержать данные активных клиентов + лидов + контрактов и услуг.
        base_queryset = super().get_queryset().select_related("potential_client", "contract__service")

        # Проверяем, есть ли у пользователя глобальное право на просмотр всех активных клиентов.
        # Это право обычно есть у суперпользователей, администраторов.
        if user.has_perm("customers.view_activeclient"):
            # Если право есть - возвращаем всех активных клиентов.
            return base_queryset

        # # Если глобального права нет - фильтруем по полю manager у связанного лида.
        return base_queryset.filter(potential_client__manager=user)

        # queryset = super().get_queryset().select_related("potential_client", "contract__service")
        #
        # # Оборачиваем результат в `cast`, чтобы mypy был уверен в типе.
        # return cast(QuerySet[ActiveClient], queryset)


class ActiveClientDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра активного клиента."""

    model = ActiveClient
    template_name = "customers/customers-detail.html"
    permission_required = "customers.view_activeclient"

    def get_queryset(self) -> QuerySet[ActiveClient]:
        """
        Переопределяем queryset для оптимизации на детальной странице.
        select_related подгружает данные из двух связанных моделей
        (лида и контракта) одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related("potential_client", "contract")


class ActiveClientUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Представление для редактирования записи об активном клиенте.
    Позволяет привязать клиента к другому контракту.
    """

    model = ActiveClient
    object: ActiveClient  # Явная аннотация для mypy
    form_class = ActiveClientUpdateForm  # Используем специальную форму для редактирования
    template_name = "customers/customers-edit.html"
    permission_required = "customers.change_activeclient"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse("customers:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Переопределяем метод для логирования успешного редактирования объекта.
        """
        response = super().form_valid(form)

        logger.info(
            f"Пользователь '{self.request.user.username}' обновил запись активного клиента: '{self.object}' (PK={self.object.pk})."
        )
        messages.success(self.request, "Данные активного клиента успешно обновлены.")
        return response


class ActiveClientDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Представление для "мягкого" удаления записи об активном клиенте.
    Деактивирует клиента, но не удаляет его данные из системы.
    """

    model = ActiveClient
    template_name = "customers/customers-delete.html"
    success_url = reverse_lazy("customers:list")
    permission_required = "customers.delete_activeclient"

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().
        """
        # Для ActiveClient нет защищенных объектов, удаление всегда возможно.
        self.object.soft_delete()

        logger.info(
            f"Пользователь '{self.request.user.username}' 'мягко' удалил (деактивировал) "
            f"клиента: '{self.object}' (PK={self.object.pk})."
        )
        messages.success(self.request, f'Активный клиент "{self.object}" был успешно удален.')
        return HttpResponseRedirect(self.get_success_url())


class ActiveClientCreateFromLeadView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Специализированное представление для ключевого бизнес-процесса:
    "активации" Потенциального клиента.
    """

    model = ActiveClient
    form_class = ActiveClientCreateForm  # Используем специальную форму для создания
    template_name = "customers/customers-create.html"
    permission_required = "customers.add_activeclient"

    # Явно аннотируем self.lead для mypy, так как он создается в dispatch.
    lead: PotentialClient

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """
        Переопределяем метод `dispatch` для выполнения проверок до того, как будет показана форма.
        Проверяет, можно ли в принципе инициировать активацию для данного лида.
        """

        # Извлекаем PK лида из URL (например, /customers/new/from-lead/15/).
        lead_pk = self.kwargs.get("lead_pk")

        logger.debug(f"Пользователь '{request.user.username}' инициировал активацию лида с PK={lead_pk}.")

        # Получаем объект лида или возвращаем ошибку 404, если лид не найден.
        self.lead = get_object_or_404(PotentialClient, pk=lead_pk)

        # Проверяем, не является ли лид уже активным клиентом.
        # Если да - перенаправляем обратно с сообщением об ошибке.
        # Запрещаем активацию, только если статус лида уже "Конвертирован".
        # Это позволяет повторно активировать "потерянных" клиентов
        # или тех, у кого закончился старый контракт.
        if self.lead.status == PotentialClient.Status.CONVERTED:
            messages.error(request, f'Клиент "{self.lead}" уже является активным.')
            return HttpResponseRedirect(reverse("leads:list"))  # Возвращаемся в список лидов

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self) -> dict[str, Any]:
        """
        Передаем начальные данные в форму.
        Это скрытое поле с ID лида, которого мы активируем.
        """
        initial = super().get_initial()
        initial["potential_client"] = self.lead
        return initial

    def get_form_kwargs(self) -> dict[str, Any]:
        """
        Передаем объект `lead` в конструктор формы, чтобы она могла отфильтровать контракты.
        """
        # Получаем стандартный набор kwargs от родительского класса.
        kwargs = super().get_form_kwargs()

        # Добавляем в словарь объект `self.lead` под ключом 'lead'.
        # Именно этот ключ "ловим" в `__init__` формы ActiveClientCreateForm.
        kwargs["lead"] = self.lead
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Вызывается после успешной валидации формы.
        Меняем статус лида после его конвертации.
        """
        # Сначала вызываем родительский метод.
        # Он создает и сохраняет объект `ActiveClient` и помещает его в `self.object`.
        response = super().form_valid(form)

        # Проверяем, что self.object (экземпляр ActiveClient) был успешно создан родительским методом.
        if self.object:
            # Проверяем, что у лида еще не статус "Конвертирован"
            if self.lead.status != PotentialClient.Status.CONVERTED:
                # Обновляем статус лида.
                self.lead.status = PotentialClient.Status.CONVERTED
                # Сохраняем только измененное поле для эффективности.
                self.lead.save(update_fields=["status"])

            logger.info(
                f"Лид '{self.lead}' (PK={self.lead.pk}) успешно конвертирован в активного клиента "
                f"пользователем '{self.request.user.username}'. "
                f"Привязан контракт с PK={self.object.contract.pk}."
            )

        else:
            # Этот блок кода вряд ли когда-либо выполнится в CreateView,
            # но он делает логику полной и защищает от непредвиденных случаев.
            logger.error(
                f"Не удалось создать объект ActiveClient для лида '{self.lead}' (PK={self.lead.pk}) "
                f"пользователем '{self.request.user.username}'."
            )

        # Сообщение об успехе и редирект остаются в get_success_url
        return response

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Добавляем в контекст шаблона объект `lead` для отображения информации о нем.
        """
        context = super().get_context_data(**kwargs)
        context["lead"] = self.lead
        return context

    def get_success_url(self) -> str:
        """
        Перенаправляем на список активных клиентов после успешной активации.
        """
        messages.success(self.request, f'Клиент "{self.lead}" успешно активирован.')
        return reverse("customers:list")
