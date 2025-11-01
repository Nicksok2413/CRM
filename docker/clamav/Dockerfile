# Используем официальный образ
FROM clamav/clamav:latest

# Отключаем первоначальный запуск freshclam при старте контейнера.
# Фоновое обновление все равно будет работать.
RUN sed -i 's/freshclam -d --daemon-notify/echo "Skipping initial freshclam daemon"/g' /init