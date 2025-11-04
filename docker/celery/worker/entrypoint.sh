#!/bin/sh

# ==============================================================================
# Entrypoint-скрипт для контейнера Celery Worker.
# ==============================================================================

# `set -e` — это команда "fail fast". Если любая из последующих команд
# завершится с ошибкой, скрипт немедленно прекратит выполнение.
set -e

# Worker'у для работы нужен брокер сообщений (Redis).
# Вызываем скрипт для ожидания готовности внешних сервисов, передавая ему, какие сервисы нужно ждать.
/wait-for-services.sh redis

echo "-> (Celery Worker Entrypoint) Redis запущен."

# Запуск основного процесса.

# Указываем пользователя, от имени которого будет запущен процесс.
APP_USER=appuser

# Запускаем Celery Worker от имени appuser, передавая команду из docker-compose.yml.
echo "-> (Celery Worker Entrypoint) Запуск Celery Worker от пользователя ${APP_USER}..."
#exec su-exec "${APP_USER}" "$@"
exec su-exec "${APP_USER}" celery -A config.celery worker --loglevel=info