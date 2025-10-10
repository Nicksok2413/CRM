"""
Формы для приложения leads.
"""

import phonenumbers

from django import forms
from django.conf import settings

from .models import PotentialClient


class PotentialClientForm(forms.ModelForm):
    """
    Форма для создания и редактирования Потенциальных клиентов.
    Включает кастомную валидацию на уникальность email и телефона.
    """

    class Meta:
        model = PotentialClient
        fields = ('first_name', 'last_name', 'email', 'phone', 'ad_campaign')

    def clean_email(self) -> str:
        """
        Кастомный валидатор для поля email.
        Проверяет, не существует ли уже клиента с таким email (без учета регистра).
        """
        # Получаем email из данных формы
        email = self.cleaned_data.get('email')

        # Создаем запрос для поиска дубликатов.
        # `iexact` обеспечивает регистронезависимый поиск.
        query = PotentialClient.objects.filter(email__iexact=email)

        # Если мы редактируем существующего клиента (self.instance.pk не None),
        # мы должны исключить его самого из проверки.
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        # Если запрос нашел хотя бы одного другого клиента с таким email
        if query.exists():
            # Генерируем ошибку валидации, которая будет показана пользователю
            raise forms.ValidationError("Клиент с таким email уже существует в системе.")

        # Если все в порядке, возвращаем очищенное значение
        return email

    def clean_phone(self) -> str:
        """
        Кастомный валидатор для поля phone.
        Нормализует номер и проверяет его на уникальность.
        """
        phone = self.cleaned_data.get('phone')

        # Если поле телефона пустое, пропускаем валидацию
        if not phone:
            return phone

        # 1. Нормализуем номер к стандарту E.164, как в модели
        try:
            parsed_phone = phonenumbers.parse(phone, settings.DEFAULT_PHONE_REGION)
            normalized_phone = phonenumbers.format_number(
                parsed_phone,
                phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.phonenumberutil.NumberParseException:
            # Эта ошибка маловероятна, так как основной валидатор уже сработал,
            # но оставляем для надежности.
            raise forms.ValidationError("Не удалось распознать формат телефонного номера.")

        # 2. Проверяем на уникальность, используя нормализованный номер
        query = PotentialClient.objects.filter(phone=normalized_phone)

        # Исключаем самого себя при редактировании
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError("Клиент с таким телефонным номером уже существует.")

        # Возвращаем нормализованный номер, чтобы он сохранился в БД
        return normalized_phone