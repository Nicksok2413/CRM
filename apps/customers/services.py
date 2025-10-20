"""
Сервисный слой для приложения customers.

Инкапсулирует бизнес-логику, связанную с управлением клиентами,
делая ее независимой от представлений (Views) и переиспользуемой.
"""

import logging
from typing import Any

from django.db import transaction

from apps.contracts.models import Contract
from apps.leads.models import PotentialClient

from .models import ActiveClient

# Получаем экземпляр логгера для этого модуля
logger = logging.getLogger(__name__)


class CustomerActivationError(Exception):
    """Кастомное исключение для ошибок во время процесса активации клиента."""

    pass


@transaction.atomic
def activate_customer(*, lead: PotentialClient, contract: Contract, user: Any) -> ActiveClient:
    """
    Сервисная функция для активации клиента (конвертации лида).

    Инкапсулирует всю бизнес-логику процесса:
    1. Проверяет, можно ли активировать лида.
    2. Проверяет, подходит ли контракт для данной активации.
    3. Создает запись `ActiveClient` (связь лида и контракта).
    4. Обновляет статус лида до "Конвертирован".

    Args:
        lead: Экземпляр `PotentialClient` для активации.
        contract: Экземпляр `Contract`, который будет привязан к клиенту.
        user: Пользователь, выполняющий операцию (для логирования).

    Returns:
        Созданный экземпляр `ActiveClient`.

    Raises:
        CustomerActivationError: Если активация невозможна по бизнес-правилам.
    """
    logger.debug(f"Запуск сервиса активации для лида '{lead}' с контрактом '{contract}' пользователем '{user}'.")

    # === 1. Валидация бизнес-правил ===
    if lead.status == PotentialClient.Status.CONVERTED:
        logger.warning(f"Ошибка активации: лид '{lead}' уже имеет статус 'Конвертирован'.")
        raise CustomerActivationError(f'Клиент "{lead}" уже является активным.')

    if hasattr(contract, "active_client") and contract.active_client is not None:
        logger.warning(f"Ошибка активации: контракт '{contract}' уже используется.")
        raise CustomerActivationError(f'Контракт "{contract}" уже используется другим клиентом.')

    if lead.ad_campaign and lead.ad_campaign.service != contract.service:
        logger.warning(
            f"Ошибка активации: услуга контракта '{contract.service}' "
            f"не соответствует услуге кампании лида '{lead.ad_campaign.service}'."
        )
        raise CustomerActivationError("Контракт не соответствует услуге, в которой был заинтересован клиент.")

    # === 2. Выполнение операций в рамках транзакции ===
    # Создаем запись, связывающую клиента с контрактом.
    active_client = ActiveClient.objects.create(potential_client=lead, contract=contract)

    # Обновляем статус лида.
    lead.status = PotentialClient.Status.CONVERTED
    lead.save(update_fields=["status"])

    logger.info(
        f"Лид '{lead}' (PK={lead.pk}) успешно конвертирован. "
        f"Создана запись ActiveClient (PK={active_client.pk}) "
        f"с контрактом (PK={contract.pk}). Операцию выполнил: '{user}'."
    )

    # === 3. Возврат результата ===
    return active_client
