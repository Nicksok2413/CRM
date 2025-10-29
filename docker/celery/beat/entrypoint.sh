#!/bin/sh

set -e

# Указываем пользователя, от имени которого будет запущен процесс.
APP_USER=appuser

echo "-> (Celery Beat Entrypoint) Ожидание запуска Redis..."

# Простой цикл ожидания Redis.
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 1
done

echo "-> (Celery Beat Entrypoint) Redis запущен."

# Удаляем старый PID-файл планировщика, если он остался после сбоя.
# Это предотвращает ошибки "Scheduler is already running".
rm -f /app/celerybeat.pid

# Запускаем Celery Beat от имени `appuser`.
echo "-> (Celery Beat Entrypoint) Запуск Celery Beat от пользователя ${APP_USER}..."
exec su-exec "${APP_USER}" celery -A config.celery beat --loglevel=info --pidfile=/app/celerybeat.pid