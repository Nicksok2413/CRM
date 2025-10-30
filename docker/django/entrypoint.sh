#!/bin/sh

# ==============================================================================
# Entrypoint-скрипт для Django-контейнера.
# Выполняет команды, необходимые перед запуском основного процесса.
# ==============================================================================

# `set -e` — это команда "fail fast". Если любая из последующих команд
# завершится с ошибкой, скрипт немедленно прекратит выполнение.
set -e

# Django для работы нужна БД (PostgreSQL) и сервис кэширования (Redis).
# Вызываем скрипт для ожидания готовности внешних сервисов, передавая ему, какие сервисы нужно ждать.
/wait-for-services.sh postgres redis

echo "-> (Django Entrypoint) Все внешние сервисы запущены."

# Установка прав на тома.
# Указываем пользователя и группу, под которыми будет работать приложение.
APP_USER=appuser
APP_GROUP=appgroup

echo "-> (Django Entrypoint) Установка прав на volumes..."

# Используем chown для изменения владельца точки монтирования томов.
# Это нужно делать от root перед понижением привилегий.
chown -R "${APP_USER}:${APP_GROUP}" /app/logs
chown -R "${APP_USER}:${APP_GROUP}" /app/staticfiles
chown -R "${APP_USER}:${APP_GROUP}" /app/uploads

# Создаем пустые файлы логов от имени root, а затем меняем их владельца.
# Это гарантирует, что Gunicorn, запущенный от appuser, сможет в них писать.
touch /app/logs/gunicorn_access.log /app/logs/gunicorn_error.log
chown "${APP_USER}:${APP_GROUP}" /app/logs/gunicorn_*.log

echo "   Права установлены."

echo "-> (Django Entrypoint) Применение миграций базы данных от пользователя ${APP_USER}..."
# Применяем все недостающие миграции от имени appuser.
# `--noinput` отключает все интерактивные запросы.
su-exec "${APP_USER}" python manage.py migrate --noinput

echo "-> (Django Entrypoint) Сбор статических файлов от пользователя ${APP_USER}..."
# Собираем статику от имени appuser.
# Собираем все статические файлы из приложений в единую директорию (STATIC_ROOT), чтобы Nginx мог их эффективно раздавать.
su-exec "${APP_USER}" python manage.py collectstatic --noinput

# Запускаем основной процесс Gunicorn от имени appuser.
echo "-> (Django Entrypoint) Запуск основного процесса (Gunicorn) от пользователя ${APP_USER}..."
exec su-exec "${APP_USER}" "$@"