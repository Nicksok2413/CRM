"""
Сигналы для приложения users.
"""

import logging
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User

# Получаем логгер для приложения
logger = logging.getLogger("apps.users")


@receiver(post_save, sender=User)
def create_user_profile(sender: type[User], instance: User, created: bool, **kwargs: Any) -> None:
    """
    Сигнал для автоматического создания Профиля при создании нового объекта User.

    Сигнал не будет срабатывать при загрузке данных из фикстур (raw=True).

    Args:
        sender: Класс модели, отправившей сигнал (User).
        instance: Экземпляр созданного пользователя (User).
        created: Флаг, указывающий, была ли запись создана.
        **kwargs: Дополнительные аргументы.
    """

    # Проверяем, что это реальное создание объекта, а не загрузка из фикстур.
    if created and not kwargs.get("raw", False):
        try:
            # Создаем профиль и связываем его с пользователем.
            Profile.objects.create(user=instance)

            # Логируем успешное создание профиля.
            logger.info(
                f"Сигнал: Успешно создан профиль для нового пользователя '{instance.username}' (PK={instance.pk})."
            )
        except Exception as exc:
            # Логируем ошибку, если по какой-то причине профиль не создался.
            logger.error(
                f"Сигнал: Ошибка при создании профиля для пользователя '{instance.username}' (PK={instance.pk}). Ошибка: {exc}"
            )
