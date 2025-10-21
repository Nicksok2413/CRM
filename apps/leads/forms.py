"""
Формы для приложения leads.
"""

import phonenumbers
from django import forms
from django.conf import settings

from apps.users.models import User

from .models import PotentialClient


class PotentialClientForm(forms.ModelForm):
    """
    Форма для создания и редактирования Потенциальных клиентов.
    Включает кастомную валидацию на уникальность email и телефона.
    """

    class Meta:
        model = PotentialClient
        fields = ("first_name", "last_name", "email", "phone", "ad_campaign", "manager")

    def clean_email(self) -> str:
        """
        Кастомный валидатор для поля email.
        Проверяет, не существует ли уже клиента или пользователя с таким email (без учета регистра).
        """
        # Получаем email из данных формы
        email: str = self.cleaned_data["email"]

        # 1. Создаем запрос для поиска дубликатов в лидах.
        # `iexact` обеспечивает регистронезависимый поиск.
        lead_query = PotentialClient.objects.filter(email__iexact=email)

        # Если редактируем существующего клиента (self.instance.pk не None),
        # мы должны исключить его самого из проверки.
        if self.instance and self.instance.pk:
            lead_query = lead_query.exclude(pk=self.instance.pk)

        # Если запрос нашел хотя бы одного другого клиента с таким email.
        if lead_query.exists():
            # Генерируем ошибку валидации, которая будет показана пользователю.
            raise forms.ValidationError("Клиент с таким email уже существует в системе.")

        # 2. Создаем запрос для поиска дубликатов в пользователях (сотрудниках).
        user_query = User.objects.filter(email__iexact=email)

        # Если запрос нашел хотя бы одного другого пользователя с таким email.
        if user_query.exists():
            # Получаем пользователя, чтобы дать более информативное сообщение.
            existing_user = user_query.first()

            # Добавляем эту строку. Она ничего не делает во время выполнения,
            # но для mypy это доказательство, что existing_user не None.
            assert existing_user is not None

            # Генерируем ошибку валидации, которая будет показана пользователю.
            raise forms.ValidationError(f"Этот email уже используется сотрудником: {existing_user.get_full_name()}.")

        # Если все в порядке, возвращаем очищенное значение.
        return email

    def clean_phone(self) -> str | None:
        """
        Кастомный валидатор для поля phone.
        Нормализует номер и проверяет его на уникальность.
        """
        phone = self.cleaned_data.get("phone")

        # Если поле телефона пустое, пропускаем валидацию.
        if not phone:
            return phone

        # 1. Нормализуем номер к стандарту E.164, как в модели.
        try:
            parsed_phone = phonenumbers.parse(phone, settings.DEFAULT_PHONE_REGION)
            normalized_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.phonenumberutil.NumberParseException:
            # Эта ошибка маловероятна, так как основной валидатор уже сработал,
            # но оставляем для надежности.
            raise forms.ValidationError("Не удалось распознать формат телефонного номера.")

        # 2. Проверяем на уникальность, используя нормализованный номер.
        query = PotentialClient.objects.filter(phone=normalized_phone)

        # Исключаем самого себя при редактировании.
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            # Генерируем ошибку валидации, которая будет показана пользователю.
            raise forms.ValidationError("Клиент с таким телефонным номером уже существует.")

        # Возвращаем нормализованный номер, чтобы он сохранился в БД.
        return normalized_phone
