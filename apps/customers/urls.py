from django.urls import path

from .views import ActiveClientCreateView


# Пространство имен для URL-адресов этого приложения
# Позволит использовать, например, `{% url 'customers:list' %}` в шаблонах
app_name = 'customers'

urlpatterns = [
    # URL для создания активного клиента из лида
    path('new/from-lead/<int:lead_pk>/', ActiveClientCreateView.as_view(), name='create_from_lead'),
]
