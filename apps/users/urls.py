from django.urls import path
from django.views.decorators.cache import cache_page

from .views import IndexView

# Пространство имен для URL-адресов этого приложения.
# Позволит использовать, например, `{% url 'users:index' %}` в шаблонах.
app_name = "users"

urlpatterns = [
    # Корневой URL будет отображать главную страницу.
    # Кэшируем всю HTML-страницу на 5 минут (300 секунд).
    path("", cache_page(60 * 5)(IndexView.as_view()), name="index"),
]
