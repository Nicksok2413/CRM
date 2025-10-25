import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from apps.common.management.commands.populate_db import PotentialClientFactory


@pytest.mark.django_db
def test_lead_list_view_object_permissions(api_client, create_user_with_role):
    """
    Тестирует, что менеджеры видят только свои лиды, а администраторы всех.
    """

    # 1. ARRANGE (Подготовка данных).

    # Создаем пользователей.
    manager1 = create_user_with_role(username="manager1", role_name="Менеджер")
    manager2 = create_user_with_role(username="manager2", role_name="Менеджер")

    # Создаем 3 лида: два для manager1, один для manager2.
    lead_m1_1 = PotentialClientFactory(manager=manager1)
    lead_m1_2 = PotentialClientFactory(manager=manager1)
    lead_m2_1 = PotentialClientFactory(manager=manager2)

    # Сигнал уже должен был назначить права, но для надежности теста назначим их явно.
    assign_perm("leads.view_potentialclient", manager1, lead_m1_1)
    assign_perm("leads.view_potentialclient", manager1, lead_m1_2)
    assign_perm("leads.view_potentialclient", manager2, lead_m2_1)

    url = reverse("leads:list")

    # 2. ACT & ASSERT для Менеджера 1.

    api_client.login(username="manager1", password="password")
    response = api_client.get(url)

    assert response.status_code == 200

    # queryset в контексте должен содержать ровно 2 лида.
    queryset = response.context["filter"].qs
    assert queryset.count() == 2
    assert lead_m1_1 in queryset
    assert lead_m1_2 in queryset
    assert lead_m2_1 not in queryset

    api_client.logout()

    # 3. ACT & ASSERT для Менеджера 2.

    api_client.login(username="manager2", password="password")
    response = api_client.get(url)

    assert response.status_code == 200

    # queryset в контексте должен содержать ровно 1 лид.
    queryset = response.context["filter"].qs
    assert queryset.count() == 1
    assert lead_m2_1 in queryset
    assert lead_m1_1 not in queryset


@pytest.mark.django_db
def test_lead_list_view_for_global_perms(api_client, create_user_with_role):
    """
    Тестирует, что пользователь с глобальными правами (например, Оператор)
    видит всех лидов.
    """
    # 1. ARRANGE

    # Создаем оператора. Его группа "Оператор" имеет глобальное право 'leads.view_potentialclient'.
    operator = create_user_with_role(username="operator", role_name="Оператор")

    # Создаем двух менеджеров для назначения лидам.
    manager1 = create_user_with_role(username="manager1", role_name="Менеджер")
    manager2 = create_user_with_role(username="manager2", role_name="Менеджер")

    # Создаем 3 лида для разных менеджеров.
    PotentialClientFactory(manager=manager1)
    PotentialClientFactory(manager=manager1)
    PotentialClientFactory(manager=manager2)

    # Логинимся как оператор.
    api_client.login(username="operator", password="password")

    # 2. ACT (Выполнение действия).

    url = reverse("leads:list")
    response = api_client.get(url)

    # 3. ASSERT (Проверка результата).

    assert response.status_code == 200

    # Оператор с глобальным правом должен видеть все 3 созданных лида.
    assert response.context["object_list"].count() == 3