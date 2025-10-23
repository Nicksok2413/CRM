import logging

from celery import shared_task
from django.core.mail import send_mail

from apps.users.models import User

from .models import PotentialClient

# Получаем логгер для приложения.
logger = logging.getLogger("apps.leads")


@shared_task
def notify_manager_about_new_lead(lead_id: int, manager_id: int) -> None:
    """
    Асинхронная задача для отправки email-уведомления менеджеру о его новом лиде.

    Args:
        lead_id: PK лида.
        manager_id: PK пользователя-менеджера.
    """
    try:
        lead = PotentialClient.objects.get(pk=lead_id)
        manager = User.objects.get(pk=manager_id)

        if not manager.email:
            logger.warning(f"Не удалось отправить уведомление: у менеджера '{manager}' не указан email.")
            return

        subject = f"CRM: Вам назначен новый лид - {lead}"
        message = f"""
        Здравствуйте, {manager.first_name}!

        Вам был назначен новый потенциальный клиент:
        - ФИО: {lead}
        - Email: {lead.email}
        - Телефон: {lead.phone or "Не указан"}

        Пожалуйста, свяжитесь с ним в ближайшее время.
        Ссылка на карточку клиента: # (здесь будет ссылка на сайт)
        """
        send_mail(subject, message, "crm@example.com", [manager.email])
        logger.info(f"Уведомление о новом лиде '{lead}' успешно отправлено менеджеру '{manager}'.")
    except (PotentialClient.DoesNotExist, User.DoesNotExist) as exc:
        logger.error(f"Ошибка при отправке уведомления: объект не найден. {exc}")
