#!/usr/bin/env python3
"""
Запуск бота Сопровод в DEVELOPMENT режиме
Использует env.dev файл
"""
import os
import sys
from pathlib import Path

def load_env_file(filepath):
    """Загружает переменные из env файла"""
    if not Path(filepath).exists():
        print(f"❌ Файл {filepath} не найден!")
        print(f"📝 Создайте файл {filepath} на основе .env.example")
        sys.exit(1)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

if __name__ == "__main__":
    print("🚀 Запуск Сопровод в DEVELOPMENT режиме...")
    
    # Загружаем dev окружение
    load_env_file('.env.dev')
    
    # Проверяем обязательные переменные
    required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        print("📝 Проверьте файл .env.dev")
        sys.exit(1)
    
    print("✅ Переменные окружения загружены из .env.dev")
    print(f"🤖 Бот токен: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}...")
    print(f"🔑 OpenAI ключ: {os.getenv('OPENAI_API_KEY')[:20]}...")
    
    # Запускаем основной файл
    from main import main
    main() 