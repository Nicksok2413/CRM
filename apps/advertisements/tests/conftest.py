"""
Файл `conftest.py` для приложения `advertisements`.
"""

from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

from apps.advertisements.models import AdCampaign
from apps.common.management.commands.populate_db import (
    ActiveClientFactory,
    AdCampaignFactory,
    ContractFactory,
    PotentialClientFactory,
    ServiceFactory,
)
from apps.leads.models import PotentialClient


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


@pytest.fixture
def detailed_stats_data(db: None) -> dict:
    """
    Фикстура для создания сложного набора данных для тестирования
    детальной статистики `get_detailed_stats_for_campaign`.
    """
    # 1. Создаем услугу, она будет общей для всех сущностей в этом тесте
    service = ServiceFactory()

    # 2. Создаем кампанию, для которой будем считать статистику
    campaign = AdCampaignFactory(budget=Decimal("1000.00"), service=service)

    # 3. Создаем лидов, ЯВНО привязывая их к нашей кампании
    # --- 3.1. Лид "Активный" ---
    lead_active = PotentialClientFactory(ad_campaign=campaign, status=PotentialClient.Status.CONVERTED)
    # ЯВНО создаем контракт для нужной услуги
    contract_active = ContractFactory(service=service, amount=Decimal("1500.00"))
    ActiveClientFactory(potential_client=lead_active, contract=contract_active)

    # --- 3.2. Лид "Архивный" (по истории) ---
    lead_archived_history = PotentialClientFactory(ad_campaign=campaign, status=PotentialClient.Status.IN_PROGRESS)
    # ЯВНО создаем контракт для нужной услуги
    contract_archived = ContractFactory(service=service, amount=Decimal("500.00"))
    archived_ac = ActiveClientFactory(potential_client=lead_archived_history, contract=contract_archived)
    archived_ac.soft_delete()

    # --- 3.3. Лид "Архивный" (по статусу "Потерян") ---
    lead_archived_lost = PotentialClientFactory(ad_campaign=campaign, status=PotentialClient.Status.LOST)

    # --- 3.4. Лид "В работе" ---
    lead_in_work = PotentialClientFactory(ad_campaign=campaign, status=PotentialClient.Status.IN_PROGRESS)

    # Возвращаем словарь с ключевыми объектами.
    return {
        "campaign": campaign,
        "lead_active": lead_active,
        "lead_archived_history": lead_archived_history,
        "lead_archived_lost": lead_archived_lost,
        "lead_in_work": lead_in_work,
    }