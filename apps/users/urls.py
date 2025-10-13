from django.urls import path

from .views import IndexView

# Пространство имен для URL-адресов этого приложения
# Позволит использовать, например, `{% url 'users:index' %}` в шаблонах
app_name = "users"

urlpatterns = [
    # Корневой URL будет отображать главную страницу
    path("", IndexView.as_view(), name="index"),
]
