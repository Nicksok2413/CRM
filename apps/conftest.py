"""
Общие фикстуры для всех тестов проекта.
"""

from typing import Callable

import pytest
from django.contrib.auth.models import Group
from django.test.client import Client

from apps.users.models import User


@pytest.fixture
def api_client() -> Client:
    """Простая фикстура, возвращающая стандартный тестовый клиент Django."""
    return Client()


@pytest.fixture
def create_user_with_role(db) -> Callable:
    """
    Фабрика для создания пользователя и добавления его в группу.
    Предполагается, что группы были созданы миграцией.
    """

    def _create_user(username: str, role_name: str) -> User:
        # Создаем пользователя.
        user = User.objects.create_user(username=username, password="password")

        # Находим группу.
        try:
            group = Group.objects.get(name=role_name)
        except Group.DoesNotExist:
            pytest.fail(f"Тест не может быть выполнен: группа '{role_name}' не была создана миграциями.")

        # 3. Добавляем пользователя в группу.
        user.groups.add(group)

        return user

    return _create_user
