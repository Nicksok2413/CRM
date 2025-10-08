"""
Настройки административной панели для приложения customers.
"""

from django.contrib import admin

from .models import ActiveClient


@admin.register(ActiveClient)
class ActiveClientAdmin(admin.ModelAdmin):
    """
    Административный класс для модели ActiveClient.
    """
    # Отображаем обе связанные сущности: лиды и контракты.
    list_display = ('potential_client', 'contract')

    # Оптимизация запросов: при загрузке списка активных клиентов
    # сразу загружаем связанные данные лида и контрактов одним SQL-запросом, избегая проблемы "N+1".
    # `list_select_related` заставляет Django использовать SQL JOIN, получая все данные за один запрос.
    list_select_related = ('potential_client', 'contract')

    # Поиска по полям связанной модели лида.
    # Используем синтаксис `related_model__field_name`
    # для указания Django, что нужно искать в таблице `PotentialClient`.
    search_fields = ('potential_client__last_name', 'potential_client__first_name')
