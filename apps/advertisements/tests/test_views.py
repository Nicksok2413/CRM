import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

# Импортируем модели напрямую, а не фабрики
from apps.advertisements.models import AdCampaign
from apps.contracts.models import Contract
from apps.customers.models import ActiveClient
from apps.leads.models import PotentialClient
from apps.products.models import Service


@pytest.mark.django_db
def test_ad_campaign_statistic_view_manual_data(client, django_user_model):
    """
    Тестирует AdCampaignStatisticView с полностью контролируемыми,
    созданными вручную данными для максимальной надежности.
    """
    # =========================================================================
    # 1. ARRANGE (Подготовка данных)
    # =========================================================================

    # --- Создаем пользователя и права ---
    user = django_user_model.objects.create_user(username="statistic_viewer", password="password")
    content_type = ContentType.objects.get_for_model(AdCampaign)
    permission = Permission.objects.get(content_type=content_type, codename="view_adcampaign")
    user.user_permissions.add(permission)
    client.login(username="statistic_viewer", password="password")

    # --- Создаем сущности шаг за шагом ---

    # 1. Создаем услугу
    service = Service.objects.create(name="Тестовая услуга", cost=100)

    # 2. Создаем две кампании для этой услуги
    target_campaign = AdCampaign.objects.create(name="Целевая кампания", service=service, budget=1000.00)
    other_campaign = AdCampaign.objects.create(name="Другая кампания", service=service, budget=5000.00)

    # 3. Создаем 3 лида для ЦЕЛЕВОЙ кампании
    lead1 = PotentialClient.objects.create(
        first_name="Иван", last_name="Тестовый1", email="t1@test.com", ad_campaign=target_campaign
    )
    lead2 = PotentialClient.objects.create(
        first_name="Петр", last_name="Тестовый2", email="t2@test.com", ad_campaign=target_campaign
    )
    # lead3 = PotentialClient.objects.create(
    #     first_name="Сидор", last_name="Тестовый3", email="t3@test.com", ad_campaign=target_campaign
    # )

    # 4. Создаем 2 контракта для этой же услуги
    contract1 = Contract.objects.create(
        name="Контракт 1", service=service, amount=750.00, start_date="2025-01-01", end_date="2025-12-31"
    )
    contract2 = Contract.objects.create(
        name="Контракт 2", service=service, amount=1250.00, start_date="2025-01-01", end_date="2025-12-31"
    )

    # 5. "Активируем" 2 лида, связывая их с контрактами
    ActiveClient.objects.create(potential_client=lead1, contract=contract1)
    ActiveClient.objects.create(potential_client=lead2, contract=contract2)

    # 6. Создаем "шумовые" данные для другой кампании
    other_lead = PotentialClient.objects.create(
        first_name="Шум", last_name="Шумов", email="noise@test.com", ad_campaign=other_campaign
    )
    other_contract = Contract.objects.create(
        name="Контракт шум", service=service, amount=9999.00, start_date="2025-01-01", end_date="2025-12-31"
    )
    ActiveClient.objects.create(potential_client=other_lead, contract=other_contract)

    # =========================================================================
    # 2. ACT (Выполнение действия)
    # =========================================================================

    url = reverse("ads:statistic")
    response = client.get(url)

    # =========================================================================
    # 3. ASSERT (Проверка результата)
    # =========================================================================

    assert response.status_code == 200

    all_campaign_stats = response.context["ads"]
    assert len(all_campaign_stats) == 2

    # Находим статистику для ЦЕЛЕВОЙ кампании
    target_stats = [stats for stats in all_campaign_stats if stats.pk == target_campaign.pk][0]
    # Находим статистику для ДРУГОЙ кампании
    other_stats = [stats for stats in all_campaign_stats if stats.pk == other_campaign.pk][0]

    # --- Проверяем ЦЕЛЕВУЮ кампанию ---
    assert target_stats.leads_count == 3, "Неверное кол-во лидов у целевой кампании"
    assert target_stats.customers_count == 2, "Неверное кол-во активных клиентов у целевой кампании"
    assert target_stats.total_revenue == 2000.00, "Неверный доход у целевой кампании"
    assert target_stats.profit == 200.00, "Неверная рентабельность у целевой кампании"

    # --- Проверяем ДРУГУЮ кампанию, чтобы убедиться в изоляции ---
    assert other_stats.leads_count == 1, "Неверное кол-во лидов у другой кампании"
    assert other_stats.customers_count == 1, "Неверное кол-во активных клиентов у другой кампании"
    assert other_stats.total_revenue == 9999.00, "Неверный доход у другой кампании"
