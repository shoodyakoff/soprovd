"""
Обработчик callback-кнопок (inline клавиатуры)
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import STYLE_NEUTRAL, STYLE_BOLD, STYLE_FORMAL
from handlers.conversation import generate_letter

# Настройка логирования
logger = logging.getLogger(__name__)

async def handle_style_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик выбора стиля через inline-кнопки
    """
    if not update.callback_query or not update.effective_user or not context.user_data:
        from telegram.ext import ConversationHandler
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
        
        from telegram.ext import ConversationHandler
        return ConversationHandler.END 