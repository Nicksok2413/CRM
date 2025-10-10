"""
Формы для приложения contracts.
"""

from django import forms

from .models import Contract


class ContractForm(forms.ModelForm):
    """
    Форма для создания и редактирования Контрактов.
    """

    class Meta:
        model = Contract
        fields = ('name', 'service', 'document', 'amount', 'start_date', 'end_date')

        # Для полей дат добавляем виджеты с выбором даты, чтобы улучшить UX.
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
