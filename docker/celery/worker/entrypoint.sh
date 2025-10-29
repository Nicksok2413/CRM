#!/bin/sh

set -e

# Указываем пользователя, от имени которого будет запущен процесс.
APP_USER=appuser

echo "-> (Celery Worker Entrypoint) Ожидание запуска Redis..."

# Простой цикл ожидания Redis.
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 1
done

echo "-> (Celery Worker Entrypoint) Redis запущен."

# Запускаем Celery Worker от имени `appuser`.
echo "-> (Celery Worker Entrypoint) Запуск Celery Worker от пользователя ${APP_USER}..."
exec su-exec "${APP_USER}" celery -A config.celery worker --loglevel=info