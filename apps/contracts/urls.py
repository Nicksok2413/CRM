from django.urls import path

from .views import (
    ContractCreateView,
    ContractDeleteView,
    ContractDetailView,
    ContractListView,
    ContractUpdateView,
)

# Пространство имен для URL-адресов этого приложения
# Позволит использовать, например, `{% url 'contracts:list' %}` в шаблонах
app_name = "contracts"

urlpatterns = [
    path("", ContractListView.as_view(), name="list"),
    path("new/", ContractCreateView.as_view(), name="create"),
    path("<int:pk>/", ContractDetailView.as_view(), name="detail"),
    path("<int:pk>/delete/", ContractDeleteView.as_view(), name="delete"),
    path("<int:pk>/edit/", ContractUpdateView.as_view(), name="edit"),
]
