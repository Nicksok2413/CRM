#!/bin/sh

# ==============================================================================
# Entrypoint-скрипт для Django-контейнера.
# Выполняет команды, необходимые перед запуском основного процесса.
# ==============================================================================

# `set -e` — это команда "fail fast". Если любая из последующих команд
# завершится с ошибкой, скрипт немедленно прекратит выполнение.
set -e

# Функция для проверки готовности Базы Данных.
wait_for_db() {
    echo "-> (Entrypoint) Ожидание запуска PostgreSQL..."
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
    # Docker Compose увидит это и, в зависимости от настроек, перезапустит контейнер.
    if conn is None:
        print("-> (Entrypoint) ОШИБКА: Не удалось подключиться к PostgreSQL после 30 секунд.", file=sys.stderr)
        sys.exit(1)

    # Закрываем соединение.
    conn.close()

except KeyError as exc:
    print(f"-> (Entrypoint) ОШИБКА: переменная окружения {exc} не установлена.", file=sys.stderr)
    sys.exit(1)
except Exception as exc:
    print(f"-> (Entrypoint) ОШИБКА: произошла ошибка при проверке БД (psycopg3): {exc}", file=sys.stderr)
    sys.exit(1)
END
}

# Ожидание готовности Базы Данных.
wait_for_db

echo "-> (Entrypoint) PostgreSQL успешно запущен."

# Установка прав на тома.
# Указываем пользователя и группу, под которыми будет работать приложение.
APP_USER=appuser
APP_GROUP=appgroup

echo "-> (Entrypoint) Установка прав на volumes..."

# Используем chown для изменения владельца точки монтирования тома.
# Это нужно делать от root перед понижением привилегий.
chown -R "${APP_USER}:${APP_GROUP}" /app/staticfiles
chown -R "${APP_USER}:${APP_GROUP}" /app/uploads
chown -R "${APP_USER}:${APP_GROUP}" /app/logs
echo "   Права установлены."

echo "-> (Entrypoint) Применение миграций базы данных..."
# Применяем все недостающие миграции от имени appuser.
# `--noinput` отключает все интерактивные запросы.
su-exec "${APP_USER}" python manage.py migrate --noinput

echo "-> (Entrypoint) Сбор статических файлов..."
# Собираем статику от имени appuser.
# Собираем все статические файлы из приложений в единую директорию (STATIC_ROOT), чтобы Nginx мог их эффективно раздавать.
su-exec "${APP_USER}" python manage.py collectstatic --noinput

# Запускаем основной процесс Gunicorn от имени appuser.
echo "-> (Entrypoint) Запуск основного процесса (Gunicorn)..."
exec su-exec "${APP_USER}" "$@"