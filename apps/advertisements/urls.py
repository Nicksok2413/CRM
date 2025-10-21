from django.urls import path
from django.views.decorators.cache import cache_page

from .views import (
    AdCampaignCreateView,
    AdCampaignDeleteView,
    AdCampaignDetailStatisticView,
    AdCampaignDetailView,
    AdCampaignListView,
    AdCampaignStatisticView,
    AdCampaignUpdateView,
)

# Пространство имен для URL-адресов этого приложения.
# Позволит использовать, например, `{% url 'ads:list' %}` в шаблонах.
app_name = "ads"

urlpatterns = [
    path("", AdCampaignListView.as_view(), name="list"),
    path("new/", AdCampaignCreateView.as_view(), name="create"),
    path("<int:pk>/", AdCampaignDetailView.as_view(), name="detail"),
    path("<int:pk>/delete/", AdCampaignDeleteView.as_view(), name="delete"),
    path("<int:pk>/edit/", AdCampaignUpdateView.as_view(), name="edit"),
    # URL для детальной статистики по одной рекламной кампании.
    path("<int:pk>/statistic/", AdCampaignDetailStatisticView.as_view(), name="detail_statistic"),
    # URL для статистики всех рекламных кампаний.
    # Кэшируем всю HTML-страницу на 10 минут (600 секунд).
    path("statistic/", cache_page(60 * 10)(AdCampaignStatisticView.as_view()), name="statistic"),
]
