"""
Модели для приложения leads (потенциальные клиенты).
"""

from typing import TYPE_CHECKING, Any

import phonenumbers
from django.conf import settings
from django.db import models

from apps.advertisements.models import AdCampaign
from apps.common.models import BaseModel
from apps.common.validators import validate_international_phone_number, validate_letters_and_hyphens

# Этот блок импортируется только во время статической проверки типов.
# Он предотвращает ошибки циклического импорта во время выполнения.
if TYPE_CHECKING:
    from apps.customers.models import ActiveClient


class PotentialClient(BaseModel):
    """
    Модель для хранения данных о потенциальных клиентах (лидах) с жизненным циклом.
    """

    class Status(models.TextChoices):
        """
        Определяет возможные статусы жизненного цикла лида.
        `TextChoices` автоматически создает удобные для использования атрибуты
        (например, `PotentialClient.Status.NEW`).
        """

        NEW = "NEW", "Новый"
        IN_PROGRESS = "IN_PROGRESS", "В работе"
        CONVERTED = "CONVERTED", "Конвертирован"
        LOST = "LOST", "Потерян"

    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя",
        validators=[validate_letters_and_hyphens],  # Валидатор для имени
    )
    last_name = models.CharField(
        max_length=100,
        db_index=True,  # Для ускорения операций фильтрации и сортировки
        verbose_name="Фамилия",
        validators=[validate_letters_and_hyphens],  # Валидатор для фамилии
    )
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,  # Разрешаем хранить в БД NULL вместо пустой строки
        verbose_name="Телефон",
        validators=[validate_international_phone_number],  # Валидатор для телефона
        help_text="Введите номер в любом удобном формате, включая международный.",
    )

    status = models.CharField(
        max_length=20,
        db_index=True,  # Для ускорения операций фильтрации и сортировки
        choices=Status.choices,  # Используем определенные статусы
        default=Status.NEW,  # По умолчанию каждый новый лид - "Новый"
        verbose_name="Статус",
    )

    ad_campaign = models.ForeignKey(
        AdCampaign,
        on_delete=models.SET_NULL,  # Если кампания удалена, мы не хотим терять лида
        null=True,
        blank=True,
        related_name="leads",
        verbose_name="Рекламная кампания",
    )

    # Связь с пользователем (менеджером), который отвечает за этого лида.
    # on_delete=models.SET_NULL: если менеджер будет удален, лид не удалится,
    # а просто станет "бесхозным", и его сможет подобрать другой.
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Поле не обязательно, лид может быть "общим"
        related_name="managed_leads",  # Имя для обратной связи
        verbose_name="Ответственный менеджер",
    )

    # Явная аннотация для обратной связи.
    # PyCharm и mypy теперь знают, что у `PotentialClient` есть
    # менеджер `contracts_history`, который возвращает QuerySet объектов `ActiveClient`.
    contracts_history: models.Manager["ActiveClient"]

    @property
    def active_contract(self) -> "ActiveClient | None":
        """
        Возвращает текущую запись об активном контракте клиента (объект ActiveClient).

        Это свойство ищет в истории контрактов запись, которая не была "мягко удалена".
        Возвращает `None`, если активного контракта нет.
        """
        return self.contracts_history.filter(is_deleted=False).first()

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Переопределяем метод save для нормализации телефонного номера
        к международному стандарту E.164 (+375291234567).
        """
        if self.phone:
            try:
                # Парсим номер, используя регион по умолчанию из настроек
                parsed_phone = phonenumbers.parse(self.phone, settings.DEFAULT_PHONE_REGION)

                # Форматируем номер в стандарт E.164
                self.phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
            except phonenumbers.phonenumberutil.NumberParseException:
                # Этот блок, по идее, никогда не должен сработать,
                # так как валидатор уже проверил номер.
                # Но мы оставляем его для дополнительной надежности.
                pass  # Оставляем номер как есть, если что-то пошло не так

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = "Потенциальный клиент"
        verbose_name_plural = "Потенциальные клиенты"
        ordering = ["-created_at"]

        # Добавляем кастомные ограничения.
        constraints = [
            # Уникальность для email.
            # Поле `email` должно быть уникальным только для тех записей,
            # у которых is_deleted=False (т.е. тех, которые не были 'мягко удалены').
            models.UniqueConstraint(
                fields=["email"], condition=models.Q(is_deleted=False), name="unique_active_lead_email"
            ),
            # Уникальность для телефона.
            # Поле `phone` должно быть уникальным только для тех записей,
            # у которых is_deleted=False (т.е. тех, которые не были 'мягко удалены').
            # `nulls_not_distinct=True` (для PostgreSQL) может понадобиться, если
            # несколько записей с NULL в телефоне вызовут ошибку.
            # Но condition=Q(...) обычно решает эту проблему.
            models.UniqueConstraint(
                fields=["phone"], condition=models.Q(is_deleted=False), name="unique_active_lead_phone"
            ),
        ]
