"""
Настройки административной панели для приложения products.
"""

from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Административный класс для модели Service.
    """
    # Поля для отображения в списке всех услуг.
    list_display = ('name', 'cost', 'created_at')

    # Поля, по которым будет работать поиск.
    search_fields = ('name', 'description')

    # Фильтры.
    # Добавляем боковую панель для фильтрации.
    # Для полей типа DateTimeField Django автоматически создает удобные фильтры:
    # "Сегодня", "Последние 7 дней" и т.д.
    list_filter = ('created_at',)
