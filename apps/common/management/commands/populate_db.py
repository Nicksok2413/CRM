"""
Кастомная management-команда для наполнения базы данных
случайными, правдоподобными данными для тестирования и разработки.
"""

import random
from argparse import ArgumentParser
from typing import Any

import factory  # noqa
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker  # noqa

# Импортируем все модели
from apps.advertisements.models import AdCampaign
from apps.contracts.models import Contract
from apps.customers.models import ActiveClient
from apps.leads.models import PotentialClient
from apps.products.models import Service

# Инициализируем Faker для генерации данных
# 'ru_RU' для генерации русскоязычных имен, текстов и т.д.
faker = Faker("ru_RU")


# ======================================================================
# ФАБРИКИ ДЛЯ МОДЕЛЕЙ
# ======================================================================


class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Service

    name = factory.LazyFunction(lambda: faker.bs().capitalize())
    description = factory.LazyFunction(faker.text)
    cost = factory.LazyFunction(lambda: round(random.uniform(1000, 50000), 2))


class AdCampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdCampaign

    name = factory.LazyFunction(lambda: f"РК {faker.company()}")
    channel = factory.LazyFunction(lambda: random.choice(["Яндекс.Директ", "Google Ads", "VK", "Facebook"]))
    budget = factory.LazyFunction(lambda: round(random.uniform(50000, 500000), 2))


class PotentialClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PotentialClient

    first_name = factory.LazyFunction(faker.first_name)
    last_name = factory.LazyFunction(faker.last_name)
    email = factory.LazyFunction(faker.unique.email)
    phone = factory.LazyFunction(faker.phone_number)
    status = factory.LazyFunction(
        lambda: random.choice([PotentialClient.Status.NEW, PotentialClient.Status.IN_PROGRESS])
    )


class ContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contract

    name = factory.LazyFunction(lambda: f"Контракт №{random.randint(1000, 9999)}")
    amount = factory.LazyFunction(lambda: round(random.uniform(20000, 1000000), 2))
    start_date = factory.LazyFunction(faker.past_date)
    end_date = factory.LazyFunction(faker.future_date)


class ActiveClientFactory(factory.django.DjangoModelFactory):
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
        Добавляем аргумент командной строки для указания количества
        создаваемых записей.
        """
        parser.add_argument("--count", type=int, default=10, help="Количество создаваемых записей для каждой модели")

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Основной метод команды, который будет выполнен при ее запуске.
        """
        count = options["count"]
        self.stdout.write(self.style.SUCCESS(f"Начинаем наполнение базы данных. Будет создано по ~{count} записей..."))

        # Очищаем генератор уникальных значений Faker перед каждым запуском
        faker.unique.clear()

        # 1. Создаем услуги
        self.stdout.write("Создаем услуги...")
        # `create_batch` создает указанное количество объектов
        services = ServiceFactory.create_batch(count // 2 or 1)  # создаем в два раза меньше услуг

        # 2. Создаем Рекламные Кампании, привязывая их к Услугам
        self.stdout.write("Создаем рекламные кампании...")
        campaigns = []

        for _ in range(count):
            # Для каждой кампании выбираем случайную услугу
            service = random.choice(services)
            campaigns.append(AdCampaignFactory.create(service=service))

        # 3. Создаем потенциальных клиентов (лидов)
        self.stdout.write("Создаем потенциальных клиентов...")
        leads = []

        for _ in range(count * 3):  # Создадим в 3 раза больше лидов
            # Случайно выбираем одну из уже созданных кампаний
            campaign = random.choice(campaigns)
            leads.append(PotentialClientFactory.create(ad_campaign=campaign))

        # 4. Создадим некоторое количество "свободных" контрактов
        self.stdout.write('Создаем "свободные" контракты...')
        # Получим список всех услуг, чтобы создавать контракты для них
        all_services = Service.objects.all()
        free_contracts = []

        for _ in range(count):
            # Создаем контракт для случайной услуги
            service = random.choice(all_services)
            free_contracts.append(ContractFactory.create(service=service))

        # 5. "Активируем" часть клиентов
        self.stdout.write("Создаем активных клиентов и связанные с ними контракты...")
        # Перемешиваем список лидов
        random.shuffle(leads)

        # Делаем активной примерно треть от всех лидов
        num_active_clients = len(leads) // 3

        for lead in leads[:num_active_clients]:
            # Получаем услугу из кампании, с которой пришел лид
            service_for_contract = lead.ad_campaign.service
            # Создаем контракт для этой конкретной услуги
            contract = ContractFactory.create(service=service_for_contract)
            # Создаем запись об активном клиенте, связывая лида и контракт
            ActiveClientFactory.create(potential_client=lead, contract=contract)

        # 6. Создаем архивные контракты для некоторых из уже активных клиентов
        self.stdout.write("Создаем архивные (старые) контракты...")

        # Список активных клиентов
        active_leads_with_history = leads[:num_active_clients]

        # Перемешиваем список активных клиентов
        random.shuffle(active_leads_with_history)

        # Возьмем 1/5 от активных и добавим им еще по одному "старому" контракту
        for lead in active_leads_with_history[: len(active_leads_with_history) // 5]:
            # Получаем услугу из кампании, с которой пришел лид
            service_for_contract = lead.ad_campaign.service
            # Создаем контракт для этой конкретной услуги
            contract = ContractFactory.create(service=service_for_contract)
            # Создаем еще одну запись ActiveClient
            old_active_client_record = ActiveClientFactory.create(potential_client=lead, contract=contract)
            # И сразу же "мягко" ее удаляем, чтобы она стала архивной
            old_active_client_record.soft_delete()

        self.stdout.write(self.style.SUCCESS("База данных успешно наполнена!"))
