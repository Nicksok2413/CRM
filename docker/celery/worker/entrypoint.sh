#!/bin/sh

# ==============================================================================
# Entrypoint-скрипт для контейнера Celery Worker.
# ==============================================================================

# `set -e` — это команда "fail fast". Если любая из последующих команд
# завершится с ошибкой, скрипт немедленно прекратит выполнение.
set -e

# Ожидание зависимостей.
# Worker'у для работы нужен брокер сообщений. В нашем случае это Redis.

# Функция для проверки готовности Redis.
wait_for_redis() {
    echo "-> (Celery Worker Entrypoint) Ожидание запуска Redis..."
    python << END
import os
import sys
import time
import redis

# Получаем хост и порт из переменных окружения.
redis_host = os.environ.get("REDIS_HOST", "redis")
redis_port = int(os.environ.get("REDIS_PORT", 6379))

# Создаем клиент Redis. `decode_responses=True` для удобства отладки.
r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Пытаемся подключиться 30 раз с интервалом в 1 секунду.
print("Попытка подключения к Redis...")

for attempt in range(30):
    try:
        # PING - это стандартный способ проверки "здоровья" Redis.
        # Если она возвращает 'PONG', значит, сервер готов.
        if r.ping() == True:
            print(f"   Попытка {attempt+1}/30: Redis запущен - получен ответ PONG.")
            sys.exit(0) # Успешный выход из Python-скрипта.
    except redis.exceptions.ConnectionError as exc:
        print(f"   Попытка {attempt+1}/30: Redis недоступен, ожидание... ({exc})")
        time.sleep(1)

print("-> (Celery Worker Entrypoint) ОШИБКА: Не удалось подключиться к Redis после 30 секунд.", file=sys.stderr)
sys.exit(1) # Выход с ошибкой, если подключиться не удалось.
END
}

# Ожидание готовности Redis.
wait_for_redis

echo "-> (Celery Worker Entrypoint) Redis запущен."

# Запуск основного процесса.

# Указываем пользователя, от имени которого будет запущен процесс.
APP_USER=appuser

# Запускаем Celery Worker от имени appuser.
echo "-> (Celery Worker Entrypoint) Запуск Celery Worker от пользователя ${APP_USER}..."
exec su-exec "${APP_USER}" "$@"