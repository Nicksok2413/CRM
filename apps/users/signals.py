"""
Сигналы для приложения users.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User


@receiver(post_save, sender=User)
def create_user_profile(sender: type[User], instance: User, created: bool, **kwargs) -> None:
    """
    Сигнал для автоматического создания Профиля при создании нового объекта User.

    Сигнал не будет срабатывать при загрузке данных из фикстур (raw=True).

    Args:
        sender: Модель-отправитель (User).
        instance: Экземпляр созданного пользователя.
        created: Флаг, указывающий, была ли запись создана.
    """

    # Проверяем, что это реальное создание объекта, а не загрузка из фикстур
    if created and not kwargs.get("raw", False):
        # Создаем профиль и связываем его с пользователем
        Profile.objects.create(user=instance)
