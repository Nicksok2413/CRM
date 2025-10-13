from django.urls import path

from .views import (
    LeadCreateView,
    LeadDeleteView,
    LeadDetailView,
    LeadListView,
    LeadUpdateView,
)

# Пространство имен для URL-адресов этого приложения
# Позволит использовать, например, `{% url 'leads:list' %}` в шаблонах
app_name = "leads"

urlpatterns = [
    path("", LeadListView.as_view(), name="list"),
    path("new/", LeadCreateView.as_view(), name="create"),
    path("<int:pk>/", LeadDetailView.as_view(), name="detail"),
    path("<int:pk>/delete/", LeadDeleteView.as_view(), name="delete"),
    path("<int:pk>/edit/", LeadUpdateView.as_view(), name="edit"),
]
