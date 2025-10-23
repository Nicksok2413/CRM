import pytest
from django.contrib.auth.models import Group

from apps.users.models import User


@pytest.fixture
def create_user_with_role():
    """
    Фабрика для создания пользователя и назначения ему роли (группы).
    """

    def _create_user(username: str, role_name: str) -> User:
        user = User.objects.create_user(username=username, password="password")
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(group)
        return user

    return _create_user
