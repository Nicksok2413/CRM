"""
Формы для приложения advertisements.
"""

from django import forms

from .models import AdCampaign


class AdCampaignForm(forms.ModelForm):
    """
    Форма для создания и редактирования Рекламных кампаний.
    """

    class Meta:
        model = AdCampaign
        fields = ("name", "service", "channel", "budget")


class LeadStatusFilterForm(forms.Form):
    """
    Форма для фильтрации по статусам лидов на странице детальной статистики по одной Рекламной кампании.
    """

    # Определяем возможные статусы
    STATUS_CHOICES = (
        ("", "Все статусы"),
        ("active", "Активный"),
        ("archived", "Архивный"),
        ("in_work", "В работе"),
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label="Фильтр по статусу")
