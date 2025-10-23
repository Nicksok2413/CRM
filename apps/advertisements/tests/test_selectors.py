import pytest
from decimal import Decimal
from apps.advertisements.selectors import get_campaigns_with_stats
from apps.common.management.commands.populate_db import (
    ServiceFactory, AdCampaignFactory, PotentialClientFactory, ActiveClientFactory
)


@pytest.mark.django_db
def test_get_campaigns_with_stats():
    """
    Тестирует селектор get_campaigns_with_stats.
    Проверяет корректность расчета KPI: leads_count, customers_count, total_revenue, profit.
    """
    # 1. ARRANGE (Подготовка данных)
    # Создаем кампанию с известным бюджетом
    campaign = AdCampaignFactory(budget=1000.00)

    # Создаем 3 лида для этой кампании
    leads = PotentialClientFactory.create_batch(3, ad_campaign=campaign)

    # Активируем 2 из них с контрактами на известные суммы
    ActiveClientFactory(potential_client=leads[0], contract__amount=750.00)
    ActiveClientFactory(potential_client=leads[1], contract__amount=1250.00)

    # "Мягко" удаляем одного из лидов, он не должен учитываться в leads_count
    leads[2].soft_delete()

    # 2. ACT (Выполнение действия)
    annotated_queryset = get_campaigns_with_stats()
    stats = annotated_queryset.get(pk=campaign.pk)

    # 3. ASSERT (Проверка результата)
    assert stats.leads_count == 2  # Должно быть 2, так как один лид удален
    assert stats.customers_count == 2
    assert stats.total_revenue == Decimal("2000.00")  # 750 + 1250
    assert stats.profit == Decimal("200.00")  # (2000 / 1000) * 100
