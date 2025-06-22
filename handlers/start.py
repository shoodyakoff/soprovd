"""
Обработчик команды /start
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /start - приветствие и начало разговора
    """
    if not update.effective_user or not update.message:
        from config import WAITING_JOB_DESCRIPTION
        return WAITING_JOB_DESCRIPTION
        
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    logger.info(f"[USER {user_id}] (@{username}) Запустил бота командой /start")
    
    welcome_message = (
        "Привет! Я помогу тебе написать заметное сопроводительное письмо "
        "под конкретную вакансию. Готов? Тогда поехали 👇\n\n"
        "Для начала, пришли мне описание вакансии текстом."
    )
    
    await update.message.reply_text(welcome_message)
    
    logger.info(f"[USER {user_id}] Приветственное сообщение отправлено, ожидание описания вакансии")
    
    # Переходим к состоянию ожидания описания вакансии
    from config import WAITING_JOB_DESCRIPTION
    return WAITING_JOB_DESCRIPTION 