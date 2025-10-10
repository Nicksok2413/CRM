"""
Формы для приложения customers.
"""

from django import forms

from .models import ActiveClient
from apps.contracts.models import Contract


class ActiveClientForm(forms.ModelForm):
    """
    Форма для создания Активного клиента.
    """

    def __init__(self, *args, **kwargs):
        """
        Переопределяем конструктор для кастомизации поля 'contract'.
        """
        super().__init__(*args, **kwargs)

        # Фильтруем queryset для поля 'contract'.
        # Показываем только те контракты, которые еще не связаны
        # ни с одним активным клиентом (`active_client__isnull=True`).
        # Это предотвратит ошибки уникальности и улучшит UX.
        self.fields['contract'].queryset = Contract.objects.filter(active_client__isnull=True)

    class Meta:
        model = ActiveClient
        fields = ('potential_client', 'contract')

        # Прячем поле `potential_client`, так как оно будет
        # заполнено автоматически из URL и не должно редактироваться пользователем.
        widgets = {
            'potential_client': forms.HiddenInput(),
        }
