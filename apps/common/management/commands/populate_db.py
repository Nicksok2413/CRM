"""
Кастомная management-команда для наполнения базы данных
случайными, правдоподобными данными для тестирования и разработки.

Использование:
    python manage.py populate_db
    python manage.py populate_db --count 50
"""

import random
from argparse import ArgumentParser
from typing import Any

import factory  # noqa
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker  # noqa

# Импортируем все модели
from apps.advertisements.models import AdCampaign
from apps.contracts.models import Contract
from apps.customers.models import ActiveClient
from apps.leads.models import PotentialClient
from apps.products.models import Service
from apps.users.models import User

# Инициализируем Faker для генерации данных.
# 'ru_RU' для генерации русскоязычных имен, текстов и т.д.
faker = Faker("ru_RU")


# ======================================================================
# ФАБРИКИ ДЛЯ МОДЕЛЕЙ
# ======================================================================


class ServiceFactory(factory.django.DjangoModelFactory):
    """Фабрика для модели Service."""

    class Meta:
        model = Service

    name = factory.LazyFunction(lambda: faker.bs().capitalize())
    description = factory.LazyFunction(faker.text)
    cost = factory.LazyFunction(lambda: round(random.uniform(1000, 50000), 2))


class AdCampaignFactory(factory.django.DjangoModelFactory):
    """Фабрика для модели AdCampaign."""

    class Meta:
        model = AdCampaign

    name = factory.LazyFunction(lambda: f"РК {faker.company()}")
    channel = factory.LazyFunction(lambda: random.choice(["Яндекс.Директ", "Google Ads", "VK", "Facebook"]))
    budget = factory.LazyFunction(lambda: round(random.uniform(50000, 500000), 2))


class PotentialClientFactory(factory.django.DjangoModelFactory):
    """Фабрика для модели PotentialClient."""

    class Meta:
        model = PotentialClient

    first_name = factory.LazyFunction(faker.first_name)
    last_name = factory.LazyFunction(faker.last_name)
    email = factory.LazyFunction(faker.unique.email)
    phone = factory.LazyFunction(faker.phone_number)
    status = factory.LazyFunction(
        lambda: random.choice([PotentialClient.Status.NEW, PotentialClient.Status.IN_PROGRESS])
    )
    manager = factory.LazyFunction(
        # Выбираем случайного пользователя (менеджера) из БД.
        lambda: User.objects.filter(groups__name="Менеджер").order_by("?").first()
    )


class ContractFactory(factory.django.DjangoModelFactory):
    """Фабрика для модели Contract."""

    class Meta:
        model = Contract

    name = factory.LazyFunction(lambda: f"Контракт №{random.randint(100, 999)}")
    amount = factory.LazyFunction(lambda: round(random.uniform(20000, 1000000), 2))
    start_date = factory.LazyFunction(faker.past_date)
    end_date = factory.LazyFunction(faker.future_date)


class ActiveClientFactory(factory.django.DjangoModelFactory):
    """Фабрика для модели ActiveClient."""

    class Meta:
        model = ActiveClient


# ======================================================================
# КЛАСС КОМАНДЫ
# ======================================================================


class Command(BaseCommand):
    """
    Django management-команда для наполнения БД.
    """

    help = "Наполняет базу данных тестовыми данными"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Добавляем аргумент командной строки `--count`
        для указания количества создаваемых записей.
        """
        parser.add_argument("--count", type=int, default=10, help="Количество создаваемых записей для каждой модели")

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Основной метод команды, который будет выполнен при запуске команды.
        Декоратор `@transaction.atomic` гарантирует, что операции
        будут выполнены в одной транзакции: либо все успешно, либо ничего.
        """
        count = options["count"]
        self.stdout.write(self.style.SUCCESS(f"Начинаем наполнение базы данных. Будет создано по ~{count} записей..."))

        # Очищаем генератор уникальных значений Faker перед каждым запуском.
        faker.unique.clear()

        # 1. Создаем трех пользователей (менеджеров).
        self.stdout.write('Создаем тестовых пользователей и добавляем их в группу "Менеджер"...')

        # Находим группу "Менеджер".
        # `get_or_create` безопасен, если группы еще нет.
        manager_group, _ = Group.objects.get_or_create(name="Менеджер")

        for idx in range(1, 4):
            # Получаем или создаем пользователя.
            user, created = User.objects.get_or_create(
                username=f"manager_{idx}", defaults={"first_name": f"Менеджер_{idx}"}
            )

            # Устанавливаем базовый пароль созданному пользователю.
            if created:
                user.set_password("password")
                user.save()

            # Добавляем пользователя в группу.
            user.groups.add(manager_group)

        # 2. Создаем услуги.
        self.stdout.write("Создаем услуги...")
        # `create_batch` создает указанное количество объектов.
        services = ServiceFactory.create_batch(count // 2 or 1)  # создаем в два раза меньше услуг

        # 3. Создаем Рекламные Кампании, привязывая их к Услугам.
        self.stdout.write("Создаем рекламные кампании...")
        campaigns = []

        for _ in range(count):
            # Для каждой кампании выбираем случайную услугу.
            service = random.choice(services)
            campaigns.append(AdCampaignFactory.create(service=service))

        # 4. Создаем потенциальных клиентов (лидов).
        self.stdout.write("Создаем потенциальных клиентов...")
        leads = []

        for _ in range(count * 3):  # Создадим в 3 раза больше лидов
            # Случайно выбираем одну из уже созданных кампаний.
            campaign = random.choice(campaigns)
            leads.append(PotentialClientFactory.create(ad_campaign=campaign))

        # 5. "Активируем" часть лидов.
        self.stdout.write("Создаем активных клиентов и связанные с ними контракты...")
        # Перемешиваем список лидов.
        random.shuffle(leads)

        # Делаем активной примерно треть от всех лидов.
        for lead in leads[: len(leads) // 3]:
            # Получаем услугу из кампании, с которой пришел лид.
            service_for_contract = lead.ad_campaign.service
            # Создаем контракт для этой конкретной услуги.
            contract = ContractFactory.create(service=service_for_contract)
            # Создаем запись об активном клиенте, связывая лида и контракт.
            ActiveClientFactory.create(potential_client=lead, contract=contract)

            # После создания ActiveClient, вручную обновляем статус лида.
            # Мы не можем положиться на сигналы, так как они могут не всегда
            # корректно срабатывать в контексте management-команд или массового создания.
            if lead.status != PotentialClient.Status.CONVERTED:
                # Меняем статус лида на "Конвертирован".
                lead.status = PotentialClient.Status.CONVERTED
                # Сохраняем только измененное поле для эффективности.
                lead.save(update_fields=["status"])

        # 6. Создадим некоторое количество "свободных" контрактов.
        # Они нужны для ручного тестирования активации через интерфейс.
        self.stdout.write('Создаем "свободные" контракты для ручного тестирования...')

        # Получим список всех услуг, чтобы создавать контракты для них.
        all_services = Service.objects.all()
        free_contracts = []

        for _ in range(count):
            # Создаем контракт для случайной услуги.
            service = random.choice(all_services)
            free_contracts.append(ContractFactory.create(service=service))
