"""
Unit-тесты для селекторов приложения `advertisements`.
"""

from decimal import Decimal

import pytest

from apps.advertisements.models import AdCampaign
from apps.advertisements.selectors import get_campaigns_with_stats, get_detailed_stats_for_campaign
from apps.common.management.commands.populate_db import (
    ActiveClientFactory,
    AdCampaignFactory,
    ContractFactory,
    PotentialClientFactory,
    ServiceFactory,
)


@pytest.mark.django_db
def test_get_campaigns_with_stats():
    """
    Тестирует селектор `get_campaigns_with_stats`.
    """
    # 1. ARRANGE (Подготовка)
    # Создаем услугу
    service = ServiceFactory()
    # Создаем кампанию, ЯВНО привязав ее к услуге
    campaign = AdCampaignFactory(budget=Decimal("1000.00"), service=service)

    # Создаем 3 лида, ЯВНО привязав их к кампании
    leads = PotentialClientFactory.create_batch(3, ad_campaign=campaign)

    # Активируем 2 из них. Для каждого ЯВНО создаем подходящий контракт
    contract1 = ContractFactory(service=service, amount=Decimal("750.00"))
    ActiveClientFactory(potential_client=leads[0], contract=contract1)

    contract2 = ContractFactory(service=service, amount=Decimal("1250.00"))
    ActiveClientFactory(potential_client=leads[1], contract=contract2)

    # "Мягко" удаляем третьего лида
    leads[2].soft_delete()

    # 2. ACT (Действие)
    stats = get_campaigns_with_stats().get(pk=campaign.pk)

    # 3. ASSERT (Проверка)
    assert stats.leads_count == 2
    assert stats.customers_count == 2
    assert stats.total_revenue == Decimal("2000.00")
    assert stats.profit == Decimal("200.00")


@pytest.mark.django_db
def test_get_detailed_stats_kpi_calculation(detailed_stats_data: dict):
    """
    Проверяет, что KPI в детальной статистике считаются по всем лидам.
    """
    # 1. ARRANGE
    campaign: AdCampaign = detailed_stats_data["campaign"]

    # 2. ACT
    stats = get_detailed_stats_for_campaign(campaign=campaign, status_filter="")

    # 3. ASSERT
    assert stats["total_leads"] == 4
    assert stats["total_active_clients"] == 1
    assert stats["total_revenue"] == Decimal("2000.00")
    assert stats["profit"] == 200.0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status_filter, expected_leads_keys, description",
    [
        (
            "",
            ["lead_active", "lead_archived_history", "lead_archived_lost", "lead_in_work"],
            "Без фильтра - показать всех",
        ),
        ("active", ["lead_active"], "Фильтр 'active' - показать только активного"),
        (
            "archived",
            ["lead_archived_history", "lead_archived_lost"],
            "Фильтр 'archived' - показать архивных",
        ),
        ("in_work", ["lead_in_work"], "Фильтр 'in_work' - показать тех, кто в работе"),
    ],
)
def test_get_detailed_stats_list_filtering(
    detailed_stats_data: dict, status_filter: str, expected_leads_keys: list[str], description: str
):
    """
    Параметризованный тест для проверки логики фильтрации списка `leads_list`.
    """
    # 1. ARRANGE
    campaign: AdCampaign = detailed_stats_data["campaign"]
    expected_ids = {detailed_stats_data[key].id for key in expected_leads_keys}

    # 2. ACT
    stats = get_detailed_stats_for_campaign(campaign=campaign, status_filter=status_filter)
    result_ids = {lead.id for lead in stats["leads_list"]}

    # 3. ASSERT
    assert result_ids == expected_ids, f"Ошибка в логике фильтрации для: {description}"