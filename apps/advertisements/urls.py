from django.urls import path

from .views import (
    AdCampaignCreateView,
    AdCampaignDeleteView,
    AdCampaignDetailView,
    AdCampaignListView,
    AdCampaignUpdateView,
)

# Пространство имен для URL-адресов этого приложения
# Позволит использовать, например, `{% url 'ads:list' %}` в шаблонах
app_name = 'ads'

urlpatterns = [
    path('', AdCampaignListView.as_view(), name='list'),
    path('new/', AdCampaignCreateView.as_view(), name='create'),
    path('<int:pk>/', AdCampaignDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', AdCampaignDeleteView.as_view(), name='delete'),
    path('<int:pk>/edit/', AdCampaignUpdateView.as_view(), name='edit'),

]
