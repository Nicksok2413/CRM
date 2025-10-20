"""
Сервисы (Services) для приложения customers.

Этот файл содержит функции, которые инкапсулируют сложные бизнес-операции,
связанные с клиентами. Они отделяют логику изменения данных от представлений (Views),
делая код чище, переиспользуемым и легко тестируемым.
"""

import logging
from typing import TYPE_CHECKING

from django.db import transaction

from apps.contracts.models import Contract
from apps.leads.models import PotentialClient

from .models import ActiveClient

# Этот блок импортируется только во время статической проверки типов.
# Он предотвращает ошибки циклического импорта во время выполнения.
if TYPE_CHECKING:
    from apps.users.models import User


# Получаем логгер для приложения.
logger = logging.getLogger("apps.customers")


class CustomerActivationError(Exception):
    """Кастомное исключение для обработки ошибок в процессе активации клиента."""

    pass


@transaction.atomic
def activate_customer(lead: PotentialClient, contract: Contract, user: "User") -> ActiveClient:
    """
    Сервисная функция для активации клиента (конвертации лида).

    Эта функция является "единой точкой правды" для бизнес-процесса активации.
    Она выполняется в атомарной транзакции, что гарантирует целостность данных:
    либо все операции выполнятся успешно, либо ни одна из них не будет применена.

    Логика работы:
    1. Проверяет бизнес-правила (статус лида, доступность контракта, соответствие услуги).
    2. Создает запись `ActiveClient`.
    3. Обновляет статус лида до `CONVERTED`.

    Args:
        lead: Экземпляр PotentialClient для активации.
        contract: Экземпляр Contract, который будет привязан к клиенту.
        user: Пользователь, выполняющий операцию (для логирования).

    Returns:
        Созданный экземпляр ActiveClient в случае успеха.

    Raises:
        CustomerActivationError: Если активация невозможна по какой-либо из бизнес-причин.
    """
    logger.debug(
        f"Запуск сервиса `activate_customer` для лида '{lead}' (PK={lead.pk}) "
        f"и контракта '{contract}' (PK={contract.pk}) пользователем '{user.username}'."
    )

    # 1. Валидация бизнес-правил.

    # Проверяем, не является ли лид уже активным клиентом.
    if lead.status == PotentialClient.Status.CONVERTED:
        raise CustomerActivationError(f'Клиент "{lead}" уже является активным.')

    # Проверяем, что контракт "свободен".
    if hasattr(contract, "active_client") and contract.active_client is not None:
        raise CustomerActivationError(f'Контракт "{contract}" уже используется другим клиентом.')

    # Проверяем, что услуга в контракте соответствует услуге, в которой был заинтересован лид.
    if lead.ad_campaign and lead.ad_campaign.service != contract.service:
        raise CustomerActivationError("Контракт не соответствует услуге, в которой был заинтересован клиент.")

    # 2. Выполнение операций с базой данных.

    # Создаем запись, связывающую лида и контракт.
    active_client = ActiveClient.objects.create(potential_client=lead, contract=contract)

    logger.info(
        f"Создана запись ActiveClient (PK={active_client.pk}) для лида '{lead}' (PK={lead.pk}) "
        f"с контрактом '{contract}' (PK={contract.pk})."
    )

    # Обновляем статус лида.
    lead.status = PotentialClient.Status.CONVERTED
    # Сохраняем только измененное поле для эффективности.
    lead.save(update_fields=["status"])

    logger.info(f"Статус лида '{lead}' (PK={lead.pk}) обновлен на 'CONVERTED'.")

    # Возвращаем результат.
    return active_client
