from django.urls import path

from .views import (
    ActiveClientCreateFromLeadView,
    ActiveClientDetailView,
    ActiveClientDeleteView,
    ActiveClientListView,
    ActiveClientUpdateView,
)

# Пространство имен для URL-адресов этого приложения
# Позволит использовать, например, `{% url 'customers:list' %}` в шаблонах
app_name = 'customers'

urlpatterns = [
    path('', ActiveClientListView.as_view(), name='list'),
    path('<int:pk>/', ActiveClientDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', ActiveClientDeleteView.as_view(), name='delete'),
    path('<int:pk>/edit/', ActiveClientUpdateView.as_view(), name='edit'),

    # URL для создания активного клиента из лида
    path('new/from-lead/<int:lead_pk>/', ActiveClientCreateFromLeadView.as_view(), name='create_from_lead'),
]
