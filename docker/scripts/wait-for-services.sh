#!/bin/sh

# ==============================================================================
# Общий скрипт для ожидания готовности внешних сервисов (БД, Redis и т.д.).
# ==============================================================================

# `set -e` — это команда "fail fast". Если любая из последующих команд
# завершится с ошибкой, скрипт немедленно прекратит выполнение.
set -e

# Функция для проверки готовности БД (PostgreSQL).
wait_for_db() {
    echo "-> (Wait Script) Ожидание запуска PostgreSQL..."
    python << END
import os
import psycopg
import sys
import time

# Собираем строку подключения из переменных окружения, которые передал docker-compose.
conn_str = (
    f"dbname={os.environ['DB_NAME']} "
    f"user={os.environ['DB_USER']} "
    f"password={os.environ['DB_PASSWORD']} "
    f"host={os.environ['DB_HOST']} "
    f"port={os.environ['DB_PORT']}"
)

# Пытаемся подключиться 30 раз с интервалом в 1 секунду.
try:
    conn = None
    print("Попытка подключения к БД...")

    for attempt in range(30):
        try:
            conn = psycopg.connect(conn_str, connect_timeout=2)
            print(f"   Попытка {attempt+1}/30: PostgreSQL запущен - соединение установлено.")
            break
        except psycopg.OperationalError as exc:
            print(f"   Попытка {attempt+1}/30: PostgreSQL недоступен, ожидание... ({exc})")
            time.sleep(1)

    # Если после всех попыток подключиться не удалось, выходим с кодом ошибки 1.
    if conn is None:
        print("-> (Wait Script) ОШИБКА: Не удалось подключиться к PostgreSQL после 30 секунд.", file=sys.stderr)
        sys.exit(1)

    # Закрываем соединение.
    conn.close()

except KeyError as exc:
    print(f"-> (Wait Script) ОШИБКА: переменная окружения {exc} не установлена.", file=sys.stderr)
    sys.exit(1)
except Exception as exc:
    print(f"-> (Wait Script) ОШИБКА: произошла ошибка при проверке БД (psycopg3): {exc}", file=sys.stderr)
    sys.exit(1)
END
}

# Функция для проверки готовности Redis.
wait_for_redis() {
    echo "-> (Wait Script) Ожидание запуска Redis..."
    python << END
import os
import sys
import time
import redis

# Получаем хост и порт из переменных окружения.
redis_host = os.environ.get("REDIS_HOST", "redis")
redis_port = int(os.environ.get("REDIS_PORT", 6379))

# Создаем клиент Redis. `decode_responses=True` для удобства отладки.
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Пытаемся подключиться 30 раз с интервалом в 1 секунду.
print("Попытка подключения к Redis...")

for attempt in range(30):
    try:
        # PING - это стандартный способ проверки "здоровья" Redis.
        # Если она возвращает 'PONG', значит, сервер готов.
        if redis_client.ping():
            print(f"   Попытка {attempt+1}/30: Redis запущен - получен ответ PONG.")
            sys.exit(0) # Успешный выход из Python-скрипта.
    except redis.exceptions.ConnectionError as exc:
        print(f"   Попытка {attempt+1}/30: Redis недоступен, ожидание... ({exc})")
        time.sleep(1)

print("-> (Wait Script) ОШИБКА: Не удалось подключиться к Redis после 30 секунд.", file=sys.stderr)
sys.exit(1) # Выход с ошибкой, если подключиться не удалось.
END
}

# `"$@"` - это все аргументы, переданные скрипту.
# Итерируемся по ним и вызываем соответствующую функцию.
for service in "$@"; do
    case $service in
        postgres)
            wait_for_postgres
            ;;
        redis)
            wait_for_redis
            ;;
        *)
            echo "-> (Wait Script) Неизвестный сервис: $service"
            ;;
    esac
done