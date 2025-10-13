"""
Формы для приложения products.
"""

from django import forms

from .models import Service


class ServiceForm(forms.ModelForm):
    """
    Форма для создания и редактирования Услуг.

    Автоматически генерирует поля на основе модели Service и обеспечивает валидацию данных.
    """

    class Meta:
        model = Service
        fields = ("name", "description", "cost")
