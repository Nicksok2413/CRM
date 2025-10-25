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
from apps.leads.models import PotentialClient


@pytest.fixture
def detailed_stats_data() -> dict:
    """
    Фикстура для создания сложного набора данных для тестирования
    детальной статистики `get_detailed_stats_for_campaign`.
    """
    # 1. Создаем услугу, она будет общей для всех сущностей в этом тесте.
    service = ServiceFactory()

    # 2. Создаем кампанию, для которой будем считать статистику.
    campaign = AdCampaignFactory(budget=Decimal("1000.00"), service=service)

    # 3. Создаем лидов, привязывая их к кампании.

    # --- 3.1. Лид "активный" ---

    # Создаем лида.
    lead_active = PotentialClientFactory(ad_campaign=campaign, status=PotentialClient.Status.CONVERTED)

    # Создаем контракт для лида.
    contract_active = ContractFactory(service=service, amount=Decimal("1500.00"))

    # Активируем лида.
    ActiveClientFactory(potential_client=lead_active, contract=contract_active)

    # --- 3.2. Лид "архивный" (по истории) ---

    # Создаем лида.
    lead_archived_history = PotentialClientFactory(ad_campaign=campaign, status=PotentialClient.Status.IN_PROGRESS)

    # Создаем контракт для лида.
    contract_archived = ContractFactory(service=service, amount=Decimal("500.00"))

    # Активируем лида.
    archived_active_client = ActiveClientFactory(potential_client=lead_archived_history, contract=contract_archived)

    # "Мягко" удаляем.
    archived_active_client.soft_delete()

    # --- 3.3. Лид "архивный" (по статусу "Потерян") ---

    # Создаем лида.
    lead_archived_lost = PotentialClientFactory(ad_campaign=campaign, status=PotentialClient.Status.LOST)

    # --- 3.4. Лид "В работе" ---

    # Создаем лида.
    lead_in_work = PotentialClientFactory(ad_campaign=campaign, status=PotentialClient.Status.IN_PROGRESS)

    # Возвращаем словарь с ключевыми объектами.
    return {
        "campaign": campaign,
        "lead_active": lead_active,
        "lead_archived_history": lead_archived_history,
        "lead_archived_lost": lead_archived_lost,
        "lead_in_work": lead_in_work,
    }


@pytest.mark.django_db
def test_get_campaigns_with_stats_calculation():
    """
    Тестирует селектор `get_campaigns_with_stats` на корректность основных расчетов KPI.
    """
    # 1. ARRANGE (Подготовка данных).

    # Создаем услугу.
    service = ServiceFactory()

    # Создаем кампанию, привязав ее к услуге.
    campaign = AdCampaignFactory(budget=Decimal("1000.00"), service=service)

    # Создаем 3 лида, привязав их к кампании.
    leads = PotentialClientFactory.create_batch(3, ad_campaign=campaign)

    # Активируем 2 из них. Для каждого создаем подходящий контракт.
    contract1 = ContractFactory(service=service, amount=Decimal("750.00"))
    ActiveClientFactory(potential_client=leads[0], contract=contract1)

    contract2 = ContractFactory(service=service, amount=Decimal("1250.00"))
    ActiveClientFactory(potential_client=leads[1], contract=contract2)

    # 2. ACT (Выполнение действия).

    # Получаем статистику кампании.
    stats = get_campaigns_with_stats().get(pk=campaign.pk)

    # 3. ASSERT (Проверка результата).

    # Проверяем расчеты.
    assert stats.leads_count == 3
    assert stats.customers_count == 2
    # Используем Decimal для точного сравнения.
    assert stats.total_revenue == Decimal("2000.00")
    assert stats.profit == Decimal("200.00")


@pytest.mark.django_db
def test_get_detailed_stats_kpi_calculation(detailed_stats_data: dict):
    """
    Проверяет, что KPI в детальной статистике считаются по всем лидам.
    """
    # 1. ARRANGE (Подготовка данных).

    campaign: AdCampaign = detailed_stats_data["campaign"]

    # 2. ACT (Выполнение действия).

    # Получаем детальную статистику кампании.
    stats = get_detailed_stats_for_campaign(campaign=campaign, status_filter="")

    # 3. ASSERT (Проверка результата).

    # Проверяем расчеты.
    assert stats["total_leads"] == 4
    assert stats["total_active_clients"] == 1
    assert stats["total_revenue"] == Decimal("2000.00")
    assert stats["profit"] == 200.0


@pytest.mark.django_db
def test_get_campaigns_with_stats_handles_soft_deleted_leads():
    """
    Проверяет, что селектор `get_campaigns_with_stats` корректно
    игнорирует "мягко удаленных" лидов при подсчете `leads_count`.
    """
    # 1. ARRANGE (Подготовка данных).

    # Создаем услугу.
    service = ServiceFactory()

    # Создаем кампанию, привязав ее к услуге.
    campaign = AdCampaignFactory(service=service)

    # Создаем 3 лида, привязав их к кампании.
    leads = PotentialClientFactory.create_batch(3, ad_campaign=campaign)

    # Одного из них "мягко" удаляем.
    leads[1].soft_delete()

    # 2. ACT (Выполнение действия).

    # Получаем статистику кампании.
    stats = get_campaigns_with_stats().get(pk=campaign.pk)

    # 3. ASSERT (Проверка результата).

    # Ожидаем, что в подсчет попадут только 2 лида.
    assert stats.leads_count == 2


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
    # 1. ARRANGE (Подготовка данных).

    campaign: AdCampaign = detailed_stats_data["campaign"]
    expected_ids = {detailed_stats_data[key].id for key in expected_leads_keys}

    # 2. ACT (Выполнение действия).
    stats = get_detailed_stats_for_campaign(campaign=campaign, status_filter=status_filter)
    result_ids = {lead.id for lead in stats["leads_list"]}

    # 3. ASSERT (Проверка результата).

    assert result_ids == expected_ids, f"Ошибка в логике фильтрации для: {description}"