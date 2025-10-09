"""
Кастомная management-команда для наполнения базы данных
случайными, правдоподобными данными для тестирования и разработки.
"""

import random
from typing import Any

import factory
from faker import Faker

from django.core.management.base import BaseCommand
from django.db import transaction

# Импортируем все модели
from apps.advertisements.models import AdCampaign
from apps.contracts.models import Contract
from apps.customers.models import ActiveClient
from apps.leads.models import PotentialClient
from apps.products.models import Service

# Инициализируем Faker для генерации данных
# 'ru_RU' для генерации русскоязычных имен, текстов и т.д.
faker = Faker('ru_RU')


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
    # Автоматически создаст связанную Услугу с помощью ServiceFactory
    service = factory.SubFactory(ServiceFactory)
    channel = factory.LazyFunction(lambda: random.choice(['Яндекс.Директ', 'Google Ads', 'VK', 'Facebook']))
    budget = factory.LazyFunction(lambda: round(random.uniform(50000, 500000), 2))


class PotentialClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PotentialClient

    first_name = factory.LazyFunction(faker.first_name)
    last_name = factory.LazyFunction(faker.last_name)
    email = factory.LazyFunction(faker.unique.email)
    phone = factory.LazyFunction(faker.phone_number)
    # Автоматически создаст связанную Рекламную кампанию
    ad_campaign = factory.SubFactory(AdCampaignFactory)


class ContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contract

    name = factory.LazyAttribute(lambda o: f"Контракт №{random.randint(100, 999)} на {o.service.name}")
    # Указываем, что услуга будет передана при создании
    service = factory.SubFactory(ServiceFactory)
    amount = factory.LazyFunction(lambda: round(random.uniform(20000, 1000000), 2))
    start_date = factory.LazyFunction(faker.past_date)
    end_date = factory.LazyFunction(faker.future_date)


class ActiveClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActiveClient

    # Связь с лидом будет установлена при создании
    potential_client = factory.SubFactory(PotentialClientFactory)

    # Создаем контракт, который логически связан с лидом
    # Услуга в контракте должна быть той же, что и в рекламной кампании лида
    contract = factory.LazyAttribute(
        lambda o: ContractFactory(service=o.potential_client.ad_campaign.service)
    )


# ======================================================================
# КЛАСС КОМАНДЫ
# ======================================================================

class Command(BaseCommand):
    """
    Django management-команда для наполнения БД.
    """
    help = 'Наполняет базу данных тестовыми данными'

    def add_arguments(self, parser):
        """
        Добавляем аргумент командной строки для указания количества
        создаваемых записей.
        """
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Количество создаваемых записей для каждой модели'
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Основной метод команды, который будет выполнен при ее запуске.
        """
        count = options['count']
        self.stdout.write(self.style.SUCCESS(f'Начинаем наполнение базы данных. Будет создано по ~{count} записей...'))

        # ======================================================================
        # 1. Создаем Услуги и Рекламные Кампании
        # ======================================================================
        self.stdout.write('Создаем Услуги и Рекламные кампании...')
        # `create_batch` создает указанное количество объектов
        campaigns = AdCampaignFactory.create_batch(count)

        # ======================================================================
        # 2. Создаем Потенциальных клиентов (Лидов)
        # ======================================================================
        self.stdout.write('Создаем Потенциальных клиентов...')
        leads = []

        for _ in range(count * 3):  # Создадим в 3 раза больше лидов
            # Случайно выбираем одну из уже созданных кампаний
            campaign = random.choice(campaigns)
            leads.append(PotentialClientFactory(ad_campaign=campaign))

        # ======================================================================
        # 3. "Активируем" часть клиентов
        # ======================================================================
        self.stdout.write('Создаем Активных клиентов и Контракты...')
        # Перемешиваем список лидов
        random.shuffle(leads)
        # Делаем активной примерно треть от всех лидов
        num_active_clients = len(leads) // 3

        for lead in leads[:num_active_clients]:
            # Создаем Активного клиента, фабрика сама создаст связанный Контракт
            ActiveClientFactory(potential_client=lead)

        self.stdout.write(self.style.SUCCESS('База данных успешно наполнена!'))
