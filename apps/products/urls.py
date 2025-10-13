from django.urls import path

from .views import ServiceCreateView, ServiceDeleteView, ServiceDetailView, ServiceListView, ServiceUpdateView

# Пространство имен для URL-адресов этого приложения
# Позволит использовать, например, `{% url 'products:list' %}` в шаблонах
app_name = "products"

urlpatterns = [
    path("", ServiceListView.as_view(), name="list"),
    path("new/", ServiceCreateView.as_view(), name="create"),
    path("<int:pk>/", ServiceDetailView.as_view(), name="detail"),
    path("<int:pk>/delete/", ServiceDeleteView.as_view(), name="delete"),
    path("<int:pk>/edit/", ServiceUpdateView.as_view(), name="edit"),
]
