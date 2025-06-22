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
    CHOOSING_MODE,
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
from handlers.callback import handle_style_callback, handle_mode_choice
from handlers.personalized_conversation import (
    start_personalized,
    receive_job_description,
    receive_resume,
    handle_style_choice,
    cancel_personalized,
    WAITING_JOB_DESCRIPTION as PERS_WAITING_JOB,
    WAITING_RESUME as PERS_WAITING_RESUME,
    WAITING_STYLE_CONFIRMATION as PERS_WAITING_STYLE
)
from handlers.v3_conversation import get_v3_conversation_handler

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
    
    # Объединенный ConversationHandler для обоих режимов
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_MODE: [
                CallbackQueryHandler(handle_mode_choice, pattern="^mode_(classic|personalized|v3)$")
            ],
            WAITING_JOB_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_job_description)
            ],
            WAITING_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_resume)
            ],
            WAITING_STYLE_CHOICE: [
                CallbackQueryHandler(handle_style_callback, pattern="^style_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_in_style_choice)
            ],
            # Персонализированные состояния
            PERS_WAITING_JOB: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_job_description)
            ],
            PERS_WAITING_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_resume)
            ],
            PERS_WAITING_STYLE: [
                CallbackQueryHandler(handle_style_choice, pattern="^style_")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start)  # Позволяем начать заново в любой момент
        ],
        allow_reentry=True,  # Позволяем начать заново
        per_message=False,   # False для работы с MessageHandler
        per_chat=True,       # Один разговор на чат
        per_user=True        # Один разговор на пользователя
    )
    
    # Добавляем v3.0 conversation handler ПЕРВЫМ (приоритет)
    v3_handler = get_v3_conversation_handler()
    application.add_handler(v3_handler)
    logger.info("🚀 v3.0 ConversationHandler добавлен!")
    
    # Добавляем основной conversation handler
    application.add_handler(conversation_handler)
    logger.info(f"🔥 ConversationHandler добавлен! States: {list(conversation_handler.states.keys())}")
    
    # Добавляем общий обработчик для отладки
    async def debug_handler(update, context):
        if update.message and update.effective_user:
            logger.info(f"🔥 DEBUG: Получено сообщение от {update.effective_user.id}: '{update.message.text[:50]}...'")
            logger.info(f"🔥 DEBUG: Текущее состояние: {context.user_data.get('state', 'unknown') if context.user_data else 'no_user_data'}")
    
    application.add_handler(MessageHandler(filters.ALL, debug_handler), group=1)
    
    # Обработчик команды help
    async def help_handler(update, context):
        await update.message.reply_text(
            "📋 <b>Доступные команды:</b>\n\n"
            "🤖 /start - выбор режима работы\n"
            "🎯 /personalized - персонализированный режим\n"
            "❌ /cancel - отмена текущего процесса",
            parse_mode='HTML'
        )
    
    application.add_handler(CommandHandler("help", help_handler))
    
    logger.info("Бот LetterGenius запущен!")
    
    # Запускаем бота
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main() 