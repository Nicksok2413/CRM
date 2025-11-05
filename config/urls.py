"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Админ-панель
    path("admin/", admin.site.urls),
    # Встроенные URL для аутентификации (login, logout, password_reset, и т.д.)
    # Они будут доступны по адресам '/accounts/login/', '/accounts/logout/' и т.д.
    path("accounts/", include("django.contrib.auth.urls")),
    # Корневой маршрут обрабатываться в apps.users.urls.
    path("", include("apps.users.urls")),
    # Маршрут для приложения advertisements ("Рекламные кампании")
    path("ads/", include("apps.advertisements.urls")),
    # Маршрут для приложения contracts ("Контракты")
    path("contracts/", include("apps.contracts.urls")),
    # Маршрут для приложения customers ("Активные клиенты")
    path("customers/", include("apps.customers.urls")),
    # Маршрут для приложения leads ("Лиды")
    path("leads/", include("apps.leads.urls")),
    # Маршрут для метрик Prometheus
    path("metrics/", include("django_prometheus.urls")),
    # Маршрут для приложения products ("Услуги")
    path("products/", include("apps.products.urls")),
]

# ======================================================================
# НАСТРОЙКА ДЛЯ РАЗДАЧИ МЕДИАФАЙЛОВ В РЕЖИМЕ РАЗРАБОТКИ
# ======================================================================

# Это специальная конструкция, которая добавляет маршрут для медиафайлов,
# только если проект запущен в режиме отладки (DEBUG = True).
# В продакшене (DEBUG = False) эта строка не будет выполняться,
# так как раздачей файлов должен заниматься веб-сервер (Nginx).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
