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
