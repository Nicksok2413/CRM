import os

from celery import Celery

# Устанавливаем переменную окружения, чтобы Celery знал, где искать настройки Django.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Создаем экземпляр приложения Celery.
app = Celery("config")

# Загружаем конфигурацию из настроек Django
# Все настройки Celery в `settings.py` должны начинаться с `CELERY_`.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически обнаруживаем и регистрируем задачи из всех файлов tasks.py в установленных приложениях Django.
app.autodiscover_tasks()
