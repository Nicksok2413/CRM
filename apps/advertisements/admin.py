"""
Настройки административной панели для приложения advertisements.
"""

from django.contrib import admin

from .models import AdCampaign


@admin.register(AdCampaign)
class AdCampaignAdmin(admin.ModelAdmin):
    """
    Административный класс для модели AdCampaign.
    """
    #Поля для отображения в списке всех рекламных кампании, включая связанную услугу.
    list_display = ('name', 'service', 'channel', 'budget')

    # Оптимизация запросов: при загрузке списка рекламных компаний
    # сразу загружаем связанные данные услуг одним SQL-запросом, избегая проблемы "N+1".
    # `list_select_related` заставляет Django использовать SQL JOIN, получая все данные за один запрос.
    list_select_related = ('service',)

    # Поля, по которым будет работать поиск.
    search_fields = ('name', 'channel')

    # Фильтры.
    # Фильтрация по ForeignKey (`service`) автоматически создаст список всех услуг для выбора.
    list_filter = ('channel', 'service')
