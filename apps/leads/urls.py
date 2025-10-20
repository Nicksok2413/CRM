from django.urls import path

from .views import (
    LeadCreateView,
    LeadDeleteView,
    LeadDetailView,
    LeadListView,
    LeadUpdateView,
    UpdateLeadStatusView,
    get_lead_creation_stats,
)

# Пространство имен для URL-адресов этого приложения.
# Позволит использовать, например, `{% url 'leads:list' %}` в шаблонах.
app_name = "leads"

urlpatterns = [
    path("", LeadListView.as_view(), name="list"),
    path("new/", LeadCreateView.as_view(), name="create"),
    path("<int:pk>/", LeadDetailView.as_view(), name="detail"),
    path("<int:pk>/delete/", LeadDeleteView.as_view(), name="delete"),
    path("<int:pk>/edit/", LeadUpdateView.as_view(), name="edit"),
    # URL для обновления статуса лида.
    path("<int:pk>/update-status/<str:status>/", UpdateLeadStatusView.as_view(), name="update_status"),
    # URL для API-endpoint, возвращающий статистику создания лидов за последние 30 дней в формате JSON.
    path("api/lead-stats/", get_lead_creation_stats, name="api_lead_stats"),
]
