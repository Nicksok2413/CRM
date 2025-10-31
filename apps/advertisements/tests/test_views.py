import pytest
from django.urls import reverse
from decimal import Decimal

from apps.common.management.commands.populate_db import (
    AdCampaignFactory,
    ContractFactory,
    PotentialClientFactory,
    ActiveClientFactory,
    ServiceFactory,
)


@pytest.fixture
def statistic_view_data(db):
    """
    Фикстура для создания изолированного набора тестовых данных.
    """
    # 1. Создаем одну общую услугу для всех.
    service = ServiceFactory()

    # 2. Создаем две кампании, обе для одной и той же услуги.
    target_campaign = AdCampaignFactory(budget=1000.00, name="Целевая кампания", service=service)
    other_campaign = AdCampaignFactory(budget=5000.00, name="Другая кампания", service=service)

    # 3. Создаем лидов для целевой кампании.
    target_leads = PotentialClientFactory.create_batch(3, ad_campaign=target_campaign)

    # 4. Активируем 2 из 3 лидов для целевой кампании.
    # Создаем контракт для первого лида.
    contract1 = ContractFactory.create(amount=750.00, service=service)
    ActiveClientFactory.create(potential_client=target_leads[0], contract=contract1)

    # Создаем контракт для второго лида.
    contract2 = ContractFactory.create(amount=1250.00, service=service)
    ActiveClientFactory.create(potential_client=target_leads[1], contract=contract2)

    # 5. Создаем "шумовые" данные для другой кампании.
    other_lead = PotentialClientFactory.create(ad_campaign=other_campaign)
    other_contract = ContractFactory.create(amount=9999.00, service=service)
    ActiveClientFactory.create(potential_client=other_lead, contract=other_contract)

    # Возвращаем ID целевой кампании, чтобы тест знал, что проверять.
    return target_campaign.pk


@pytest.mark.django_db
def test_ad_campaign_statistic_view(api_client, create_user_with_role, statistic_view_data):
    """
    Тестирует AdCampaignStatisticView, используя данные из фикстур.
    """

    # 1. ARRANGE (Подготовка данных).

    # Создаем пользователя и добавляем его в группу "Маркетолог".
    marketer = create_user_with_role(username="marketer", role_name="Маркетолог")
    
    api_client.force_login(marketer)

    # Получаем ID нашей целевой кампании из фикстуры `statistic_view_data`.
    target_campaign_pk = statistic_view_data

    # 2. ACT (Выполнение действия).

    url = reverse('ads:statistic')
    response = api_client.get(url)

    # 3. ASSERT (Проверка результата).

    # Получаем статистику всех кампаний.
    all_campaign_stats = response.context['ads']

    # Находим статистику целевой кампании.
    target_stats = None

    for stats in all_campaign_stats:
        if stats.pk == target_campaign_pk:
            target_stats = stats
            break

    assert target_stats is not None, "Целевая кампания не найдена в ответе View"

    # Проверяем расчеты.
    assert target_stats.leads_count == 3
    assert target_stats.customers_count == 2
    # Используем Decimal для точного сравнения.
    assert target_stats.total_revenue == Decimal("2000.00")
    assert target_stats.profit == Decimal("200.00")
