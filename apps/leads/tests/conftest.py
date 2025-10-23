import pytest
from django.contrib.auth.models import Group
from apps.users.models import User


@pytest.fixture
def manager1(db):
    user = User.objects.create_user(username="manager1", password="password")
    group, _ = Group.objects.get_or_create(name="Менеджер")
    user.groups.add(group)
    return user


@pytest.fixture
def manager2(db):
    user = User.objects.create_user(username="manager2", password="password")
    group, _ = Group.objects.get_or_create(name="Менеджер")
    user.groups.add(group)
    return user
