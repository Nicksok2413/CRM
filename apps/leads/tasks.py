import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from apps.users.models import User

from .models import PotentialClient

# Получаем логгер для приложения.
logger = logging.getLogger("apps.leads")


# `@shared_task` делает эту функцию задачей Celery, которую можно вызвать асинхронно с помощью `.delay()`.
@shared_task
def notify_manager_about_new_lead(lead_id: int, manager_id: int) -> None:
    """
    Асинхронная задача для отправки email-уведомления менеджеру о его новом лиде.

    Args:
        lead_id: PK лида.
        manager_id: PK пользователя-менеджера.
    """
    try:
        # Получаем лида.
        lead = PotentialClient.objects.select_related("manager").get(pk=lead_id)

        # Получаем менеджера.
        manager = User.objects.get(pk=manager_id)

        # Проверяем что у менеджера есть email для отправки.
        if not manager.email:
            logger.warning(f"Не удалось отправить уведомление: у менеджера '{manager}' не указан email.")
            return

        # Формируем письмо.
        subject = f"CRM: Вам назначен новый лид - {lead}"
        message = f"""
        Здравствуйте, {manager.first_name or manager.username}!

        Вам был назначен новый потенциальный клиент:
        - ФИО: {lead}
        - Email: {lead.email}
        - Телефон: {lead.phone or "Не указан"}
        - Источник: {lead.ad_campaign.name if lead.ad_campaign else "Не указан"}

        Пожалуйста, свяжитесь с ним в ближайшее время.
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

        logger.info(f"Уведомление о новом лиде '{lead}' успешно отправлено менеджеру '{manager}'.")

    except (PotentialClient.DoesNotExist, User.DoesNotExist) as exc:
        # Если к моменту выполнения задачи лид или менеджер были удалены, логируем ошибку и прекращаем выполнение.
        logger.error(f"Ошибка при отправке уведомления: объект не найден. {exc}")
