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
    Периодическая задача для поиска контрактов, истекающих через 7 дней,
    и отправки уведомлений ответственным менеджерам.
    """
    seven_days_from_now = timezone.now().date() + timedelta(days=7)

    expiring_contracts = Contract.objects.filter(
        end_date=seven_days_from_now, is_deleted=False, active_client__is_deleted=False
    ).select_related("active_client__potential_client__manager")

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
