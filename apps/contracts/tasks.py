import logging
from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from .models import Contract

# Получаем логгер для приложения.
logger = logging.getLogger("apps.contracts")


@shared_task
def check_expiring_contracts() -> None:
    """
    Периодическая задача для поиска контрактов и отправки уведомлений.

    - Запускается планировщиком Celery Beat по расписанию из `settings.py`.
    - Ищет все контракты, которые истекают ровно через 7 дней.
    - Группирует их по ответственным менеджерам и отправляет каждому
      менеджеру одно письмо со списком его истекающих контрактов.
    """

    logger.info("Запуск периодической задачи: `check_expiring_contracts`.")

    # Определяем целевую дату (ровно через неделю от сегодня).
    target_date = timezone.now().date() + timedelta(days=7)

    # Строим "тяжелый" запрос к БД.
    # Мы ищем только "активные" контракты, т.е. те, у которых:
    # - сам контракт не "мягко удален" (`is_deleted=False`).
    # - связанная запись `ActiveClient` не "мягко удалена".
    expiring_contracts = (
        Contract.objects.filter(end_date=target_date, is_deleted=False, active_client__is_deleted=False)
        .select_related(
            "active_client__potential_client__manager"
            # Оптимизация: одним запросом получаем контракт, клиента, лида и менеджера.
        )
        .order_by("active_client__potential_client__manager__id")  # Сортируем по менеджеру
    )

    if not expiring_contracts:
        logger.info("Проверка истекающих контрактов: контрактов для уведомления не найдено.")
        return

    for contract in expiring_contracts:
        manager = contract.active_client.potential_client.manager

        if manager and manager.email:
            subject = f"CRM: Контракт '{contract.name}' скоро истекает."
            message = f"Здравствуйте, {manager.first_name}!\n\nНапоминаем, что контракт №{contract.name} для клиента {contract.active_client.potential_client} истекает {contract.end_date.strftime('%d-%m-%Y')}."
            send_mail(subject, message, "crm@example.com", [manager.email])
            logger.info(f"Уведомление об истекающем контракте '{contract.name}' отправлено менеджеру '{manager}'.")
