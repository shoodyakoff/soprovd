"""
Главный файл Telegram-бота Сопровод v6.0
НОВАЯ ЛОГИКА: единый анализ через smart_analyzer_v6
FORCED UPDATE: 2025-06-24 08:01:00 UTC - COMMIT fdccee3
"""

# ПРИНУДИТЕЛЬНЫЙ ВЫВОД САМЫЙ ПЕРВЫЙ - COMMIT fdccee3
print("=" * 60)
print("🚨🚨🚨 MAIN.PY STARTING - COMMIT fdccee3 🚨🚨🚨")
print("🚨🚨🚨 NEW CODE MUST BE RUNNING NOW! 🚨🚨🚨")
print("=" * 60)

import logging
import os
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

# DEBUG: Проверим переменные окружения ДО импорта config
print("=" * 50)
print("🚨 RAILWAY FORCED DEBUG START 🚨")
print("=" * 50)
print(f"🔍 RAILWAY DEBUG: SUPABASE_URL = {os.getenv('SUPABASE_URL', 'NOT_FOUND')}")
print(f"🔍 RAILWAY DEBUG: SUPABASE_KEY = {os.getenv('SUPABASE_KEY', 'NOT_FOUND')[:20]}...")
print(f"🔍 RAILWAY DEBUG: ENVIRONMENT = {os.getenv('ENVIRONMENT', 'NOT_FOUND')}")
print(f"🔍 RAILWAY DEBUG: TELEGRAM_BOT_TOKEN = {os.getenv('TELEGRAM_BOT_TOKEN', 'NOT_FOUND')[:20]}...")
print("=" * 50)
print("🚨 RAILWAY FORCED DEBUG END 🚨")
print("=" * 50)

from config import TELEGRAM_BOT_TOKEN

from handlers.simple_conversation_v6 import get_conversation_handler, get_command_handlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
        logging.FileHandler('bot.log', encoding='utf-8')  # Сохранение в файл
    ]
)
logger = logging.getLogger(__name__)

async def check_ai_api():
    """
    Проверяет работу AI API при запуске (OpenAI или Claude)
    """
    from services.ai_factory import get_ai_service, AIFactory
    
    ai_service = get_ai_service()
    provider_name = AIFactory.get_provider_name()
    
    is_working = await ai_service.test_api_connection()
    if not is_working:
        logger.error(f"❌ {provider_name} API не работает! Проверьте API ключ и интернет соединение.")
        logger.error("Бот будет запущен, но генерация писем может не работать.")
    else:
        logger.info(f"✅ {provider_name} API работает нормально")
    
    return is_working

async def post_init(application):
    """
    Функция, вызываемая после инициализации приложения
    """
    from services.ai_factory import AIFactory
    provider_name = AIFactory.get_provider_name()
    logger.info(f"Проверяю {provider_name} API...")
    await check_ai_api()

def main():
    """
    Основная функция запуска бота v6.0 - НОВАЯ ЛОГИКА для Стаса!
    """
    # ДИАГНОСТИКА: Сравним что в Railway Variables vs что читает код
    print("🔍 TELEGRAM TOKEN DIAGNOSTIC:")
    print(f"   Expected: 7647818988:AAFgh0...")
    print(f"   From config.py: {TELEGRAM_BOT_TOKEN}")
    print(f"   From os.getenv: {os.getenv('TELEGRAM_BOT_TOKEN')}")
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN.startswith('7647818988'):
        print("✅ Correct token found")
    else:
        print("❌ WRONG TOKEN! Railway variables not working!")
        print("🚨 This explains why old bot instance is running")
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    # Добавляем НОВЫЙ v6.0 handler - только актуальная логика!
    v6_handler = get_conversation_handler()
    application.add_handler(v6_handler)
    logger.info("🚀 Стас, v6.0 ConversationHandler добавлен - НОВАЯ ЛОГИКА!")
    
    # Добавляем команды help, about, support
    command_handlers = get_command_handlers()
    for handler in command_handlers:
        application.add_handler(handler)
    logger.info("✅ Команды help, about, support зарегистрированы!")
    
    # Старый help handler удален - используем новый из handlers
    
    logger.info("🚀 Стас, бот Сопровод v6.0 запущен! НОВАЯ ЛОГИКА: smart_analyzer_v6 + UNIFIED_ANALYSIS_PROMPT!")
    
    # Запускаем бота
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main() 