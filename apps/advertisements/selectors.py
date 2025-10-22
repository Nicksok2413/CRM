"""
Селекторы (Selectors) для приложения advertisements.

Этот файл содержит функции, которые инкапсулируют сложную логику извлечения данных из базы данных.
Они отделяют бизнес-логику запросов от представлений (Views), делая код более чистым,
переиспользуемым и легко тестируемым.
"""

from decimal import Decimal
from typing import TypedDict

from django.db.models import Case, Count, DecimalField, ExpressionWrapper, F, Prefetch, Q, QuerySet, Sum, When
from django.db.models.functions import Coalesce

from apps.customers.models import ActiveClient
from apps.leads.models import PotentialClient

from .models import AdCampaign


def get_campaigns_with_stats() -> QuerySet[AdCampaign]:
    """
    Возвращает queryset рекламных кампаний, аннотированный статистикой.

    Аннотации включают:
    - leads_count: Количество активных лидов.
    - customers_count: Количество конвертированных клиентов.
    - total_revenue: Общий доход от контрактов.
    - profit: Рентабельность (ROI) в процентах.

    Returns:
        QuerySet[AdCampaign]: QuerySet с добавленными статистическими полями.
    """
    return AdCampaign.objects.annotate(
        # Количество уникальных лидов для каждой кампании, которые не были "мягко" удалены.
        leads_count=Count("leads", filter=Q(leads__is_deleted=False), distinct=True),
        # Количество активных клиентов для каждой кампании, которые не были "мягко" удалены.
        customers_count=Count(
            "leads__contracts_history", filter=Q(leads__contracts_history__is_deleted=False), distinct=True
        ),
        # Суммарный доход от контрактов активных клиентов.
        # Coalesce(..., 0) заменяет NULL на 0, если у кампании нет дохода.
        total_revenue=Coalesce(
            Sum("leads__contracts_history__contract__amount", filter=Q(leads__contracts_history__is_deleted=False)),
            0,
            output_field=DecimalField(),
        ),
        # Рассчитываем соотношение дохода к бюджету.
        # Используем Case/When, чтобы избежать деления на ноль, если бюджет равен 0.
        # Используем ExpressionWrapper, чтобы явно указать Django,
        # что результат деления должен быть DecimalField.
        # Это решает проблемы с типами данных на уровне базы данных.
        profit=Case(
            When(budget=0, then=None),  # Если бюджет 0, оставляем поле пустым
            default=ExpressionWrapper(
                (F("total_revenue") / F("budget")) * 100,  # Умножаем на 100, чтобы получить проценты
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
        ),
    )


# Определяем тип для словаря, чтобы mypy понимал его структуру.
class CampaignDetailStats(TypedDict):
    """Типизированный словарь для данных детальной статистики."""

    leads_list: list
    total_leads: int
    total_active_clients: int
    total_revenue: Decimal
    profit: float | None


def get_detailed_stats_for_campaign(campaign: AdCampaign, status_filter: str) -> CampaignDetailStats:
    """
    Рассчитывает и возвращает детальную статистику для одной рекламной кампании.

    Args:
        campaign: Экземпляр AdCampaign, для которого рассчитывается статистика.
        status_filter: Строка с фильтром по статусу ('', 'active', 'archived', 'in_work').

    Returns:
        CampaignDetailStats: Словарь с подробной статистикой.
    """

    # 1. Получаем всех лидов кампании, предзагружая историю контрактов.

    # Внутри предзагрузки также подтягиваем данные самих контрактов.
    leads_query = campaign.leads.all().prefetch_related(
        # Prefetch - для обратной связи (может быть много записей).
        Prefetch("contracts_history", queryset=ActiveClient.objects.select_related("contract"))
    )

    # 2. Копируем queryset в список.
    all_leads_list = list(leads_query)

    # 3. Рассчитываем KPI на основе всех привлеченных лидов.

    # Общий доход: суммируем amount всех контрактов из всей истории всех лидов.
    total_revenue = Decimal(0)

    for lead in all_leads_list:
        for history_entry in lead.contracts_history.all():
            if history_entry.contract:
                total_revenue += history_entry.contract.amount

    # Активные клиенты: считаем тех, у кого есть текущий активный контракт.
    active_clients_count = sum(1 for lead in all_leads_list if lead.active_contract)

    # Рентабельность
    profit = float((total_revenue / campaign.budget) * 100) if campaign.budget > 0 else None

    # 4. Фильтруем список для отображения в таблице.

    # Копируем список.
    display_leads_list = all_leads_list[:]

    if status_filter == "active":
        display_leads_list = [lead for lead in display_leads_list if lead.active_contract]
    elif status_filter == "archived":
        # "Архивный" - это тот, кто НЕ активен и НЕ находится в работе.
        # То есть:
        # 1. Либо у него есть история контрактов, но нет активного.
        # 2. Либо у него стоит статус "Потерян".
        display_leads_list = [
            lead
            for lead in display_leads_list
            if (not lead.active_contract and lead.contracts_history.exists())
            or (lead.status == PotentialClient.Status.LOST)
        ]
    elif status_filter == "in_work":
        # "В работе" - это тот, у кого нет истории контрактов И он не "потерян".
        display_leads_list = [
            lead
            for lead in display_leads_list
            if not lead.contracts_history.exists() and lead.status != PotentialClient.Status.LOST
        ]

    # Возвращаем результат.
    return {
        "leads_list": display_leads_list,  # В таблицу идет отфильтрованный список
        "total_leads": len(all_leads_list),  # В KPI идет общее количество привлеченных лидов
        "total_active_clients": active_clients_count,  # В KPI идет количество текущих активных клиентов
        "total_revenue": total_revenue,  # В KPI идет общий доход за все время
        "profit": profit,
    }
