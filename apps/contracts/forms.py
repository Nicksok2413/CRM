"""
Формы для приложения contracts.
"""
from typing import Any
from django import forms

from .models import Contract


class ContractForm(forms.ModelForm):
    """
    Форма для создания и редактирования Контрактов.
    """

    class Meta:
        model = Contract
        fields = ("name", "service", "document", "amount", "start_date", "end_date")

        # Для полей дат добавляем виджеты с выбором даты, чтобы улучшить UX.
        widgets = {
            "start_date": forms.DateInput(attrs={"placeholder": "Выберите дату...", "class": "datepicker"}),
            "end_date": forms.DateInput(attrs={"placeholder": "Выберите дату...", "class": "datepicker"}),
        }

    def clean(self) -> dict[str, Any]:
        """
        Переопределяем метод clean для добавления кастомной логики валидации,
        которая затрагивает несколько полей.
        """
        cleaned_data = super().clean()

        # Если родительский метод clean не вернул словарь (например, из-за ошибки
        # в одном из полей), мы прекращаем нашу собственную валидацию.
        if cleaned_data is None:
            # Возвращаем пустой словарь, так как метод должен вернуть dict.
            # Ошибки уже будут записаны в form.errors.
            return {}

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # Проверяем, что дата окончания не раньше даты начала
        if start_date and end_date and end_date < start_date:
            # Привязываем ошибку к конкретному полю, чтобы она отображалась рядом с ним
            self.add_error("end_date", "Дата окончания контракта не может быть раньше даты его начала.")

        return cleaned_data
