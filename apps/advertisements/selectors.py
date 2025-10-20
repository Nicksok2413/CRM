"""
Селекторы (Selectors) для приложения advertisements.

Этот файл содержит функции, которые инкапсулируют сложную логику извлечения данных из базы данных.
Они отделяют бизнес-логику запросов от представлений (Views), делая код более чистым,
переиспользуемым и легко тестируемым.
"""

from typing import TypedDict

from django.db.models import Case, Count, DecimalField, ExpressionWrapper, F, Prefetch, Q, QuerySet, Sum, When
from django.db.models.functions import Coalesce

from apps.customers.models import ActiveClient

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
    total_revenue: DecimalField
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

    # Получаем всех лидов кампании, предзагружая историю контрактов.
    # И внутри этой предзагрузки также подтягиваем данные самих контрактов.
    leads_query = campaign.leads.all().prefetch_related(
        # Prefetch - для обратной связи (может быть много записей).
        Prefetch("contracts_history", queryset=ActiveClient.objects.select_related("contract"))
    )

    # Копируем queryset в список.
    leads_list = list(leads_query)

    # Фильтруем список в зависимости от GET-параметра.
    if status_filter == "active":
        leads_list = [lead for lead in leads_list if lead.active_contract]
    elif status_filter == "archived":
        leads_list = [lead for lead in leads_list if not lead.active_contract and lead.contracts_history.exists()]
    elif status_filter == "in_work":
        leads_list = [lead for lead in leads_list if not lead.contracts_history.exists()]

    # Рассчитываем общую статистику на основе отфильтрованного списка.
    active_clients = [lead.active_contract for lead in leads_list if lead.active_contract is not None]
    total_revenue = sum(active_client.contract.amount for active_client in active_clients)
    profit = (total_revenue / campaign.budget) * 100 if campaign.budget > 0 else None

    # 4. Возвращаем типизированный словарь
    return {
        "leads_list": leads_list,
        "total_leads": len(leads_list),
        "total_active_clients": len(active_clients),
        "total_revenue": total_revenue,
        "profit": profit,
    }
