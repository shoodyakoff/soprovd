"""
Главный файл Telegram-бота Сопровод v4.0
Простой поток: вакансия → резюме → письмо
"""
import logging
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

from config import TELEGRAM_BOT_TOKEN

from handlers.simple_conversation import get_simple_conversation_handler

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

async def check_openai_api():
    """
    Проверяет работу OpenAI API при запуске
    """
    from services.openai_service import OpenAIService
    openai_service = OpenAIService()
    
    is_working = await openai_service.test_api_connection()
    if not is_working:
        logger.error("❌ OpenAI API не работает! Проверьте API ключ и интернет соединение.")
        logger.error("Бот будет запущен, но генерация писем может не работать.")
    
    return is_working

async def post_init(application):
    """
    Функция, вызываемая после инициализации приложения
    """
    logger.info("Проверяю OpenAI API...")
    await check_openai_api()

def main():
    """
    Основная функция запуска бота v4.0 - только простой поток
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    # Добавляем ТОЛЬКО v4.0 simple handler - единственный режим
    simple_handler = get_simple_conversation_handler()
    application.add_handler(simple_handler)
    logger.info("🎯 v4.0 Simple ConversationHandler добавлен - единственный режим!")
    
    # Обработчик команды help
    async def help_handler(update, context):
        await update.message.reply_text(
            "📋 <b>Сопровод v4.0 - Умный генератор писем</b>\n\n"
            "🚀 /start - создать сопроводительное письмо\n"
            "❓ /help - показать эту справку\n\n"
            "💡 Просто отправьте /start и следуйте инструкциям:\n"
            "1️⃣ Вакансия → 2️⃣ Резюме → 3️⃣ Готово!",
            parse_mode='HTML'
        )
    
    application.add_handler(CommandHandler("help", help_handler))
    
    logger.info("🚀 Бот Сопровод v4.0 запущен! Простой поток: вакансия → резюме → письмо")
    
    # Запускаем бота
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main() 