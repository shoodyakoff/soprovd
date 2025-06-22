"""
Обработчик callback-кнопок (inline клавиатуры)
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    STYLE_NEUTRAL, STYLE_BOLD, STYLE_FORMAL,
    WAITING_JOB_DESCRIPTION
)
from handlers.personalized_conversation import WAITING_JOB_DESCRIPTION as PERS_WAITING_JOB

# Настройка логирования
logger = logging.getLogger(__name__)

async def handle_style_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик выбора стиля через inline-кнопки
    """
    if not update.callback_query or not update.effective_user or not context.user_data:
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback
    
    callback_data = query.data
    
    # Определяем выбранный стиль
    style_mapping = {
        "style_neutral": STYLE_NEUTRAL,
        "style_bold": STYLE_BOLD,
        "style_formal": STYLE_FORMAL
    }
    
    style_names = {
        "style_neutral": "Нейтральный",
        "style_bold": "Смелый", 
        "style_formal": "Формальный"
    }
    
    selected_style = style_mapping.get(callback_data) if callback_data else None
    style_name = style_names.get(callback_data, "Неизвестный") if callback_data else "Неизвестный"
    
    if selected_style and query.message:
        # Сохраняем выбранный стиль
        context.user_data['style'] = selected_style
        
        logger.info(f"Пользователь {update.effective_user.id} выбрал стиль: {style_name}")
        
        # Редактируем сообщение, убирая кнопки
        await query.edit_message_text(
            f"Понял. И последний штрих: какой стиль письма ты предпочитаешь?\n\n"
            f"✅ Выбран: {style_name}"
        )
        
        # Отправляем сообщение о начале генерации
        await query.message.reply_text("Спасибо! Всё получил. Генерирую письмо...")
        
        # Генерируем письмо напрямую здесь
        from handlers.conversation import generate_letter_content
        return await generate_letter_content(query.message, context, update.effective_user.id)
    
    else:
        if query.message:
            await query.edit_message_text(
                "Произошла ошибка при выборе стиля. Попробуй начать заново командой /start"
            )
        
        # Очищаем данные пользователя
        if context.user_data:
            context.user_data.clear()
        
        return ConversationHandler.END


async def handle_mode_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик выбора режима работы бота
    """
    logger.info(f"🔥 handle_mode_choice вызван! update: {update}, callback_query: {update.callback_query if update else None}")
    
    if not update.callback_query or not update.effective_user:
        logger.error("❌ handle_mode_choice: Missing callback_query or effective_user")
        return ConversationHandler.END
        
    query = update.callback_query
    logger.info(f"🔥 Отвечаем на callback query...")
    await query.answer()
    
    choice = query.data
    logger.info(f"🔥 User {update.effective_user.id} chose mode: {choice}")
    
    if choice == "mode_classic":
        # Классический режим
        logger.info(f"🔥 Editing message for classic mode...")
        await query.edit_message_text(
            "🤖 <b>Быстрый режим выбран!</b>\n\n"
            "Для начала, пришлите мне описание вакансии текстом.",
            parse_mode='HTML'
        )
        
        logger.info(f"🔥 User {update.effective_user.id} selected classic mode, returning state: {WAITING_JOB_DESCRIPTION}")
        
        # Переходим к классическому диалогу
        return WAITING_JOB_DESCRIPTION
        
    elif choice == "mode_personalized":
        # Персонализированный режим
        logger.info(f"🔥 Editing message for personalized mode...")
        await query.edit_message_text(
            "🎯 <b>Персонализированный генератор писем</b>\n\n"
            "Я проанализирую вашу профессию и уровень, чтобы подобрать идеальный стиль письма!\n\n"
            "<b>Как это работает:</b>\n"
            "1️⃣ Вы присылаете описание вакансии\n"
            "2️⃣ Затем ваше резюме\n"
            "3️⃣ Я анализирую и предлагаю стиль\n"
            "4️⃣ Генерирую персонализированное письмо\n\n"
            "Готовы? Пришлите описание вакансии 👇",
            parse_mode='HTML'
        )
        
        logger.info(f"🔥 User {update.effective_user.id} selected personalized mode, returning state: {PERS_WAITING_JOB}")
        
        # Переходим к персонализированному ожиданию описания вакансии
        return PERS_WAITING_JOB
    
    elif choice == "mode_v3":
        # v3.0 режим - НЕ обрабатываем здесь, пусть обрабатывает v3_conversation_handler
        logger.info(f"🚀 User {update.effective_user.id} выбрал v3.0 режим - передаем в v3_conversation_handler")
        # Возвращаем END, чтобы v3_conversation_handler мог перехватить
        return ConversationHandler.END
    
    else:
        await query.edit_message_text(
            "❌ Неизвестный режим. Попробуйте еще раз с /start"
        )
        return ConversationHandler.END 