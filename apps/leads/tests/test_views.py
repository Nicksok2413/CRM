import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from apps.common.management.commands.populate_db import PotentialClientFactory


@pytest.mark.django_db
def test_lead_list_view_object_permissions(client, manager1, manager2):
    """
    Тестирует, что менеджеры видят только свои лиды.
    """
    # 1. ARRANGE
    # Создаем 3 лида: два для manager1, один для manager2
    lead_m1_1 = PotentialClientFactory(manager=manager1)
    lead_m1_2 = PotentialClientFactory(manager=manager1)
    lead_m2_1 = PotentialClientFactory(manager=manager2)

    # Сигнал уже должен был назначить права, но для надежности теста назначим их явно
    assign_perm("leads.view_potentialclient", manager1, lead_m1_1)
    assign_perm("leads.view_potentialclient", manager1, lead_m1_2)
    assign_perm("leads.view_potentialclient", manager2, lead_m2_1)

    url = reverse("leads:list")

    # 2. ACT & ASSERT для Менеджера 1
    client.login(username="manager1", password="password")
    response = client.get(url)

    assert response.status_code == 200
    # queryset в контексте должен содержать ровно 2 лида
    queryset = response.context["filter"].qs
    assert queryset.count() == 2
    assert lead_m1_1 in queryset
    assert lead_m2_1 not in queryset

    # 3. ACT & ASSERT для Менеджера 2
    client.login(username="manager2", password="password")
    response = client.get(url)

    assert response.status_code == 200
    # queryset в контексте должен содержать ровно 1 лид
    queryset = response.context["filter"].qs
    assert queryset.count() == 1
    assert lead_m2_1 in queryset
    assert lead_m1_1 not in queryset
