# ==============================================================================
# Этап 1: "Builder" — Среда для сборки зависимостей.
# ==============================================================================
# Используем легковесный образ Python.
FROM python:3.12-slim as builder

# Устанавливаем системные зависимости, которые нужны только для сборки:
# - curl: для установки PDM.
# - build-essential, wget, ca-certificates: для компиляции su-exec.
# `rm -rf /var/lib/apt/lists/*` — удаляем списки пакетов.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Компилируем su-exec — утилиту для безопасного понижения привилегий с root до обычного пользователя.
RUN wget -O su-exec.tar.gz https://github.com/ncopa/su-exec/archive/master.tar.gz && \
    tar -xzf su-exec.tar.gz && \
    cd su-exec-master && \
    make && \
    cp su-exec /usr/local/bin/su-exec && \
    cd / && \
    rm -rf su-exec.tar.gz su-exec-master

# Устанавливаем PDM.
RUN curl -sSL https://pdm-project.org/install-pdm.py | python3 -
# Добавляем путь к pdm в переменную окружения PATH.
ENV PATH="/root/.local/bin:${PATH}"
# Глобально отключаем создание виртуальных окружений для PDM.
RUN pdm config python.use_venv false

# Устанавливаем рабочую директорию.
WORKDIR /app

# Копируем только файлы, определяющие зависимости.
# Этот слой будет кэшироваться и не будет пересобираться, пока pyproject.toml или pdm.lock не изменятся.
COPY pyproject.toml pdm.lock ./

# Устанавливаем production-зависимости.
RUN pdm install --prod --no-editable

# ==============================================================================
# Этап 2: "Runner" — Финальный, чистый образ для запуска приложения.
# ==============================================================================
# Используем легковесный образ Python.
FROM python:3.12-slim

# Устанавливаем только те системные пакеты, которые необходимы для работы приложения:
# - libpq-dev: для работы драйвера psycopg.
# `rm -rf /var/lib/apt/lists/*` — удаляем списки пакетов для уменьшения размера образа.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Стандартные переменные окружения для Python в Docker.
# Весь вывод (print, логи) будет сразу отправляться в консоль Docker.
ENV PYTHONUNBUFFERED 1
# Не создавать .pyc файлы.
ENV PYTHONDONTWRITEBYTECODE 1
# Добавляем путь к пакетам в PYTHONPATH, чтобы Python их нашел.
ENV PYTHONPATH="/app/lib"

# Устанавливаем рабочую директорию.
WORKDIR /app

# Копируем скомпилированный `su-exec` из этапа "builder".
COPY --from=builder /usr/local/bin/su-exec /usr/local/bin/su-exec

# Копируем установленные Python-зависимости из этапа "builder" в папку /app/lib.
# Это делает все библиотеки доступными для Python, без активации .venv.
COPY --from=builder /app/__pypackages__/3.12/lib/. /app/lib/

# Копируем entrypoint-скрипты.
COPY ./docker/celery/beat/entrypoint.sh /docker/celery/beat/entrypoint.sh
COPY ./docker/celery/worker/entrypoint.sh /docker/celery/worker/entrypoint.sh
COPY ./docker/django/entrypoint.sh /entrypoint.sh
COPY ./docker/scripts/wait-for-services.sh /wait-for-services.sh

# Устанавливаем права на выполнение entrypoint-скриптов.
RUN chmod +x /docker/celery/beat/entrypoint.sh \
    /docker/celery/worker/entrypoint.sh \
    /entrypoint.sh \
    /wait-for-services.sh

# Создаем системную группу `appgroup` и системного non-root пользователя `appuser`.
# Это нужно для безопасности, чтобы не запускать приложение от root.
# `--no-create-home` — не создавать домашнюю директорию.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup --no-create-home appuser

# Меняем владельца рабочей директории на appuser.
RUN chown appuser:appgroup /app

# Копируем весь код нашего приложения, сразу устанавливая правильного владельца.
COPY --chown=appuser:appgroup . .

# Сообщаем Docker, что контейнер будет слушать порт 8000.
EXPOSE 8000

# Устанавливаем скрипт как точку входа.
# Он будет выполнен перед основной командой контейнера.
ENTRYPOINT ["/entrypoint.sh"]
