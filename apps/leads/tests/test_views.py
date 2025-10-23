import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm
from apps.common.management.commands.populate_db import PotentialClientFactory


@pytest.mark.django_db
def test_lead_list_view_permissions(client, create_user_with_role):
    """
    Тестирует LeadListView на правильное отображение лидов в зависимости от прав.
    """
    # 1. ARRANGE
    # Создаем двух менеджеров
    manager1 = create_user_with_role(username="manager1", role_name="Менеджер")
    manager2 = create_user_with_role(username="manager2", role_name="Менеджер")

    # Создаем администратора с глобальными правами
    admin = create_user_with_role(username="admin_user", role_name="Администратор")
    # ... (здесь нужно выдать группе "Администратор" право 'leads.view_potentialclient')

    # Создаем 3 лида: два для manager1, один для manager2
    lead_m1_1 = PotentialClientFactory(manager=manager1)
    lead_m1_2 = PotentialClientFactory(manager=manager1)
    lead_m2_1 = PotentialClientFactory(manager=manager2)

    # Назначаем объектные права (хотя сигнал это уже делает, в тестах лучше делать явно)
    assign_perm("leads.view_potentialclient", manager1, lead_m1_1)
    assign_perm("leads.view_potentialclient", manager1, lead_m1_2)
    assign_perm("leads.view_potentialclient", manager2, lead_m2_1)

    url = reverse("leads:list")

    # 2. ACT & ASSERT для Менеджера 1
    client.login(username="manager1", password="password")
    response = client.get(url)

    assert response.status_code == 200
    # Менеджер 1 должен видеть только СВОИ 2 лида
    assert response.context["leads"].count() == 2
    assert lead_m1_1 in response.context["leads"]
    assert lead_m2_1 not in response.context["leads"]

    # 3. ACT & ASSERT для Менеджера 2
    client.login(username="manager2", password="password")
    response = client.get(url)

    assert response.status_code == 200
    # Менеджер 2 должен видеть только СВОЙ 1 лид
    assert response.context["leads"].count() == 1
    assert lead_m2_1 in response.context["leads"]
    assert lead_m1_1 not in response.context["leads"]

    # 4. ACT & ASSERT для Администратора
    # client.login(username="admin_user", password="password")
    # response = client.get(url)
    # assert response.status_code == 200
    # Администратор должен видеть ВСЕ 3 лида
    # assert response.context["leads"].count() == 3
