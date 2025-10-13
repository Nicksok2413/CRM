"""
Представления (Views) для приложения users.
"""
from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Импортируем модели для подсчета статистики
from apps.advertisements.models import AdCampaign
from apps.customers.models import ActiveClient
from apps.leads.models import PotentialClient
from apps.products.models import Service


class IndexView(LoginRequiredMixin, TemplateView):
    """
    Представление для отображения главной страницы (дашборда).

    - LoginRequiredMixin: Запрещает доступ неавторизованным пользователям.
    - TemplateView: Базовый класс для отображения статичного шаблона.
    """

    template_name = "users/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[Any, Any]:
        """
        Переопределяем метод для добавления кастомного контекста в шаблон.
        """
        # Получаем стандартный контекст от родительского класса
        context = super().get_context_data(**kwargs)

        # Добавляем в контекст статистику (количество записей в моделях)
        # Django ORM .count() - быстрый и эффективный способ выполнить SQL-запрос `SELECT COUNT(*) ...`
        context["products_count"] = Service.objects.count()
        context["advertisements_count"] = AdCampaign.objects.count()
        context["leads_count"] = PotentialClient.objects.count()
        context["customers_count"] = ActiveClient.objects.count()

        # Добавляем заголовок страницы
        context["title"] = "Главная страница"

        return context
