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
    required_vars = ['TELEGRAM_BOT_TOKEN']
    ai_provider = os.getenv('AI_PROVIDER', 'openai').lower()
    
    # Добавляем проверку ключа в зависимости от провайдера
    if ai_provider == 'claude':
        required_vars.append('ANTHROPIC_API_KEY')
    else:
        required_vars.append('OPENAI_API_KEY')
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        print("📝 Проверьте файл .env.dev")
        sys.exit(1)
    
    print("✅ Переменные окружения загружены из .env.dev")
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    print(f"🤖 Бот токен: {bot_token[:20] if bot_token else 'НЕ НАЙДЕН'}...")
    print(f"🤖 AI Провайдер: {ai_provider.upper()}")
    
    if ai_provider == 'claude':
        claude_key = os.getenv('ANTHROPIC_API_KEY', '')
        print(f"🔑 Claude ключ: {claude_key[:20] if claude_key else 'НЕ НАЙДЕН'}...")
    else:
        openai_key = os.getenv('OPENAI_API_KEY', '')
        print(f"🔑 OpenAI ключ: {openai_key[:20] if openai_key else 'НЕ НАЙДЕН'}...")
    print("🚀 Запускаю НОВУЮ ЛОГИКУ v6.0 для Стаса!")
    
    # Запускаем основной файл
    from main import main
    main() 