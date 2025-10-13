"""
Тесты для представлений (views) приложения advertisements.
"""

import pytest  # noqa
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from apps.advertisements.models import AdCampaign
from apps.common.management.commands.populate_db import (
    ActiveClientFactory,
    AdCampaignFactory,
    PotentialClientFactory,
    ServiceFactory,
)


@pytest.mark.django_db
def test_ad_campaign_statistic_view(client, django_user_model):
    """
    Тестирует представление AdCampaignStatisticView.

    Проверяет:
    - Доступность страницы для авторизованного пользователя с правами.
    - Корректность расчета всех статистических показателей.
    """
    # =========================================================================
    # 1. ARRANGE (Подготовка данных)
    # =========================================================================

    # --- Создаем пользователя и даем ему права на просмотр кампаний ---
    user = django_user_model.objects.create_user(username="statistic_viewer", password="password")

    # Находим право 'view_adcampaign' в базе данных
    content_type = ContentType.objects.get_for_model(AdCampaign)
    permission = Permission.objects.get(
        content_type=content_type,
        codename="view_adcampaign",
    )
    user.user_permissions.add(permission)

    # Логиним пользователя в тестовый клиент
    client.login(username="statistic_viewer", password="password")

    # --- Создаем тестовые данные с помощью фабрик ---

    # Создаем одну услугу, которая будет общей для всего теста
    test_service = ServiceFactory()

    # Создадим две рекламные кампании (с известными бюджетами), чтобы тест был более надежным.
    # Первая - целевая.
    target_campaign = AdCampaignFactory(budget=1000.00, name="Целевая кампания", service=test_service)
    # Вторая - "шумовая", чтобы убедиться, что ее данные не влияют на результат.
    other_campaign = AdCampaignFactory(budget=5000.00, name="Другая кампания", service=test_service)

    # Создаем 3 лида для целевой кампании
    leads = PotentialClientFactory.create_batch(3, ad_campaign=target_campaign)

    # "Активируем" 2 из 3 лидов для целевой кампании, создав для них контракты с известной суммой
    # Фабрика сама создаст связанный контракт
    ActiveClientFactory(potential_client=leads[0], contract__amount=750.00, contract__service=target_campaign.service)
    ActiveClientFactory(potential_client=leads[1], contract__amount=1250.00, contract__service=target_campaign.service)

    # Создадим "шумового" активного клиента для другой кампании
    other_lead = PotentialClientFactory(ad_campaign=other_campaign)
    ActiveClientFactory(potential_client=other_lead, contract__amount=9999.00, contract__service=other_campaign.service)

    # =========================================================================
    # 2. ACT (Выполнение действия)
    # =========================================================================

    # Получаем URL страницы статистики
    url = reverse("ads:statistic")
    # Отправляем GET-запрос на этот URL
    response = client.get(url)

    # =========================================================================
    # 3. ASSERT (Проверка результата)
    # =========================================================================

    # --- Проверяем базовые вещи ---
    # Убеждаемся, что страница доступна (код ответа 200 OK)
    assert response.status_code == 200

    # В контексте должно быть 2 кампании
    all_campaign_stats = response.context["ads"]
    assert AdCampaign.objects.count() == 2
    assert len(all_campaign_stats) == 2

    # --- Проверяем расчеты ---
    # Находим в ответе статистику целевой кампании
    target_stats = None

    for stats in all_campaign_stats:
        if stats.pk == target_campaign.pk:
            target_stats = stats
            break

    # Убеждаемся, что мы нашли целевую кампанию в ответе
    assert target_stats is not None, "Целевая кампания не найдена в ответе View"

    # Проверяем количество лидов
    assert target_stats.leads_count == 3

    # Проверяем количество активных клиентов
    assert target_stats.customers_count == 2

    # Проверяем суммарный доход (750 + 1250)
    assert target_stats.total_revenue == 2000.00

    # Проверяем расчет рентабельности: (2000 / 1000) * 100
    assert target_stats.profit == 200.00
