# ==============================================================================
# Dockerfile для сервиса Nginx.
# ==============================================================================
# Используем официальный, легковесный образ Nginx на базе Alpine Linux.
FROM nginx:1.28-alpine

# Устанавливаем openssl для генерации самоподписанных SSL-сертификатов в entrypoint-скрипте.
# --no-cache гарантирует, что кэш пакетов не будет сохранен в слое, уменьшая размер образа.
RUN apk --no-cache add openssl

# Удаляем стандартную конфигурацию Nginx.
RUN rm /etc/nginx/conf.d/default.conf

# Копируем кастомный конфигурационный файл.
# COPY ./docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./docker/nginx/nginx.conf /etc/nginx/conf.d/crm.conf

# Создаем директории для логов Nginx и даем права пользователю nginx.
# Это гарантирует, что Nginx сможет писать в свои лог-файлы.
RUN mkdir -p /var/log/nginx && \
    touch /var/log/nginx/access.log /var/log/nginx/error.log && \
    chown -R nginx:nginx /var/log/nginx

# Создаем директорию для SSL-сертификатов.
# Права на запись не нужны, но установим владельца.
RUN mkdir -p /etc/nginx/certs && \
    chown nginx:nginx /etc/nginx/certs

# Копируем entrypoint-скрипт в специальную директорию Docker для entrypoint-скриптов и делаем его исполняемым.
COPY ./docker/nginx/entrypoint.sh /docker-entrypoint.d/10-ssl-cert-gen.sh
RUN chmod +x /docker-entrypoint.d/10-ssl-cert-gen.sh

# Открываем порты для HTTP (80) и HTTPS (443).
EXPOSE 80
EXPOSE 443
