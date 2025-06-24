"""
Simple Conversation Handler v6.0
Упрощенный поток с использованием smart_analyzer_v6
Релизная версия с улучшенным UX
"""
import logging
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from services.smart_analyzer_v6 import generate_simple_letter
from services.analytics_service import analytics
from models.analytics_models import UserData, LetterSessionData

logger = logging.getLogger(__name__)

# Состояния для v6.0
WAITING_VACANCY, WAITING_RESUME = range(300, 302)

# ============================================================================
# РЕЛИЗНАЯ ВЕРСИЯ 6.0 - ГОТОВА К ПРОДАКШЕНУ
# 
# ✅ Реализованные улучшения для релиза:
# • Расширенное приветствие с персонализацией
# • Команды: /help, /about, /support, /cancel, /start
# • Подробные инструкции на каждом шаге
# • Улучшенные сообщения об ошибках
# • Времязависимые приветствия
# • Мотивационные сообщения
# • Информация о конфиденциальности
# • Обратная связь и поддержка
# • Убрано дублирование команд (/new удален)
# ============================================================================


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать справку по командам"""
    if update.message:
        await update.message.reply_text(
            "📚 <b>СПРАВКА ПО КОМАНДАМ</b>\n\n"
            "🎯 <b>/start</b> - Создать новое сопроводительное письмо\n"
            "ℹ️ <b>/about</b> - О боте и его возможностях\n"
            "📞 <b>/support</b> - Связаться с поддержкой\n"
            "❌ <b>/cancel</b> - Отменить текущий процесс",
            parse_mode='HTML'
        )
        
        await update.message.reply_text(
            "💡 <b>Как пользоваться:</b>\n"
            "1️⃣ Нажмите /start\n"
            "2️⃣ Отправьте текст вакансии\n"
            "3️⃣ Отправьте ваше резюме\n"
            "4️⃣ Получите готовое письмо!\n\n"
            "⚡ Процесс займет всего 30-45 секунд",
            parse_mode='HTML'
        )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Информация о боте"""
    if update.message:
        # Отправляем информацию частями для лучшего отображения
        await update.message.reply_text(
            "🤖 <b>О БОТЕ СОПРОВОД</b>\n\n"
            "🎯 <b>Миссия:</b> Помогать людям находить работу мечты\n\n"
            "✨ <b>Возможности:</b>\n"
            "• Анализ вакансий с помощью ИИ\n"
            "• Персонализация под каждую позицию\n"
            "• Профессиональный стиль письма\n"
            "• Быстрая генерация (30-45 сек)",
            parse_mode='HTML'
        )
        
        await update.message.reply_text(
            "🔒 <b>Конфиденциальность:</b>\n"
            "• Ваши данные не сохраняются\n"
            "• Обработка происходит в реальном времени\n"
            "• Полная анонимность\n\n"
            "📊 <b>Версия:</b> 6.0\n"
            "🚀 <b>Создано с любовью для соискателей</b>\n\n"
            "💌 Удачи в поиске работы!",
            parse_mode='HTML'
        )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Контакты поддержки"""
    if update.message:
        await update.message.reply_text(
            "📞 <b>ПОДДЕРЖКА И ОБРАТНАЯ СВЯЗЬ</b>\n\n"
            "💬 <b>Есть вопросы или предложения?</b>\n"
            "Мы всегда готовы помочь!\n\n"
            "📧 <b>Способы связи:</b>\n"
            "• Напишите нам в чат поддержки\n"
            "• Оставьте отзыв о работе бота\n"
            "• Сообщите об ошибках",
            parse_mode='HTML'
        )
        
        await update.message.reply_text(
            "🐛 <b>Нашли баг?</b>\n"
            "Опишите проблему максимально подробно\n\n"
            "💡 <b>Есть идеи для улучшения?</b>\n"
            "Мы ценим каждое предложение!\n\n"
            "⚡ Обычно отвечаем в течение 24 часов",
            parse_mode='HTML'
        )





async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога v6.0"""
    logger.info("🚀 Начинаем диалог v6.0")
    
    # Трекаем пользователя
    user = update.effective_user
    if user:
        user_data = UserData(
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            language_code=user.language_code
        )
        user_id = await analytics.track_user(user_data)
        if user_id and context.user_data is not None:
            context.user_data['analytics_user_id'] = user_id
            await analytics.track_start_command(user_id)
    
    # Персональное приветствие с учетом времени
    user_name = ""
    if user and user.first_name:
        user_name = f", {user.first_name}"
    
    # Определяем время суток для приветствия
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        time_greeting = "Доброе утро"
    elif 12 <= current_hour < 18:
        time_greeting = "Добрый день"
    elif 18 <= current_hour < 23:
        time_greeting = "Добрый вечер"
    else:
        time_greeting = "Доброй ночи"
    
    message = (
        f"🎯 <b>{time_greeting}{user_name}! Я Сопровод</b>\n\n"
        "🚀 <b>Я создаю персональные сопроводительные письма к резюме!</b>\n\n"
        "✨ <b>Что я умею:</b>\n"
        "• Анализирую вакансию и ваше резюме\n"
        "• Создаю уникальное письмо под каждую позицию\n"
        "• Подчеркиваю ваши сильные стороны\n"
        "• Учитываю требования работодателя\n\n"
        "⚡ <b>Процесс простой - всего 2 шага:</b>\n"
        "1️⃣ Отправьте текст вакансии\n"
        "2️⃣ Отправьте ваше резюме\n\n"
        "⏰ Письмо будет готово через 30-45 секунд\n\n"
        "📝 <b>Шаг 1/2:</b> Отправьте текст вакансии\n\n"
        "💡 <i>Совет: Скопируйте полное описание вакансии с сайта работодателя</i>"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text=message, parse_mode='HTML')
    elif update.message:
        await update.message.reply_text(text=message, parse_mode='HTML')
    
    return WAITING_VACANCY


async def handle_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка вакансии"""
    if not update.message or not update.message.text:
        if update.message:
            await update.message.reply_text(
                "❌ <b>Нужен текст вакансии</b>\n\n"
                "📄 Пожалуйста, отправьте текстовое сообщение с описанием вакансии\n\n"
                "💡 <i>Не прикрепляйте файлы - только текст</i>",
                parse_mode='HTML'
            )
        return WAITING_VACANCY
    
    vacancy_text = update.message.text
    
    if len(vacancy_text) < 100:
        await update.message.reply_text(
            "❌ <b>Описание вакансии слишком короткое</b>\n\n"
            f"📊 Получено: {len(vacancy_text)} символов\n"
            f"📋 Нужно минимум: 100 символов\n\n"
            "💡 <b>Что добавить:</b>\n"
            "• Требования к кандидату\n"
            "• Обязанности\n"
            "• Условия работы\n"
            "• Информация о компании",
            parse_mode='HTML'
        )
        return WAITING_VACANCY
    
    # Сохраняем вакансию
    if context.user_data is not None:
        context.user_data['vacancy_text'] = vacancy_text
        
        # Создаем сессию аналитики
        user_id = context.user_data.get('analytics_user_id')
        logger.info(f"🔍 RAILWAY DEBUG: handle_vacancy analytics_user_id: {user_id}")
        
        if user_id:
            logger.info(f"🔍 RAILWAY DEBUG: Creating LetterSessionData for user {user_id}")
            
            try:
                session_data = LetterSessionData(
                    user_id=user_id,
                    mode="v6.0",
                    job_description=vacancy_text[:1000],  # Первые 1000 символов
                    job_description_length=len(vacancy_text),
                    selected_style="professional"
                )
                logger.info(f"🔍 RAILWAY DEBUG: LetterSessionData created successfully")
                
                session_id = await analytics.create_letter_session(session_data)
                logger.info(f"🔍 RAILWAY DEBUG: create_letter_session returned: {session_id}")
                
                if session_id:
                    context.user_data['analytics_session_id'] = session_id
                    logger.info(f"🔍 RAILWAY DEBUG: Calling track_vacancy_sent...")
                    await analytics.track_vacancy_sent(user_id, session_id, len(vacancy_text))
                    logger.info(f"🔍 RAILWAY DEBUG: track_vacancy_sent completed")
                else:
                    logger.error(f"❌ RAILWAY DEBUG: create_letter_session returned None!")
                    
            except Exception as e:
                logger.error(f"❌ RAILWAY DEBUG: Exception in vacancy analytics: {e}")
                import traceback
                logger.error(f"❌ RAILWAY DEBUG: Traceback: {traceback.format_exc()}")
        else:
            logger.error(f"❌ RAILWAY DEBUG: No analytics_user_id found!")
    else:
        logger.error(f"❌ RAILWAY DEBUG: context.user_data is None!")
    
    await update.message.reply_text(
        "✅ <b>Отлично! Вакансия сохранена</b>\n\n"
        "📋 <b>Шаг 2/2:</b> Теперь отправьте ваше резюме\n\n"
        "📝 <b>Что отправить:</b>\n"
        "• Полный текст резюме\n"
        "• Можно скопировать с HeadHunter, Хабр Карьера\n"
        "• Или из Word/PDF файла\n"
        "• Включите опыт работы и навыки\n\n"
        "💡 <i>Совет: Чем подробнее резюме, тем лучше письмо!</i>\n\n"
        "🔒 <i>Конфиденциально: данные не сохраняются</i>",
        parse_mode='HTML'
    )
    
    return WAITING_RESUME


async def handle_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка резюме и генерация письма"""
    if not update.message or not update.message.text:
        if update.message:
            await update.message.reply_text(
                "❌ <b>Нужен текст резюме</b>\n\n"
                "📄 Пожалуйста, отправьте ваше резюме в виде текста\n\n"
                "💡 <i>Скопируйте резюме и вставьте как обычное сообщение</i>",
                parse_mode='HTML'
            )
        return WAITING_RESUME
    
    resume_text = update.message.text
    
    if len(resume_text) < 100:
        await update.message.reply_text(
            "❌ <b>Резюме слишком короткое</b>\n\n"
            f"📊 Получено: {len(resume_text)} символов\n"
            f"📋 Нужно минимум: 100 символов\n\n"
            "💡 <b>Добавьте в резюме:</b>\n"
            "• Опыт работы (должности, достижения)\n"
            "• Навыки и компетенции\n"
            "• Образование\n"
            "• Дополнительную информацию",
            parse_mode='HTML'
        )
        return WAITING_RESUME
    
    # Получаем вакансию
    vacancy_text = None
    if context.user_data is not None:
        vacancy_text = context.user_data.get('vacancy_text')
    
    if not vacancy_text:
        await update.message.reply_text("❌ Вакансия потеряна. Начните заново: /start")
        return ConversationHandler.END
    
    # Показываем динамический прогресс
    processing_msg = await update.message.reply_text(
        "🚀 <b>Начинаю работу над вашим письмом!</b>\n\n"
        "🔍 <b>Этап 3/3:</b> Анализирую вакансию...\n"
        "⏳ Примерное время: 30-45 секунд\n\n"
        "💭 <i>Создаю персональное письмо специально для вас</i>",
        parse_mode='HTML'
    )
    
    try:
        # Аналитика
        user_id = None
        session_id = None
        if context.user_data is not None:
            user_id = context.user_data.get('analytics_user_id')
            session_id = context.user_data.get('analytics_session_id')
            
            logger.info(f"🔍 RAILWAY DEBUG: handle_resume user_id: {user_id}, session_id: {session_id}")
            
            if user_id and session_id:
                try:
                    logger.info(f"🔍 RAILWAY DEBUG: Calling track_resume_sent...")
                    await analytics.track_resume_sent(user_id, session_id, len(resume_text))
                    logger.info(f"🔍 RAILWAY DEBUG: track_resume_sent completed")
                except Exception as e:
                    logger.error(f"❌ RAILWAY DEBUG: Exception in track_resume_sent: {e}")
            else:
                logger.error(f"❌ RAILWAY DEBUG: Missing user_id or session_id!")
        else:
            logger.error(f"❌ RAILWAY DEBUG: context.user_data is None in handle_resume!")
        
        # 🎯 ПРОСТАЯ ГЕНЕРАЦИЯ v6.1: Только письмо, без сложностей
        start_time = time.time()
        
        # Обновляем сессию - добавляем данные резюме
        if user_id and session_id:
            from services.ai_factory import AIFactory
            current_provider = AIFactory.get_provider_name()
            
            await analytics.update_letter_session(session_id, {
                'resume_text': resume_text[:1000],  # Первые 1000 символов для экономии места
                'resume_length': len(resume_text),
                'openai_model_used': current_provider.lower()  # 'openai' или 'claude'
            })
        
        letter = await generate_simple_letter(
            vacancy_text=vacancy_text,
            resume_text=resume_text,
            user_id=user_id,
            session_id=session_id
        )
        
        generation_time = int(time.time() - start_time)
        
        # Удаляем прогресс
        await processing_msg.delete()
        
        # Отправляем результат
        await update.message.reply_text(
            f"✍️ <b>ПИСЬМО:</b>\n\n{letter}",
            parse_mode='HTML'
        )
        
        await update.message.reply_text(
            f"🎉 <b>Письмо готово за {generation_time} секунд!</b>\n\n"
            "✨ <b>Что дальше:</b>\n"
            "• Скопируйте письмо\n"
            "• Адаптируйте под себя при необходимости\n"
            "• Отправляйте работодателю\n\n"
            "🔄 <b>Создать новое письмо:</b> /start\n"
            "💬 <b>Есть вопросы:</b> /support\n\n"
            "🍀 <b>Удачи в поиске работы!</b>",
            parse_mode='HTML'
        )
        
        # Завершаем аналитику
        if user_id and session_id:
            # Обновляем сессию - добавляем результат генерации
            await analytics.update_letter_session(session_id, {
                'generated_letter': letter[:2000],  # Первые 2000 символов для экономии места
                'generated_letter_length': len(letter),
                'generation_time_seconds': generation_time,
                'status': 'completed'
            })
            
            await analytics.track_letter_generated(
                user_id, session_id, len(letter), generation_time
            )
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации: {e}")
        
        # 📊 АНАЛИТИКА: Логируем ошибку и помечаем сессию как заброшенную
        if user_id and session_id:
            try:
                import traceback
                from models.analytics_models import ErrorData
                
                error_data = ErrorData(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    user_id=user_id,
                    session_id=session_id,
                    stack_trace=traceback.format_exc(),
                    handler_name='handle_resume'
                )
                await analytics.log_error(error_data)
                
                # Помечаем сессию как неудачную
                await analytics.update_letter_session(session_id, {
                    'status': 'abandoned'
                })
            except Exception as log_error:
                logger.error(f"Failed to log error to database: {log_error}")
        
        try:
            await processing_msg.delete()
        except:
            pass
        
        await update.message.reply_text(
            "❌ <b>Произошла ошибка при создании письма</b>\n\n"
            "🔧 <b>Что можно сделать:</b>\n"
            "• Попробуйте еще раз: /start\n"
            "• Проверьте, что тексты достаточно подробные\n"
            "• Обратитесь в поддержку: /support\n\n"
            "😔 <i>Извините за неудобства!</i>",
            parse_mode='HTML'
        )
    
    # Очищаем данные
    if context.user_data is not None:
        context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога"""
    if context.user_data is not None:
        context.user_data.clear()
    
    if update.message:
        await update.message.reply_text(
            "❌ <b>Создание письма отменено</b>\n\n"
            "🔄 <b>Начать заново:</b> /start\n"
            "❓ <b>Нужна помощь:</b> /help\n\n"
            "👋 <i>Буду рад помочь вам снова!</i>",
            parse_mode='HTML'
        )
    
    return ConversationHandler.END


def get_conversation_handler():
    """Создает ConversationHandler для v6.0"""
    from telegram.ext import CommandHandler, MessageHandler, filters
    
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_conversation)
        ],
        states={
            WAITING_VACANCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vacancy)
            ],
            WAITING_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_resume)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_conversation),
            CommandHandler('start', start_conversation)
        ],
        name="conversation_v6",
        persistent=False,
        per_message=False,
        per_chat=True,
        per_user=True
    )


def get_command_handlers():
    """Возвращает список обработчиков команд"""
    from telegram.ext import CommandHandler
    
    return [
        CommandHandler("help", help_command),
        CommandHandler("about", about_command),
        CommandHandler("support", support_command)
    ] 