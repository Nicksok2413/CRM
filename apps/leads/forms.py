"""
Формы для приложения leads.
"""

from django import forms

from .models import PotentialClient


class PotentialClientForm(forms.ModelForm):
    """
    Форма для создания и редактирования Потенциальных клиентов.
    """

    class Meta:
        model = PotentialClient
        fields = ('first_name', 'last_name', 'email', 'phone', 'ad_campaign')
