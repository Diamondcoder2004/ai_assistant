FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода (исключая venv и __pycache__)
COPY api/ ./api/
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY utils/ ./utils/
COPY prompts/ ./prompts/
COPY config.py .
COPY main.py .

# Создание директории для логов
RUN mkdir -p logs

# Переменная окружения для Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Порт приложения
EXPOSE 8880

# Команда запуска
CMD ["uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8880"]
