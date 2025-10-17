"""
Представления (Views) для приложения products.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import ProtectedError
from django.forms.models import BaseModelForm
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from .filters import ServiceFilter
from .forms import ServiceForm
from .models import Service


class ServiceListView(LoginRequiredMixin, PermissionRequiredMixin, FilterView):
    """Представление для отображения списка услуг с фильтрацией, пагинацией и сортировкой."""

    model = Service
    template_name = "products/products-list.html"
    context_object_name = "products"
    permission_required = "products.view_service"

    # Подключаем класс фильтра
    filterset_class = ServiceFilter
    # Устанавливаем пагинацию
    paginate_by = 20


class ServiceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Представление для детального просмотра услуги."""

    model = Service
    template_name = "products/products-detail.html"
    permission_required = "products.view_service"


class ServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Представление для создания новой услуги."""

    model = Service
    object: Service  # Явная аннотация для mypy
    form_class = ServiceForm
    template_name = "products/products-create.html"
    permission_required = "products.add_service"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного создания.
        """
        return reverse("products:detail", kwargs={"pk": self.object.pk})


class ServiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Представление для редактирования услуги."""

    model = Service
    object: Service  # Явная аннотация для mypy
    form_class = ServiceForm
    template_name = "products/products-edit.html"
    permission_required = "products.change_service"

    def get_success_url(self) -> str:
        """
        Переопределяем метод для перенаправления на детальную страницу
        объекта после успешного редактирования.
        """
        return reverse("products:detail", kwargs={"pk": self.object.pk})


class ServiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Представление для "мягкого" удаления услуги.
    """

    model = Service
    template_name = "products/products-delete.html"
    success_url = reverse_lazy("products:list")
    permission_required = "products.delete_service"

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        """
        Переопределяем метод form_valid для выполнения "мягкого" удаления.

        Проверяем на защищенные связанные объекты перед "мягким" удалением.
        Вместо реального удаления объекта из базы данных, вызываем кастомный метод soft_delete().

        Raises:
            ProtectedError: Если найдены связанные объекты, прерывая удаление.
        """
        try:
            # Ищем связанные кампании, у которых флаг `is_deleted` равен False.
            active_campaigns = self.object.ad_campaigns.filter(is_deleted=False)

            # Если queryset не пустой, значит, связанные объекты существуют.
            if active_campaigns.exists():
                raise ProtectedError(
                    "Невозможно удалить услугу, есть связанные активные кампании.",
                    active_campaigns
                )

            # Если проверка пройдена, выполняем "мягкое" удаление.
            self.object.soft_delete()
            messages.success(self.request, f'Услуга "{self.object}" успешно перемещена в архив.')
            return HttpResponseRedirect(self.get_success_url())

        except ProtectedError:
            # Если поймали ошибку, показываем пользователю сообщение.
            messages.error(self.request,
                           "Эту услугу нельзя удалить, так как она используется в активных рекламных кампаниях.")
            # Возвращаем пользователя на детальную страницу.
            return HttpResponseRedirect(reverse('products:detail', kwargs={'pk': self.object.pk}))
