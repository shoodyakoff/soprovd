# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Force complete rebuild - COMMIT fdccee3
RUN echo "COMMIT: fdccee3 $(date)" > /tmp/build_info && \
    rm -rf /tmp/* || true && \
    echo "Cleared cache"

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Указываем команду запуска
CMD ["python", "main.py"] 