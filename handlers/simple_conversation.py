"""
Simple Conversation Handler v4.0
Упрощенный поток: вакансия → резюме → письмо
Сохраняет всю мощь v3.0 анализа, но убирает сложности выбора
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# Уникальные состояния для v4.0 (не пересекаются с существующими)
SIMPLE_WAITING_VACANCY, SIMPLE_WAITING_RESUME = range(200, 202)


async def start_simple_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало упрощенного диалога v4.0"""
    logger.info("🚀 Начинаем простой диалог v4.0")
    
    message = (
        "🎯 <b>Добро пожаловать в Сопровод!</b>\n\n"
        "Я создам для вас профессиональное сопроводительное письмо за 30 секунд.\n\n"
        "<b>Как это работает:</b>\n"
        "• Глубокий анализ вакансии и резюме через GPT\n"
        "• Человечный стиль без ИИ-штампов\n"
        "• Конкретные примеры из вашего опыта\n\n"
        "📝 <b>Шаг 1/2:</b> Отправьте текст вакансии"
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
    
    return SIMPLE_WAITING_VACANCY


async def handle_vacancy_simple(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода вакансии"""
    logger.info(f"📝 handle_vacancy_simple: User {update.effective_user.id if update.effective_user else 'unknown'}")
    
    if not update.message or not update.message.text:
        logger.warning("❌ Missing message or text")
        if update.message:
            await update.message.reply_text(
                "❌ Пожалуйста, отправьте текст вакансии\n\n"
                "Я работаю только с текстовым форматом.\n"
                "Скопируйте описание вакансии и отправьте его текстом.\n\n"
                "Файлы, картинки и голосовые сообщения не поддерживаются."
            )
        return SIMPLE_WAITING_VACANCY
    
    vacancy_text = update.message.text
    logger.info(f"📝 Получен текст вакансии: {len(vacancy_text)} символов")
    
    # Валидация длины
    if len(vacancy_text) < 100:
        await update.message.reply_text(
            "❌ Слишком короткое описание вакансии\n\n"
            "Пожалуйста, отправьте полное описание вакансии\n"
            "(минимум 100 символов для качественного анализа)."
        )
        return SIMPLE_WAITING_VACANCY
    
    # Сохраняем в контекст
    if context.user_data is not None:
        context.user_data['vacancy_text'] = vacancy_text
    
    await update.message.reply_text(
        "✅ Вакансия сохранена!\n\n"
        "📋 <b>Шаг 2/2:</b> Теперь отправьте текст вашего резюме",
        parse_mode='HTML'
    )
    
    return SIMPLE_WAITING_RESUME


async def handle_resume_simple(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода резюме и генерация письма"""
    logger.info(f"📋 handle_resume_simple: User {update.effective_user.id if update.effective_user else 'unknown'}")
    
    if not update.message or not update.message.text:
        logger.warning("❌ Missing message or text")
        if update.message:
            await update.message.reply_text(
                "❌ Пожалуйста, отправьте текст резюме\n\n"
                "Опишите свой опыт работы, навыки и достижения текстом.\n\n"
                "Файлы, голосовые и изображения не поддерживаются."
            )
        return SIMPLE_WAITING_RESUME
    
    resume_text = update.message.text
    logger.info(f"📋 Получен текст резюме: {len(resume_text)} символов")
    
    # Валидация длины
    if len(resume_text) < 100:
        await update.message.reply_text(
            "❌ Слишком короткое описание опыта\n\n"
            "Расскажите подробнее о себе: опыт работы, ключевые навыки,\n"
            "достижения (минимум 100 символов для качественного письма)."
        )
        return SIMPLE_WAITING_RESUME
    
    # Получаем вакансию из контекста
    vacancy_text = None
    if context.user_data is not None:
        vacancy_text = context.user_data.get('vacancy_text')
    
    if not vacancy_text:
        await update.message.reply_text(
            "❌ Ошибка: данные о вакансии потеряны.\n\n"
            "🔄 Начните заново: /start"
        )
        return ConversationHandler.END
    
    # Показываем процесс генерации
    processing_msg = await update.message.reply_text(
        "🔄 Создаю профессиональное письмо и анализ совпадений...\n\n"
        "⏳ Это займет 30-45 секунд\n"
        "🔍 Анализирую вакансию\n"
        "👤 Изучаю ваше резюме\n"
        "⚡ Ищу совпадения и преимущества\n"
        "✍️ Генерирую письмо и обоснование"
    )
    
    try:
        # Используем новый 4-этапный анализ
        logger.info("🚀 Запускаю новый 4-этапный анализ...")
        
        from services.smart_analyzer import analyze_and_generate_with_analysis
        
        result = await analyze_and_generate_with_analysis(
            vacancy_text=vacancy_text,
            resume_text=resume_text,
            style="professional"  # Фиксированный профессиональный стиль
        )
        
        # Удаляем сообщение о прогрессе
        await processing_msg.delete()
        
        # Отправляем письмо
        await update.message.reply_text(
            f"✍️ <b>СОПРОВОДИТЕЛЬНОЕ ПИСЬМО:</b>\n\n{result['letter']}",
            parse_mode='HTML'
        )
        
        # Отправляем анализ совпадений
        await update.message.reply_text(
            f"📊 <b>АНАЛИЗ СОВПАДЕНИЙ:</b>\n\n{result['analysis']}",
            parse_mode='HTML'
        )
        
        # Финальное сообщение
        await update.message.reply_text(
            "🎉 <b>Готово!</b> Письмо и анализ созданы.\n\n"
            "💡 Письмо создано с помощью нового 4-этапного анализа:\n"
            "• Структурированный анализ вакансии\n"
            "• Детальный анализ резюме\n"
            "• Точное сопоставление требований\n"
            "• Генерация на основе совпадений\n\n"
            "🔄 Чтобы создать письмо для новой вакансии, напишите /start",
            parse_mode='HTML'
        )
        
        logger.info("✅ Письмо и анализ успешно сгенерированы через новый 4-этапный флоу")
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации письма: {e}")
        
        try:
            await processing_msg.delete()
        except:
            pass  # Если сообщение уже удалено
        
        await update.message.reply_text(
            "❌ <b>Произошла ошибка при создании письма</b>\n\n"
            "Попробуйте еще раз или обратитесь в поддержку.\n\n"
            "🔄 Начать заново: /start",
            parse_mode='HTML'
        )
    
    # Очищаем данные пользователя
    if context.user_data is not None:
        context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_simple_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена простого диалога"""
    logger.info("❌ Простой диалог v4.0 отменен пользователем")
    
    if context.user_data is not None:
        context.user_data.clear()
    
    if update.message:
        await update.message.reply_text(
            "❌ Процесс отменен.\n\n"
            "🔄 Начать заново: /start"
        )
    
    return ConversationHandler.END


def get_simple_conversation_handler():
    """Создает ConversationHandler для v4.0 простого потока"""
    from telegram.ext import CommandHandler, MessageHandler, filters
    
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_simple_conversation)
        ],
        states={
            SIMPLE_WAITING_VACANCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vacancy_simple)
            ],
            SIMPLE_WAITING_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_resume_simple)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_simple_conversation),
            CommandHandler('start', start_simple_conversation)
        ],
        name="simple_conversation_v4",
        persistent=False,
        per_message=False,
        per_chat=True,
        per_user=True
    ) 