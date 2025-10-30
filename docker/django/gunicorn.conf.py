"""
Конфигурационный файл для Gunicorn.
"""

import multiprocessing

# Адрес и порт, на которых будет работать Gunicorn.
# '0.0.0.0' делает сервер доступным извне контейнера (для Nginx).
bind = "0.0.0.0:8000"

# Получаем количество ядер CPU, доступных для контейнера.
cpu_cores = multiprocessing.cpu_count()

# Количество рабочих процессов (workers).
workers = (2 * cpu_cores) + 1  # Общая рекомендация

# Класс worker'а.
worker_class = "gevent"  # Лучший класс для I/O-bound приложений

# Количество "зеленых" потоков на один worker-процесс.
worker_connections = 1000  # Стандартное значение по умолчанию

# Уровень логирования.
loglevel = "info"

# Пути к файлам логов Gunicorn.
# Они будут доступны через volume `log_data`.
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
