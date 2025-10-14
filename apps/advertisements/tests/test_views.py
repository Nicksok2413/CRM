import pytest
from django.urls import reverse
from decimal import Decimal


# Нам больше не нужны импорты фабрик и моделей прав здесь
# Все это теперь инкапсулировано в фикстурах


@pytest.mark.django_db
def test_ad_campaign_statistic_view(client, marketing_user, test_data):
    """
    Тестирует AdCampaignStatisticView, используя данные из фикстур.
    """
    # =========================================================================
    # 1. ARRANGE (Подготовка данных)
    # =========================================================================

    # Логиним пользователя, созданного в фикстуре `marketing_user`
    client.login(username="marketing_user", password="password")

    # Получаем ID нашей целевой кампании из фикстуры `test_data`
    # Сами данные уже созданы в базе данных к этому моменту.
    target_campaign_pk = test_data

    # =========================================================================
    # 2. ACT (Выполнение действия)
    # =========================================================================

    url = reverse('ads:statistic')
    response = client.get(url)

    # =========================================================================
    # 3. ASSERT (Проверка результата)
    # =========================================================================

    assert response.status_code == 200

    all_campaign_stats = response.context['ads']

    # Находим статистику целевой кампании
    target_stats = None

    for stats in all_campaign_stats:
        if stats.pk == target_campaign_pk:
            target_stats = stats
            break

    assert target_stats is not None, "Целевая кампания не найдена в ответе View"

    # Проверяем расчеты
    assert target_stats.leads_count == 3
    assert target_stats.customers_count == 2
    # Используем Decimal для точного сравнения
    assert target_stats.total_revenue == Decimal("2000.00")
    assert target_stats.profit == Decimal("200.00")