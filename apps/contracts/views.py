"""
Представления (Views) для приложения contracts.
"""

import logging
from typing import cast

from django.contrib import messages
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

from .filters import ContractFilter
from .forms import ContractForm
from .models import Contract

# Получаем логгер для приложения
logger = logging.getLogger("apps.contracts")


class ContractListView(BaseListView):
    """Представление для отображения списка контрактов с фильтрацией, пагинацией и сортировкой."""

    model = Contract
    template_name = "contracts/contracts-list.html"
    context_object_name = "contracts"
    permission_required = "contracts.view_contract"

    # Подключаем класс фильтра
    filterset_class = ContractFilter
    # Устанавливаем пагинацию
    paginate_by = 25

    def get_queryset(self) -> QuerySet[Contract]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанные услуги одним запросом, избегая проблемы "N+1".
        """
        queryset = super().get_queryset().select_related("service")

        # Оборачиваем результат в `cast`, чтобы mypy был уверен в типе
        return cast(QuerySet[Contract], queryset)


class ContractDetailView(BaseObjectDetailView):
    """Представление для детального просмотра контракта."""

    model = Contract
    template_name = "contracts/contracts-detail.html"
    permission_required = "contracts.view_contract"

    def get_queryset(self) -> QuerySet[Contract]:
        """
        Переопределяем queryset для оптимизации.
        select_related подгружает связанную услугу одним запросом, избегая проблемы "N+1".
        """
        return super().get_queryset().select_related("service")


class ContractCreateView(BaseCreateView):
    """Представление для создания нового контракта."""

    model = Contract
    object: Contract  # Явная аннотация для mypy
    form_class = ContractForm
    template_name = "contracts/contracts-create.html"
    permission_required = "contracts.add_contract"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse("contracts:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Переопределяем метод для логирования успешного создания объекта.
        """
        response = super().form_valid(form)

        logger.info(
            f"Пользователь '{self.request.user.username}' создал новый контракт: '{self.object}' (PK={self.object.pk})."
        )
        messages.success(self.request, f'Контракт "{self.object}" успешно создан.')
        return response


class ContractUpdateView(BaseObjectUpdateView):
    """Представление для редактирования контракта."""

    model = Contract
    object: Contract  # Явная аннотация для mypy
    form_class = ContractForm
    template_name = "contracts/contracts-edit.html"
    permission_required = "contracts.change_contract"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse("contracts:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Переопределяем метод для логирования успешного редактирования объекта.
        """
        response = super().form_valid(form)

        logger.info(
            f"Пользователь '{self.request.user.username}' обновил контракт: '{self.object}' (PK={self.object.pk})."
        )
        messages.success(self.request, f'Контракт "{self.object}" успешно обновлен.')
        return response


class ContractDeleteView(BaseObjectDeleteView):
    """Представление для "мягкого" удаления контракта."""

    model = Contract
    template_name = "contracts/contracts-delete.html"
    success_url = reverse_lazy("contracts:list")
    permission_required = "contracts.delete_contract"

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.

        Проверяем на защищенные связанные объекты перед "мягким" удалением.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().

        Raises:
            ProtectedError: Если найдены связанные объекты, прерывая удаление.
        """
        try:
            # Проверяем не связан ли контракт с клиентом и что клиент не "мягко удален".
            if (
                hasattr(self.object, "active_client")
                and self.object.active_client is not None
                and not self.object.active_client.is_deleted
            ):
                raise ProtectedError(
                    "Невозможно удалить контракт: он привязан к истории клиента.", {self.object.active_client}
                )

            # Если проверка пройдена, выполняем "мягкое" удаление.
            self.object.soft_delete()

            logger.info(
                f"Контракт '{self.object}' (PK={self.object.pk}) был 'мягко' удален (перемещен в архив) "
                f"пользователем '{self.request.user.username}'."
            )
            messages.success(self.request, f'Контракт "{self.object}" успешно перемещен в архив.')
            return HttpResponseRedirect(self.get_success_url())

        except ProtectedError as exc:
            # Если поймали ошибку, логируем и показываем пользователю сообщение.
            logger.warning(
                f"Заблокирована попытка удаления контракта '{self.object}' (PK={self.object.pk}) "
                f"пользователем '{self.request.user.username}', так как он защищен связанными объектами: {exc.protected_objects}"
            )
            messages.error(self.request, "Этот контракт нельзя удалить, так как он привязан к истории клиента.")

            # Возвращаем пользователя на детальную страницу.
            return HttpResponseRedirect(reverse("contracts:detail", kwargs={"pk": self.object.pk}))
