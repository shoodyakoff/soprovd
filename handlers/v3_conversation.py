"""
Handler для v3.0 - умный анализ с человечной генерацией
Простой и эффективный подход без сложных моделей
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler
from services.smart_analyzer import analyze_and_generate
from utils.keyboards import get_main_menu

logger = logging.getLogger(__name__)

# Состояния v3.0 (уникальные, не пересекающиеся с основными)
V3_VACANCY_INPUT, V3_RESUME_INPUT, V3_STYLE_SELECT = range(100, 103)

# Стили письма
LETTER_STYLES = {
    "professional": "Профессиональный",
    "friendly": "Дружелюбный", 
    "creative": "Креативный",
    "formal": "Формальный",
    "startup": "Стартап-стиль"
}


async def start_v3_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало беседы v3.0"""
    logger.info("🚀 Начинаем v3.0 диалог")
    
    message = (
        "🎯 <b>Умный генератор v3.0</b>\n\n"
        "Новый подход к созданию сопроводительных писем:\n"
        "• Глубокий анализ через GPT\n"
        "• Человечный стиль без ИИ-штампов\n"
        "• Конкретные примеры и метрики\n\n"
        "📝 <b>Шаг 1/3:</b> Отправьте текст вакансии"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            parse_mode='HTML'
        )
    elif update.message:
        await update.message.reply_text(
            text=message,
            parse_mode='HTML'
        )
    
    return V3_VACANCY_INPUT


async def handle_vacancy_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода вакансии"""
    logger.info(f"🎯 handle_vacancy_input вызван! User: {update.effective_user.id if update.effective_user else 'unknown'}")
    
    if not update.message or not update.message.text:
        logger.warning("❌ handle_vacancy_input: Missing message or text")
        return V3_VACANCY_INPUT
    
    vacancy_text = update.message.text
    logger.info(f"📝 Получен текст вакансии: {len(vacancy_text)} символов")
    
    # Валидация
    if len(vacancy_text) < 50:
        await update.message.reply_text(
            "❌ Слишком короткий текст вакансии.\n"
            "Пожалуйста, скопируйте полное описание вакансии."
        )
        return V3_VACANCY_INPUT
    
    # Сохраняем в контекст
    context.user_data['vacancy_text'] = vacancy_text
    
    logger.info(f"📝 Получена вакансия: {len(vacancy_text)} символов")
    
    await update.message.reply_text(
        "✅ Вакансия сохранена!\n\n"
        "📋 <b>Шаг 2/3:</b> Теперь отправьте текст вашего резюме",
        parse_mode='HTML'
    )
    
    return V3_RESUME_INPUT


async def handle_resume_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода резюме"""
    logger.info(f"📋 handle_resume_input вызван! User: {update.effective_user.id if update.effective_user else 'unknown'}")
    
    if not update.message or not update.message.text:
        logger.warning("❌ handle_resume_input: Missing message or text")
        return V3_RESUME_INPUT
    
    resume_text = update.message.text
    logger.info(f"📋 Получен текст резюме: {len(resume_text)} символов")
    
    # Валидация
    if len(resume_text) < 50:
        await update.message.reply_text(
            "❌ Слишком короткий текст резюме.\n"
            "Пожалуйста, отправьте более подробную информацию о себе."
        )
        return V3_RESUME_INPUT
    
    # Сохраняем в контекст
    context.user_data['resume_text'] = resume_text
    
    logger.info(f"📋 Получено резюме: {len(resume_text)} символов")
    
    # Показываем выбор стиля
    keyboard = []
    for style_key, style_name in LETTER_STYLES.items():
        keyboard.append([InlineKeyboardButton(
            text=f"✨ {style_name}",
            callback_data=f"style_{style_key}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад к выбору режима",
        callback_data="back_to_main"
    )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ Резюме сохранено!\n\n"
        "🎨 <b>Шаг 3/3:</b> Выберите стиль письма:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    
    return V3_STYLE_SELECT


async def handle_style_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора стиля и генерация письма"""
    logger.info(f"🎨 handle_style_selection вызван! User: {update.effective_user.id if update.effective_user else 'unknown'}")
    
    if not update.callback_query:
        logger.warning("❌ handle_style_selection: Missing callback_query")
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    if not query.data:
        logger.warning("❌ handle_style_selection: Missing query.data")
        return ConversationHandler.END
    
    if query.data == "back_to_main":
        from handlers.start import show_main_menu
        await show_main_menu(update, context)
        return ConversationHandler.END
    
    # Извлекаем стиль
    style_key = query.data.replace("style_", "")
    style_name = LETTER_STYLES.get(style_key, "Профессиональный")
    
    logger.info(f"🎨 Выбран стиль: {style_name}")
    
    # Получаем данные из контекста
    if not context.user_data:
        await query.edit_message_text(
            "❌ Ошибка: данные потеряны. Начните заново.",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    
    vacancy_text = context.user_data.get('vacancy_text')
    resume_text = context.user_data.get('resume_text')
    
    if not vacancy_text or not resume_text:
        await query.edit_message_text(
            "❌ Ошибка: данные потеряны. Начните заново.",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
    
    # Показываем что генерируем
    processing_msg = await query.edit_message_text(
        f"🔄 Генерирую письмо в стиле '{style_name}'...\n\n"
        "⏳ Это может занять 15-30 секунд\n"
        "🧠 Провожу глубокий анализ через GPT\n"
        "✍️ Создаю человечный текст\n"
        "🔧 Убираю ИИ-штампы"
    )
    
    try:
        # Запускаем полный флоу v3.0
        logger.info("🚀 Запускаю analyze_and_generate...")
        
        cover_letter = await analyze_and_generate(
            vacancy_text=vacancy_text,
            resume_text=resume_text,
            style=style_key
        )
        
        # Отправляем результат
        result_message = (
            f"🎉 <b>Готово!</b> Письмо в стиле '{style_name}':\n\n"
            f"<code>{cover_letter}</code>\n\n"
            "💡 <i>Письмо создано с помощью умного анализа v3.0</i>"
        )
        
        # Проверяем длину сообщения (лимит Телеграм ~4096 символов)
        if len(result_message) > 4000:
            # Разбиваем на части
            await query.edit_message_text(
                f"🎉 <b>Готово!</b> Письмо в стиле '{style_name}':",
                parse_mode='HTML'
            )
            
            if update.effective_chat:
                await update.effective_chat.send_message(
                    text=f"<code>{cover_letter}</code>",
                    parse_mode='HTML'
                )
                
                await update.effective_chat.send_message(
                    text="💡 <i>Письмо создано с помощью умного анализа v3.0</i>",
                    parse_mode='HTML',
                    reply_markup=get_main_menu()
                )
        else:
            await query.edit_message_text(
                text=result_message,
                parse_mode='HTML',
                reply_markup=get_main_menu()
            )
        
        logger.info("✅ Письмо успешно сгенерировано и отправлено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации письма: {e}")
        
        await query.edit_message_text(
            "❌ <b>Ошибка генерации</b>\n\n"
            "Что-то пошло не так. Попробуйте еще раз.\n"
            f"Ошибка: {str(e)[:100]}...",
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )
    
    # Очищаем данные пользователя
    if context.user_data:
        context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_v3_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога v3.0"""
    logger.info("❌ Диалог v3.0 отменен пользователем")
    
    if context.user_data:
        context.user_data.clear()
    
    from handlers.start import show_main_menu
    await show_main_menu(update, context)
    
    return ConversationHandler.END


def get_v3_conversation_handler():
    """Создает ConversationHandler для v3.0"""
    from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_v3_conversation, pattern='^mode_v3$')
        ],
        states={
            V3_VACANCY_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vacancy_input)
            ],
            V3_RESUME_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_resume_input)
            ],
            V3_STYLE_SELECT: [
                CallbackQueryHandler(handle_style_selection, pattern='^style_'),
                CallbackQueryHandler(handle_style_selection, pattern='^back_to_main$')
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_v3_conversation),
            CommandHandler('start', cancel_v3_conversation)
        ],
        name="v3_conversation",
        persistent=False,
        per_message=False,  # False для работы с MessageHandler
        per_chat=True,
        per_user=True
    ) 