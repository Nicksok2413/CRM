"""
Настройки административной панели для приложения leads.
"""

from django.contrib import admin

from .models import PotentialClient


@admin.register(PotentialClient)
class PotentialClientAdmin(admin.ModelAdmin):
    """
    Административный класс для модели PotentialClient.
    """

    # Поля для отображения в списке всех лидах, включая связанную рекламную компанию.
    list_display = ("last_name", "first_name", "email", "phone", "ad_campaign")

    # Оптимизация запросов: при загрузке списка лидов
    # сразу загружаем связанные данные рекламных компаний одним SQL-запросом, избегая проблемы "N+1".
    # `list_select_related` заставляет Django использовать SQL JOIN, получая все данные за один запрос.
    list_select_related = ("ad_campaign",)

    # Поиск по всем контактным данным.
    search_fields = ("last_name", "first_name", "email", "phone")

    # Фильтры.
    # Фильтрация по ForeignKey (`ad_campaign`) создаст список всех рекламных компаний для выбора.
    list_filter = ("ad_campaign",)
