"""
Формы для приложения customers.
"""
from typing import Any
from django import forms
from django.db.models import Q

from apps.contracts.models import Contract

from .models import ActiveClient


class ActiveClientCreateForm(forms.ModelForm):
    """
    Форма для создания Активного клиента из Лида.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Переопределяем конструктор для кастомизации поля 'contract'.
        """
        super().__init__(*args, **kwargs)

        # Получаем поле, с которым будем работать
        contract_field = self.fields["contract"]

        # Проверяем, что это поле выбора модели (для безопасности и подсказки mypy)
        if isinstance(contract_field, forms.ModelChoiceField):
            # Теперь mypy знает, что у contract_field есть атрибут queryset

            # Фильтруем queryset.
            # Показываем только те контракты, которые еще не связаны
            # ни с одним активным клиентом (`active_client__isnull=True`).
            contract_field.queryset = Contract.objects.filter(active_client__isnull=True)


    class Meta:
        model = ActiveClient
        fields = ("potential_client", "contract")

        # Прячем поле `potential_client`, так как оно будет
        # заполнено автоматически из URL и не должно редактироваться пользователем.
        widgets = {
            "potential_client": forms.HiddenInput(),
        }


class ActiveClientUpdateForm(forms.ModelForm):
    """
    Форма для редактирования Активного клиента.

    Основной сценарий использования: смена контракта для существующего активного клиента.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Переопределяем конструктор для кастомизации поля 'contract'.
        """
        super().__init__(*args, **kwargs)

        # `instance` - это редактируемый объект ActiveClient, который
        # Django передает в форму при ее инициализации в UpdateView.
        instance = kwargs.get("instance")

        # Получаем поле, с которым будем работать
        contract_field = self.fields["contract"]

        # Убеждаемся, что мы работаем с существующим объектом (а не создаем новый).
        # Проверяем, что у нас есть instance и что поле - нужного типа.
        if instance and instance.pk and isinstance(contract_field, forms.ModelChoiceField):
            # Модифицируем queryset.
            # Нам нужно, чтобы в выпадающем списке были:
            # 1. Все "свободные" контракты (active_client__isnull=True).
            # 2. Текущий контракт, который уже присвоен этому клиенту (pk=instance.contract.pk).
            #    Это необходимо, чтобы текущее значение отображалось в форме корректно.
            # `Q` используем для создания сложного SQL-запроса с логикой "ИЛИ" (`|`).
            contract_field.queryset = Contract.objects.filter(
                Q(active_client__isnull=True) | Q(pk=instance.contract.pk)
            )

    class Meta:
        model = ActiveClient
        # При редактировании Активного клиента, единственное, что имеет смысл менять - это его контракт.
        # Данные самого человека (ФИО, email) редактируются в его карточке Лида.
        fields = ("contract",)
