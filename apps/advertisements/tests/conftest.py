"""
Фикстуры для тестов приложения `advertisements`.
"""

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

from apps.advertisements.models import AdCampaign


@pytest.fixture
def marketing_user(db, django_user_model) -> User:
    """
    Фикстура для создания пользователя с ролью 'Маркетолог'.
    Права группы должны быть созданы миграцией.
    """
    # 1. Используем `django_user_model` для безопасного создания пользователя.
    user = django_user_model.objects.create_user(
        username="marketing_user",
        password="password"
    )

    # 2. Находим или создаем группу.
    group, _ = Group.objects.get_or_create(name="Маркетолог")

    # 3. Назначаем права группе (это делает фикстуру самодостаточной).
    content_type = ContentType.objects.get_for_model(AdCampaign)
    # Получаем все права для модели AdCampaign
    permissions = Permission.objects.filter(content_type=content_type)
    group.permissions.add(*permissions)

    # 4. Добавляем пользователя в группу.
    user.groups.add(group)

    return user
