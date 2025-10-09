from django.urls import path

from .views import (
    AdCampaignCreateView,
    AdCampaignDeleteView,
    AdCampaignDetailView,
    AdCampaignListView,
    AdCampaignUpdateView,
)

app_name = 'ads'  # Используем 'ads', как в шаблонах

urlpatterns = [
    path('', AdCampaignListView.as_view(), name='list'),
    path('new/', AdCampaignCreateView.as_view(), name='create'),
    path('<int:pk>/', AdCampaignDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', AdCampaignDeleteView.as_view(), name='delete'),
    path('<int:pk>/edit/', AdCampaignUpdateView.as_view(), name='edit'),

]
