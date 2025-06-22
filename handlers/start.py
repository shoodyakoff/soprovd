"""
Обработчик команды /start
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /start - приветствие и выбор режима
    """
    if not update.effective_user or not update.message:
        from config import WAITING_JOB_DESCRIPTION
        return WAITING_JOB_DESCRIPTION
        
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    logger.info(f"[USER {user_id}] (@{username}) Запустил бота командой /start")
    
    welcome_message = """🎯 <b>Добро пожаловать в LetterGenius!</b>

Я помогу создать идеальное сопроводительное письмо под вашу вакансию.

<b>Выберите режим:</b>

🔥 <b>Умный генератор v3.0</b> - NEW!
Глубокий анализ через GPT, человечный стиль без ИИ-штампов

🎯 <b>Персонализированный режим</b>
Анализирую вашу профессию и уровень, подбираю стиль письма

⚡ <b>Классический режим</b>
Просто, быстро, универсально

Что выбираете?"""
    
    # Создаем кнопки выбора режима
    from utils.keyboards import get_main_menu
    reply_markup = get_main_menu()
    
    await update.message.reply_text(
        welcome_message, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    logger.info(f"[USER {user_id}] Меню выбора режима отправлено")
    
    # Переходим к состоянию выбора режима
    from config import CHOOSING_MODE
    return CHOOSING_MODE


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает главное меню выбора режима
    """
    message = """🎯 <b>Выберите режим генерации:</b>

🔥 <b>Умный генератор v3.0</b> - NEW!
Глубокий анализ через GPT, человечный стиль без ИИ-штампов

🎯 <b>Персонализированный режим</b>
Анализирую вашу профессию и уровень, подбираю стиль письма

⚡ <b>Классический режим</b>
Просто, быстро, универсально"""
    
    from utils.keyboards import get_main_menu
    reply_markup = get_main_menu()
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    elif update.message:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML',
            reply_markup=reply_markup
        ) 