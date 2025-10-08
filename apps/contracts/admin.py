"""
Настройки административной панели для приложения contracts.
"""

from django.contrib import admin

from .models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """
    Административный класс для модели Contract.
    """
    # Поля для отображения в списке всех контрактов, включая связанную услугу.
    list_display = ('name', 'service', 'amount', 'start_date', 'end_date')

    # Оптимизация запросов: при загрузке списка контрактов
    # сразу загружаем связанные данные услуг одним SQL-запросом, избегая проблемы "N+1".
    # `list_select_related` заставляет Django использовать SQL JOIN, получая все данные за один запрос.
    list_select_related = ('service',)

    # Поиск по названию контракта.
    search_fields = ('name',)

    # Фильтры.
    # Фильтрация по ForeignKey (`service`) создаст список всех услуг для выбора.
    # Фильтры по датам заключения и окончания контрактов.
    list_filter = ('service', 'start_date', 'end_date')
