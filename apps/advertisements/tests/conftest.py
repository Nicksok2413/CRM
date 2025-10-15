import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from apps.advertisements.models import AdCampaign
from apps.common.management.commands.populate_db import (
    AdCampaignFactory,
    ContractFactory,
    PotentialClientFactory,
    ActiveClientFactory,
    ServiceFactory,
)


@pytest.fixture
def marketing_user(django_user_model):
    """
    Фикстура для создания пользователя с правами на просмотр статистики.
    """
    user = django_user_model.objects.create_user(username="marketing_user", password="password")
    content_type = ContentType.objects.get_for_model(AdCampaign)
    permission = Permission.objects.get(
        content_type=content_type,
        codename='view_adcampaign',
    )
    user.user_permissions.add(permission)
    return user


@pytest.fixture
def test_data():
    """
    Фикстура для создания изолированного набора тестовых данных.
    """
    # 1. Создаем одну общую услугу для всех
    service = ServiceFactory()

    # 2. Создаем две кампании, обе для одной и той же услуги
    target_campaign = AdCampaignFactory(budget=1000.00, name="Целевая кампания", service=service)
    other_campaign = AdCampaignFactory(budget=5000.00, name="Другая кампания", service=service)

    # 3. Создаем лидов для целевой кампании
    target_leads = PotentialClientFactory.create_batch(3, ad_campaign=target_campaign)

    # 4. Активируем 2 из 3 лидов для целевой кампании.
    # Создаем контракт для первого лида
    contract1 = ContractFactory.create(amount=750.00, service=service)
    ActiveClientFactory.create(potential_client=target_leads[0], contract=contract1)

    # Создаем контракт для второго лида
    contract2 = ContractFactory.create(amount=1250.00, service=service)
    ActiveClientFactory.create(potential_client=target_leads[1], contract=contract2)

    # 5. Создаем "шумовые" данные для другой кампании
    other_lead = PotentialClientFactory.create(ad_campaign=other_campaign)
    other_contract = ContractFactory.create(amount=9999.00, service=service)
    ActiveClientFactory.create(potential_client=other_lead, contract=other_contract)

    # Возвращаем ID целевой кампании, чтобы тест знал, что проверять
    return target_campaign.pk
