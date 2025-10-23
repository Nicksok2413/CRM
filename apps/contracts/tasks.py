import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
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

    # Определяем целевую дату.
    days_to_expire = settings.CONTRACT_EXPIRATION_NOTICE_DAYS
    target_date = timezone.now().date() + timedelta(days=days_to_expire)

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
        logger.info("Проверка истекающих контрактов: контрактов, истекающих через {days_to_expire} дней, не найдено.")
        return

    # Собираем контракты в словарь, где ключ - менеджер, а значение - список его контрактов.
    contracts_by_manager = {}

    for contract in expiring_contracts:
        # Убеждаемся, что у лида есть ответственный менеджер.
        manager = getattr(getattr(getattr(contract, "active_client", None), "potential_client", None), "manager", None)

        if manager and manager.email:
            # `setdefault` - удобный способ инициализировать список, если ключ еще не существует.
            contracts_by_manager.setdefault(manager, []).append(contract)

    # Отправляем сгруппированные письма.
    for manager, contracts in contracts_by_manager.items():
        subject = f"CRM: Напоминание о контрактах, истекающих {target_date.strftime('%d-%m-%Y')}"

        # Формируем красивый список контрактов для тела письма.
        contracts_list_str = "\n".join(
            [f"- {contract.name} (клиент: {contract.active_client.potential_client})" for contract in contracts]
        )

        # Формируем письмо.
        message = f"""
        Здравствуйте, {manager.first_name or manager.username}!

        Напоминаем, что у следующих ваших клиентов контракты истекают через 7 дней:

        {contracts_list_str}

        Пожалуйста, свяжитесь с ними для продления сотрудничества.
        """

        # Отправляем письмо.
        # Используем стандартную функцию Django для отправки почты.
        # Она будет использовать бэкенд, указанный в `settings.py` (консоль или реальный SMTP).
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[manager.email],
            fail_silently=False,  # Если отправка не удастся, Celery зафиксирует ошибку.
        )

        logger.info(f"Уведомление об истекающих контрактах ({len(contracts)} шт.) отправлено менеджеру '{manager}'.")

    logger.info(f"Задача `check_expiring_contracts` завершена. Отправлено уведомлений: {len(contracts_by_manager)}.")
