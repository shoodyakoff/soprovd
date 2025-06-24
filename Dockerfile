# Сопровод v6.0 - Telegram Bot for Cover Letters
# Updated dependencies: supabase==2.4.0 + gotrue==2.8.0 (fix proxy error)
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Run the application
CMD ["python", "main.py"] 