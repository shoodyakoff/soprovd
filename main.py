"""
Главный файл Telegram-бота LetterGenius
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

from config import (
    TELEGRAM_BOT_TOKEN,
    WAITING_JOB_DESCRIPTION,
    WAITING_RESUME,
    WAITING_STYLE_CHOICE
)

from handlers.start import start
from handlers.conversation import (
    handle_job_description,
    handle_resume,
    handle_text_in_style_choice,
    cancel
)
from handlers.callback import handle_style_callback

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
    Основная функция запуска бота
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    # Настройка ConversationHandler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_JOB_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_job_description)
            ],
            WAITING_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_resume)
            ],
            WAITING_STYLE_CHOICE: [
                CallbackQueryHandler(handle_style_callback, pattern="^style_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_in_style_choice)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start)  # Позволяем начать заново в любой момент
        ],
        per_message=True,  # Важно! Отслеживаем состояние для каждого сообщения
        allow_reentry=True  # Позволяем начать заново
    )
    
    # Добавляем обработчики
    application.add_handler(conversation_handler)
    
    # Обработчик для всех остальных сообщений
    async def help_handler(update, context):
        await update.message.reply_text(
            "Для создания сопроводительного письма используй команду /start\n"
            "Для отмены текущего процесса используй команду /cancel"
        )
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, help_handler))
    
    logger.info("Бот LetterGenius запущен!")
    
    # Запускаем бота
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main() 