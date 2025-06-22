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

🤖 <b>Быстрый режим</b> - классический генератор
Просто, быстро, универсально

🎯 <b>Персонализированный режим</b> - NEW! 
Анализирую вашу профессию и уровень, подбираю стиль письма

Что выбираете?"""
    
    # Создаем кнопки выбора режима
    keyboard = [
        [InlineKeyboardButton("🤖 Быстрый режим", callback_data="mode_classic")],
        [InlineKeyboardButton("🎯 Персонализированный", callback_data="mode_personalized")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    logger.info(f"[USER {user_id}] Меню выбора режима отправлено")
    
    # Переходим к состоянию выбора режима
    from config import CHOOSING_MODE
    return CHOOSING_MODE 