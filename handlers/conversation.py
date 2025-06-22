"""
Основной флоу сбора данных для генерации письма
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    WAITING_JOB_DESCRIPTION, 
    WAITING_RESUME, 
    WAITING_STYLE_CHOICE,
    GENERATING
)
from utils.keyboards import get_style_keyboard
from services.openai_service import OpenAIService

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализируем сервис OpenAI
openai_service = OpenAIService()

async def handle_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик получения описания вакансии
    """
    if not update.effective_user or not update.message:
        return WAITING_JOB_DESCRIPTION
        
    user_id = update.effective_user.id
    job_description = update.message.text
    
    logger.info(f"[USER {user_id}] СОСТОЯНИЕ: WAITING_JOB_DESCRIPTION. Получен текст описания вакансии, длина: {len(job_description) if job_description else 0}")
    
    if not job_description or len(job_description.strip()) < 10:
        logger.warning(f"[USER {user_id}] Слишком короткое описание вакансии")
        await update.message.reply_text(
            "Пожалуйста, пришли более подробное описание вакансии (минимум 10 символов)."
        )
        return WAITING_JOB_DESCRIPTION
    
    # Проверяем, не содержит ли сообщение сразу оба блока (описание + резюме)
    if len(job_description) > 2000:
        logger.warning(f"[USER {user_id}] Очень длинное сообщение ({len(job_description)} символов). Возможно, пользователь прислал все сразу.")
        await update.message.reply_text(
            "Получил очень длинное сообщение! Пожалуйста, пришли описание вакансии и резюме отдельными сообщениями для лучшей обработки.\n\n"
            "Сначала пришли только описание вакансии:"
        )
        return WAITING_JOB_DESCRIPTION
    
    # Сохраняем описание вакансии в контексте
    if context.user_data is not None:
        context.user_data['job_description'] = job_description.strip()
        # Очищаем возможные старые данные
        context.user_data.pop('resume', None)
        context.user_data.pop('style', None)
    
    logger.info(f"[USER {user_id}] Описание вакансии сохранено, переход к получению резюме")
    
    await update.message.reply_text(
        "Отлично! Теперь пришли мне твоё резюме (текстом). "
        "Можешь скопировать и вставить его сюда."
    )
    
    return WAITING_RESUME

async def handle_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик получения резюме
    """
    if not update.effective_user or not update.message:
        return WAITING_RESUME
        
    user_id = update.effective_user.id
    resume = update.message.text
    
    logger.info(f"[USER {user_id}] СОСТОЯНИЕ: WAITING_RESUME. Получен текст резюме, длина: {len(resume) if resume else 0}")
    
    # Проверяем, что у нас уже есть описание вакансии
    if not context.user_data or not context.user_data.get('job_description'):
        logger.error(f"[USER {user_id}] Получено резюме, но нет описания вакансии! Что-то пошло не так.")
        await update.message.reply_text(
            "Произошла ошибка в последовательности. Давай начнем заново с /start"
        )
        if context.user_data:
            context.user_data.clear()
        return ConversationHandler.END
    
    if not resume or len(resume.strip()) < 20:
        logger.warning(f"[USER {user_id}] Слишком короткое резюме")
        await update.message.reply_text(
            "Пожалуйста, пришли более подробное резюме (минимум 20 символов)."
        )
        return WAITING_RESUME
    
    # Сохраняем резюме в контексте
    if context.user_data is not None:
        context.user_data['resume'] = resume.strip()
    
    logger.info(f"[USER {user_id}] Резюме сохранено, отправляю клавиатуру выбора стиля")
    
    # Отправляем клавиатуру для выбора стиля
    await update.message.reply_text(
        "Понял. И последний штрих: какой стиль письма ты предпочитаешь?",
        reply_markup=get_style_keyboard()
    )
    
    return WAITING_STYLE_CHOICE

async def handle_text_in_style_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик текстовых сообщений во время ожидания выбора стиля
    """
    if not update.message:
        return WAITING_STYLE_CHOICE
        
    await update.message.reply_text(
        "Пожалуйста, выбери стиль, нажав на одну из кнопок выше."
    )
    
    return WAITING_STYLE_CHOICE

async def generate_letter_content(message, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> int:
    """
    Генерирует сопроводительное письмо (отдельная функция для использования из callback)
    """
    if not message or not context.user_data:
        return ConversationHandler.END
    
    # Получаем данные из контекста
    job_description = context.user_data.get('job_description', '')
    resume = context.user_data.get('resume', '')
    style = context.user_data.get('style', 'neutral')
    
    # Проверяем, что все данные есть
    if not job_description or not resume or not style:
        await message.reply_text(
            "Извини, не хватает данных. Попробуй начать заново командой /start"
        )
        if context.user_data:
            context.user_data.clear()
        return ConversationHandler.END
    
    logger.info(f"Начинаем генерацию для пользователя {user_id}")
    
    try:
        # Генерируем письмо
        cover_letter = await openai_service.generate_cover_letter(
            job_description=job_description,
            resume=resume,
            style=style
        )
        
        if cover_letter:
            # Отправляем сгенерированное письмо
            await message.reply_text(cover_letter)
            await message.reply_text(
                "Готово! Вот твоё письмо 👇. Надеюсь, оно поможет тебе получить желаемую работу!\n\n"
                "Чтобы создать новое письмо, используй команду /start"
            )
        else:
            await message.reply_text(
                "Извини, возникли технические проблемы. "
                "Попробуй начать заново командой /start"
            )
    
    except Exception as e:
        logger.error(f"Ошибка при генерации письма: {e}")
        await message.reply_text(
            "Извини, возникли технические проблемы. "
            "Попробуй начать заново командой /start"
        )
    
    # Очищаем данные пользователя
    if context.user_data:
        context.user_data.clear()
    
    return ConversationHandler.END

async def generate_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Генерирует сопроводительное письмо
    """
    if not update.message or not update.effective_user or not context.user_data:
        return ConversationHandler.END
    
    # Отправляем сообщение о начале генерации
    await update.message.reply_text("Спасибо! Всё получил. Генерирую письмо...")
    
    # Используем общую функцию генерации
    return await generate_letter_content(update.message, context, update.effective_user.id)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик отмены разговора
    """
    if not update.message:
        return ConversationHandler.END
        
    await update.message.reply_text(
        "Создание письма отменено. Чтобы начать заново, используй команду /start"
    )
    
    # Очищаем данные пользователя
    if context.user_data:
        context.user_data.clear()
    
    return ConversationHandler.END 