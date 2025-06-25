"""
Simple Conversation Handler v7.2
Упрощенная система обратной связи: только лайки/дизлайки БЕЗ комментариев
Релизная версия с улучшенным UX
"""
import logging
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.smart_analyzer import generate_simple_letter, generate_improved_letter
from services.analytics_service import analytics
from services.subscription_service import subscription_service
from services.feedback_service import feedback_service
from services.acquisition_service import acquisition_service
from models.analytics_models import UserData, LetterSessionData
from models.feedback_models import LetterFeedbackData, LetterIterationImprovement
from utils.validators import InputValidator, ValidationMiddleware
from utils.keyboards import get_feedback_keyboard, get_iteration_keyboard, get_final_letter_keyboard, get_retry_keyboard, get_start_work_keyboard
from utils.database import check_user_needs_consent, save_user_consent
from utils.rate_limiter import rate_limit, rate_limiter
from config import RATE_LIMITING_ENABLED, ADMIN_TELEGRAM_IDS

logger = logging.getLogger(__name__)

# Инициализация rate limiter (v9.2 Security)
if RATE_LIMITING_ENABLED:
    rate_limiter.set_admin_ids(ADMIN_TELEGRAM_IDS)
    logger.info(f"🔒 Rate limiting enabled with {len(ADMIN_TELEGRAM_IDS)} admins")
else:
    logger.info("🔒 Rate limiting disabled")

# Состояния для v7.2 с упрощенной системой оценок
WAITING_VACANCY, WAITING_RESUME, WAITING_IMPROVEMENT_REQUEST, WAITING_FEEDBACK = range(300, 304)

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


@rate_limit('commands')
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


@rate_limit('commands')
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


@rate_limit('commands')
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Контакты поддержки"""
    if update.message:
        await update.message.reply_text(
            "📞 <b>ПОДДЕРЖКА И ОБРАТНАЯ СВЯЗЬ</b>\n\n"
            "💬 <b>Есть вопросы или предложения?</b>\n"
            "Напиши в tg @shoodyakoff",
            parse_mode='HTML'
        )





@rate_limit('commands')
async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога v6.0"""
    logger.info("🚀 Начинаем диалог v6.0")
    
    # Защита от двойных нажатий - очищаем данные
    if context.user_data is not None:
        context.user_data.clear()
        # Устанавливаем флаги активной сессии и инициализации
        context.user_data['conversation_state'] = 'active'
        context.user_data['initialized'] = True  # ВСЕГДА устанавливаем для ConversationHandler
    
    # Трекаем пользователя и инициализируем
    user = update.effective_user
    user_id = None
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
            
            # Трекаем канал привлечения (если новый пользователь)
            start_param = ' '.join(context.args) if context.args else None
            if start_param:
                await acquisition_service.track_user_acquisition(
                    user_id=user_id,
                    start_param=start_param
                )
    
    # Проверяем лимиты пользователя
    if user_id:
        limits = await subscription_service.check_user_limits(user_id)
        limit_message = subscription_service.format_limit_message(limits)
        
        if not limits['can_generate']:
            # Пользователь исчерпал лимит
            if update.callback_query:
                await update.callback_query.edit_message_text(text=limit_message, parse_mode='HTML')
            elif update.message:
                await update.message.reply_text(text=limit_message, parse_mode='HTML')
            return ConversationHandler.END
    
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
    
    # Проверяем, показывали ли уже подробное объяснение
    show_full_intro = context.user_data.get('shown_full_intro', False) if context.user_data else False
    
    if not show_full_intro:
        # Полное сообщение для новых пользователей
        message = f"""
{time_greeting}{user_name}! 🎯

<b>Создадим сопроводительное письмо, которое заметят!</b>

📋 <b>Что нужно для идеального письма:</b>

<b>1️⃣ Подробное описание вакансии:</b>
• Требования к кандидату
• Обязанности и задачи  
• Информация о компании
• Условия работы

<b>2️⃣ Детальное резюме с:</b>
• Конкретными достижениями и цифрами
• Релевантным опытом работы
• Ключевыми навыками
• Образованием и сертификатами

💡 <b>Совет:</b> Чем подробнее информация, тем точнее и убедительнее будет письмо!

🚀 <b>Начнём с описания вакансии...</b>
"""
        # Помечаем что показали полное объяснение
        if context.user_data is not None:
            context.user_data['shown_full_intro'] = True
    else:
        # Сокращенное сообщение для повторных использований
        message = f"""
{time_greeting}{user_name}! 🎯

<b>Создаем новое сопроводительное письмо</b>

🚀 <b>Начнём с описания вакансии...</b>
"""
    
    # Добавляем информацию о подписке и лимитах
    if user_id:
        limits = await subscription_service.check_user_limits(user_id)
        subscription_info = subscription_service.format_subscription_info(limits)
        message += f"\n{subscription_info}\n"
    
    message += (
        "📝 <b>Шаг 1/3:</b> Отправьте текст вакансии\n\n"
        "💡 <i>Совет: Скопируйте полное описание вакансии с сайта работодателя</i>"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text=message, parse_mode='HTML')
    elif update.message:
        await update.message.reply_text(text=message, parse_mode='HTML')
    
    logger.info("🔍 START_CONVERSATION: Возвращаем WAITING_VACANCY")
    return WAITING_VACANCY


@rate_limit('commands', check_text_size=True)
@ValidationMiddleware.require_initialization
@ValidationMiddleware.require_text_message
async def handle_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка вакансии"""
    logger.info(f"🔍 HANDLE_VACANCY CALLED! Message: {update.message.text[:50] if update.message and update.message.text else 'None'}...")
    logger.info(f"🔍 context.user_data keys: {list(context.user_data.keys()) if context.user_data else 'None'}")
    
    if not update.message or not update.message.text:
        logger.error("❌ No message or text in handle_vacancy")
        return WAITING_VACANCY
        
    vacancy_text = update.message.text.strip()
    
    # Валидация текста вакансии
    is_valid, error_msg = InputValidator.validate_vacancy_text(vacancy_text)
    if not is_valid:
        await update.message.reply_text(error_msg, parse_mode='HTML')
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
        "📋 <b>Шаг 2/3:</b> Теперь отправьте ваше резюме\n\n"
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


@rate_limit('ai_requests', check_text_size=True)
@ValidationMiddleware.require_initialization
@ValidationMiddleware.require_text_message
async def handle_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка резюме и генерация письма"""
    if not update.message or not update.message.text:
        return WAITING_RESUME
        
    resume_text = update.message.text.strip()
    
    # Валидация текста резюме
    is_valid, error_msg = InputValidator.validate_resume_text(resume_text)
    if not is_valid:
        await update.message.reply_text(error_msg, parse_mode='HTML')
        return WAITING_RESUME
    
    # ========================================
    # ПРОВЕРКА СОГЛАСИЯ НА ОБРАБОТКУ ПД (ФЗ-152)
    # ========================================
    user_id = None
    if context.user_data is not None:
        user_id = context.user_data.get('analytics_user_id')
    
    if user_id:
        try:
            needs_consent = await check_user_needs_consent(user_id)
            
            if needs_consent:
                # Пользователю нужно согласие - показываем форму согласия
                logger.info(f"🔒 User {user_id} needs consent - showing consent form")
                
                # Сохраняем резюме в контексте для продолжения после согласия
                if context.user_data is not None:
                    context.user_data['pending_resume_text'] = resume_text
                
                consent_message = (
                    "🔒 <b>Согласие на обработку персональных данных</b>\n\n"
                    "Для генерации персонализированного письма нужно согласие на обработку данных резюме согласно ФЗ-152.\n\n"
                    "📋 <b>Что мы обрабатываем:</b>\n"
                    "• Текст вашего резюме (только для анализа)\n"
                    "• Информацию о вакансии\n\n"
                    "🔐 <b>Гарантии безопасности:</b>\n"
                    "• Данные НЕ сохраняются после генерации\n"
                    "• Обработка происходит в реальном времени\n"
                    "• Полная конфиденциальность\n\n"
                    "📄 <b>Документы:</b>\n"
                    "• Telegram: /privacy и /terms\n"
                    "• 🌐 Notion: https://www.notion.so/21d47215317a8035a55ac5432dc8476c\n\n"
                    "Продолжить генерацию письма?"
                )
                
                # Создаем кнопки согласия
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Согласен и продолжить", callback_data=f"consent_agree_{user_id}")],
                    [InlineKeyboardButton("❌ Отказаться", callback_data=f"consent_decline_{user_id}")],
                    [InlineKeyboardButton("📄 Политика конфиденциальности", callback_data="show_privacy")]
                ])
                
                await update.message.reply_text(
                    consent_message,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                
                # Возвращаем специальное состояние ожидания согласия
                return WAITING_RESUME  # Остаемся в том же состоянии, но ждем callback
                
        except Exception as e:
            logger.error(f"❌ Error checking consent for user {user_id}: {e}")
            # В случае ошибки продолжаем без проверки согласия
            pass
    
    # Получаем вакансию и сохраняем резюме
    vacancy_text = None
    if context.user_data is not None:
        vacancy_text = context.user_data.get('vacancy_text')
        context.user_data['resume_text'] = resume_text  # Сохраняем резюме для итераций
    
    if not vacancy_text:
        await update.message.reply_text("❌ Вакансия потеряна. Начните заново: /start")
        return ConversationHandler.END
    
    # Показываем динамический прогресс
    processing_msg = await update.message.reply_text(
        "🚀 <b>Начинаю работу над вашим письмом!</b>\n\n"
        "🔍 <b>Шаг 3/3:</b> Анализирую вакансию...\n"
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
        
        # Обновляем сессию - добавляем данные резюме (с санитизацией v9.2)
        if user_id and session_id:
            from services.ai_factory import AIFactory
            current_provider = AIFactory.get_provider_name()
            
            # Санитизируем резюме для БД (PII protection v9.2)
            sanitized_resume = InputValidator.sanitize_resume_text(resume_text)
            
            await analytics.update_letter_session(session_id, {
                'resume_text': sanitized_resume[:1000],  # Первые 1000 символов санитизированного текста
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
        
        # Получаем статус итераций для показа счетчика
        iteration_status = None
        if session_id:
            try:
                iteration_status = await feedback_service.get_session_iteration_status(session_id)
                logger.info(f"🔍 RAILWAY DEBUG: iteration_status получен: {iteration_status}")
            except Exception as e:
                logger.error(f"❌ RAILWAY DEBUG: Ошибка получения iteration_status: {e}")
        else:
            logger.error(f"❌ RAILWAY DEBUG: session_id is None!")
        
        # Проверяем, успешно ли сгенерировалось письмо
        is_generation_successful = (
            letter and 
            letter.strip() and 
            letter != "Не удалось сгенерировать письмо. Попробуйте еще раз." and
            letter != "Произошла ошибка при генерации письма. Попробуйте еще раз." and
            len(letter.strip()) > 50  # Минимальная длина для нормального письма
        )
        
        # Сохраняем данные для кнопок в context.user_data 
        if context.user_data and session_id:
            context.user_data['current_session_id'] = session_id
            context.user_data['vacancy_text'] = vacancy_text  # Для улучшений
            context.user_data['resume_text'] = resume_text    # Для улучшений
        
        # Формируем сообщение и кнопки в зависимости от результата генерации
        if is_generation_successful:
            # Письмо сгенерировано успешно
            feedback_message = f"🎉 <b>Письмо готово за {generation_time} секунд!</b>\n\n"
            
            if iteration_status:
                counter_text = feedback_service.format_iteration_counter(iteration_status)
                feedback_message += f"{counter_text}\n\n"
            
            feedback_message += (
                "💡 <b>Оцените результат:</b>\n"
                "• ❤️ Нравится - отлично!\n"
                "• 👎 Не подходит - попробуем еще раз\n\n"
                "🍀 <i>Ваша оценка поможет улучшить качество писем!</i>"
            )
            
            # Показываем кнопки оценки
            if session_id and iteration_status:
                keyboard = get_feedback_keyboard(session_id, iteration_status.current_iteration)
                logger.info(f"✅ RAILWAY DEBUG: Кнопки оценки созданы для session_id: {session_id}")
            elif session_id:
                # Fallback: создаем кнопки с дефолтными значениями если нет iteration_status
                keyboard = get_feedback_keyboard(session_id, 1)
                logger.warning(f"⚠️ RAILWAY DEBUG: Использован fallback для кнопок оценки, session_id: {session_id}")
            else:
                keyboard = None
                logger.error(f"❌ RAILWAY DEBUG: Не могу создать кнопки оценки - нет session_id!")
        else:
            # Письмо НЕ сгенерировалось
            feedback_message = f"❌ <b>Не удалось создать письмо</b>\n\n"
            
            if iteration_status:
                counter_text = feedback_service.format_iteration_counter(iteration_status)
                feedback_message += f"{counter_text}\n\n"
            
            feedback_message += (
                "🔧 <b>Что можно сделать:</b>\n"
                "• 🔄 Повторить генерацию - попробуем еще раз\n"
                "• 🆕 Создать новое письмо - начать заново\n\n"
                "💡 <i>Иногда помогает повторная попытка!</i>"
            )
            
            # Показываем кнопку повтора
            keyboard = get_retry_keyboard(session_id) if session_id else None
            logger.warning(f"🔄 RAILWAY DEBUG: Показываю кнопку повтора для session_id: {session_id}")
        
        await update.message.reply_text(
            feedback_message,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        # Завершаем аналитику
        if user_id and session_id:
            # Увеличиваем счетчик использованных писем (ТОЛЬКО для новых сессий!)
            await subscription_service.increment_usage(user_id)
            
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
    
    # НЕ очищаем context.user_data - нужно для кнопок обратной связи!
    # Переходим в состояние ожидания обратной связи вместо завершения диалога
    
    return WAITING_FEEDBACK


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


# ============================================================================
# ОБРАБОТЧИКИ СИСТЕМЫ ОЦЕНОК И ИТЕРАЦИЙ V7.2
# УПРОЩЕННАЯ ВЕРСИЯ: только лайки/дизлайки БЕЗ комментариев
# ============================================================================

async def handle_feedback_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий кнопок оценки - УПРОЩЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    if not query or not query.data:
        logger.error("❌ Feedback button: no query or data")
        return ConversationHandler.END
    
    logger.info(f"🔍 Feedback button pressed: {query.data}")
    await query.answer()
    
    # Парсим callback_data: feedback_{type}_{session_id}_{iteration}
    parts = query.data.split('_')
    if len(parts) < 4:
        logger.error(f"❌ Invalid callback data format: {query.data}")
        await query.edit_message_text("❌ Ошибка: неверный формат данных кнопки")
        return ConversationHandler.END
    
    feedback_type = parts[1]  # like, dislike
    session_id = parts[2]
    iteration = int(parts[3])
    
    # Получаем пользователя
    user_id = None
    if context.user_data:
        user_id = context.user_data.get('analytics_user_id')
    
    if not user_id:
        logger.error("❌ No user_id in context.user_data")
        await query.edit_message_text("❌ Ошибка: пользователь не найден")
        return ConversationHandler.END
    
    # Получаем статус итераций
    iteration_status = await feedback_service.get_session_iteration_status(session_id)
    if not iteration_status:
        logger.error(f"❌ No iteration status for session {session_id}")
        await query.edit_message_text("❌ Ошибка: сессия не найдена")
        return ConversationHandler.END
    
    # СРАЗУ сохраняем оценку в БД (БЕЗ комментария)
    feedback_data = LetterFeedbackData(
        session_id=session_id,
        user_id=user_id,
        iteration_number=iteration,
        feedback_type=feedback_type
    )
    await feedback_service.save_feedback(feedback_data)
    
    # Формируем ответ в зависимости от типа оценки
    if feedback_type == "like":
        response_text = (
            "❤️ <b>Спасибо за оценку!</b>\n\n"
            "🙏 Мы ценим ваш отзыв! Это помогает нам создавать лучшие письма.\n\n"
            f"🔄 <b>У вас есть ещё {iteration_status.remaining_iterations} итерации правок</b> "
            "для этой пары вакансия-резюме, или можете создать новое письмо для другой вакансии.\n\n"
            "💡 <b>Что вы хотите сделать дальше?</b>"
        )
    else:  # dislike
        response_text = (
            "👎 <b>Понятно, письмо не подошло.</b>\n\n"
            "🔧 <b>Мы поможем это исправить!</b>\n\n"
            f"🔄 <b>Осталось {iteration_status.remaining_iterations} попыток</b> для улучшения этого письма.\n\n"
            "💡 <b>Что будем делать?</b>"
        )
    
    # Показываем кнопки действий
    keyboard = get_iteration_keyboard(session_id, iteration_status.remaining_iterations)
    
    await query.edit_message_text(
        response_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    return WAITING_FEEDBACK


async def handle_improve_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка запроса на улучшение письма - НОВАЯ ЛОГИКА"""
    query = update.callback_query
    if not query or not query.data:
        logger.error("❌ Improve letter: no query or data")
        return ConversationHandler.END
    
    logger.info(f"🔄 Improve letter button pressed: {query.data}")
    
    # Защита от двойных нажатий
    await query.answer("🔄 Переходим к улучшению...")
    
    # Парсим callback_data: improve_letter_{session_id}
    parts = query.data.split('_')
    if len(parts) < 3:
        logger.error(f"❌ Invalid improve letter callback data: {query.data}")
        await query.edit_message_text("❌ Ошибка: неверный формат данных кнопки")
        return ConversationHandler.END
    
    session_id = parts[2]
    
    # Получаем статус итераций
    iteration_status = await feedback_service.get_session_iteration_status(session_id)
    if not iteration_status:
        logger.error(f"❌ No iteration status for session {session_id}")
        await query.edit_message_text(
            "❌ <b>Ошибка получения статуса сессии</b>\n\n"
            "Попробуйте создать новое письмо: /start",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    if not iteration_status.can_iterate:
        logger.warning(f"⚠️ Cannot iterate: max iterations reached")
        await query.edit_message_text(
            "❌ <b>Улучшение недоступно</b>\n\n"
            f"Достигнуто максимальное количество итераций ({iteration_status.max_iterations})\n\n"
            "✅ Используйте текущую версию письма или создайте новое: /start",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    # Сохраняем session_id для дальнейшей обработки
    if context.user_data:
        context.user_data['improvement_session_id'] = session_id
        
        # Проверяем, что у нас есть необходимые данные для улучшения
        if not context.user_data.get('vacancy_text') or not context.user_data.get('resume_text'):
            logger.error("❌ Missing vacancy_text or resume_text in context")
            await query.edit_message_text(
                "❌ <b>Недостаточно данных для улучшения</b>\n\n"
                "Создайте новое письмо: /start",
                parse_mode='HTML'
            )
            return ConversationHandler.END
    
    # НОВАЯ ЛОГИКА: показываем только текст БЕЗ кнопок
    prompt_text = feedback_service.get_improvement_prompt_text(iteration_status.remaining_iterations)
    
    await query.edit_message_text(
        prompt_text,
        parse_mode='HTML'
        # БЕЗ reply_markup - никаких кнопок!
    )
    
    return WAITING_IMPROVEMENT_REQUEST


@rate_limit('ai_requests')
async def handle_retry_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Повторная генерация письма с уже сохраненными данными"""
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    
    await query.answer("🔄 Повторяю генерацию...")
    
    # Проверяем наличие сохраненных данных
    if not context.user_data:
        await query.edit_message_text(
            "❌ Данные сессии потеряны\n\n"
            "🔄 Начните заново: /start"
        )
        return ConversationHandler.END
    
    vacancy_text = context.user_data.get('vacancy_text')
    resume_text = context.user_data.get('resume_text')
    
    if not vacancy_text or not resume_text:
        await query.edit_message_text(
            "❌ Не хватает данных для повтора\n\n"
            "🔄 Начните заново: /start"
        )
        return ConversationHandler.END
    
    # Показываем сообщение о повторной генерации
    await query.edit_message_text(
        "🔄 <b>Повторяю генерацию письма...</b>\n\n"
        "⏳ Использую сохраненные данные\n"
        "🎯 Создаю новое письмо",
        parse_mode='HTML'
    )
    
    # Повторяем генерацию напрямую с сохраненными данными
    try:
        # Импортируем необходимые функции
        from services.smart_analyzer import generate_simple_letter
        from services.analytics_service import analytics
        from services.subscription_service import subscription_service  
        from services.feedback_service import feedback_service
        from models.analytics_models import LetterSessionData
        import time
        
        # Получаем user_id
        user_id = context.user_data.get('analytics_user_id')
        if not user_id:
            if query.message:
                await query.message.reply_text("❌ Ошибка: пользователь не найден")
            return ConversationHandler.END
        
        # Создаем данные для новой сессии
        session_data = LetterSessionData(
            user_id=user_id,
            job_description=vacancy_text,
            job_description_length=len(vacancy_text),
            resume_text=resume_text,
            resume_length=len(resume_text)
        )
        
        # Создаем новую сессию для повторной генерации
        session_id = await analytics.create_letter_session(session_data)
        if not session_id:
            if query.message:
                await query.message.reply_text("❌ Ошибка создания сессии")
            return ConversationHandler.END
        
        # Генерируем письмо
        start_time = time.time()
        letter = await generate_simple_letter(
            vacancy_text=vacancy_text,
            resume_text=resume_text,
            user_id=user_id,
            session_id=session_id
        )
        generation_time = int(time.time() - start_time)
        
        # Отправляем результат
        if query.message:
            await query.message.reply_text(
                f"✍️ <b>ПИСЬМО:</b>\n\n{letter}",
                parse_mode='HTML'
            )
        
        # Проверяем успешность генерации и показываем соответствующие кнопки
        is_generation_successful = (
            letter and 
            letter.strip() and 
            letter != "Не удалось сгенерировать письмо. Попробуйте еще раз." and
            letter != "Произошла ошибка при генерации письма. Попробуйте еще раз." and
            len(letter.strip()) > 50
        )
        
        # Обновляем данные в context
        context.user_data['current_session_id'] = session_id
        
        # Получаем статус итераций
        iteration_status = await feedback_service.get_session_iteration_status(session_id)
        
        if is_generation_successful:
            # Успешная генерация
            feedback_message = f"🎉 <b>Письмо готово за {generation_time} секунд!</b>\n\n"
            
            if iteration_status:
                counter_text = feedback_service.format_iteration_counter(iteration_status)
                feedback_message += f"{counter_text}\n\n"
            
            feedback_message += (
                "💡 <b>Оцените результат:</b>\n"
                "• ❤️ Нравится - отлично!\n"
                "• 👎 Не подходит - попробуем еще раз\n\n"
                "🍀 <i>Ваша оценка поможет улучшить качество писем!</i>"
            )
            
            keyboard = get_feedback_keyboard(session_id, iteration_status.current_iteration if iteration_status else 1)
        else:
            # Неуспешная генерация
            feedback_message = f"❌ <b>Не удалось создать письмо</b>\n\n"
            
            if iteration_status:
                counter_text = feedback_service.format_iteration_counter(iteration_status)
                feedback_message += f"{counter_text}\n\n"
            
            feedback_message += (
                "🔧 <b>Что можно сделать:</b>\n"
                "• 🔄 Повторить генерацию - попробуем еще раз\n"
                "• 🆕 Создать новое письмо - начать заново\n\n"
                "💡 <i>Иногда помогает повторная попытка!</i>"
            )
            
            keyboard = get_retry_keyboard(session_id)
        
        if query.message:
            await query.message.reply_text(
                feedback_message,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        
        # Обновляем аналитику
        if is_generation_successful:
            await subscription_service.increment_usage(user_id)
            await analytics.update_letter_session(session_id, {
                'generated_letter': letter[:2000],
                'generated_letter_length': len(letter),
                'generation_time_seconds': generation_time,
                'status': 'completed'
            })
            await analytics.track_letter_generated(user_id, session_id, len(letter), generation_time)
        
        return WAITING_FEEDBACK
        
    except Exception as e:
        logger.error(f"❌ Ошибка повторной генерации: {e}")
        if query.message:
            await query.message.reply_text(
                "❌ <b>Ошибка при повторной генерации</b>\n\n"
                "🔄 Попробуйте начать заново: /start",
                parse_mode='HTML'
            )
        return ConversationHandler.END


@rate_limit('ai_requests', check_text_size=True)
async def handle_improvement_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка запроса на улучшение"""
    if not update.message or not update.message.text:
        return WAITING_IMPROVEMENT_REQUEST
    
    improvement_request = update.message.text.strip()
    
    # Получаем данные
    if not context.user_data:
        await update.message.reply_text("❌ Ошибка: данные сессии потеряны")
        return ConversationHandler.END
    
    session_id = context.user_data.get('improvement_session_id')
    user_id = context.user_data.get('analytics_user_id')
    vacancy_text = context.user_data.get('vacancy_text')
    
    if not all([session_id, user_id, vacancy_text]):
        await update.message.reply_text("❌ Ошибка: неполные данные для улучшения")
        return ConversationHandler.END
    
    # Проверяем типы данных
    if not isinstance(session_id, str) or not isinstance(user_id, int) or not isinstance(vacancy_text, str):
        await update.message.reply_text("❌ Ошибка: некорректные типы данных")
        return ConversationHandler.END
    
    # Показываем прогресс
    progress_msg = await update.message.reply_text(
        "🔄 <b>Улучшаю письмо...</b>\n\n"
        "⏳ Учитываю ваши пожелания\n"
        "🎯 Создаю улучшенную версию",
        parse_mode='HTML'
    )
    
    try:
        # Увеличиваем номер итерации
        await feedback_service.increment_session_iteration(session_id)
        
        # Получаем обновленный статус
        iteration_status = await feedback_service.get_session_iteration_status(session_id)
        if not iteration_status:
            raise Exception("Не удалось получить статус итерации")
        
        # Генерируем улучшенное письмо
        start_time = time.time()
        
        # Получаем предыдущее письмо из сессии
        session_response = await analytics.get_letter_session_by_id(session_id)
        previous_letter = ""
        if session_response:
            previous_letter = session_response.get('generated_letter', '')
        
        # Fallback если предыдущее письмо не найдено
        if not previous_letter:
            logger.warning(f"⚠️ Previous letter not found for session {session_id}, using simple generation")
            improved_letter = await generate_simple_letter(
                vacancy_text=vacancy_text,
                resume_text=context.user_data.get('resume_text', ''),
                user_id=user_id,
                session_id=session_id
            )
        else:
            # Генерируем улучшенное письмо с учетом комментариев
            logger.info(f"🔄 Improving letter with previous version ({len(previous_letter)} chars)")
            improved_letter = await generate_improved_letter(
                vacancy_text=vacancy_text,
                resume_text=context.user_data.get('resume_text', ''),
                previous_letter=previous_letter,
                user_feedback=improvement_request,
                improvement_request=improvement_request,
                user_id=user_id,
                session_id=session_id
            )
        
        generation_time = int(time.time() - start_time)
        
        # Сохраняем итерацию
        iteration_data = LetterIterationImprovement(
            session_id=session_id,
            user_id=user_id,
            iteration_number=iteration_status.current_iteration,
            user_feedback=improvement_request,
            improvement_request=improvement_request,
            previous_letter=previous_letter[:1000] if previous_letter else ""  # Первые 1000 символов
        )
        
        await feedback_service.save_letter_iteration(
            iteration_data, improved_letter, generation_time
        )
        
        # 📊 АНАЛИТИКА: Трекаем событие улучшения письма
        from models.analytics_models import EventData
        
        event_data = EventData(
            user_id=user_id,
            event_type='letter_improved',
            session_id=session_id,
            event_data={
                'iteration_number': iteration_status.current_iteration,
                'improvement_length': len(improvement_request),
                'generation_time_seconds': generation_time,
                'has_previous_letter': bool(previous_letter)
            }
        )
        await analytics.track_event(event_data)
        
        # Удаляем прогресс
        await progress_msg.delete()
        
        # Показываем улучшенное письмо
        await update.message.reply_text(
            f"✍️ <b>УЛУЧШЕННОЕ ПИСЬМО:</b>\n\n{improved_letter}",
            parse_mode='HTML'
        )
        
        # Показываем кнопки для новой оценки
        counter_text = feedback_service.format_iteration_counter(iteration_status)
        feedback_message = f"🎉 <b>Письмо улучшено за {generation_time} секунд!</b>\n\n{counter_text}\n\n"
        
        if iteration_status.remaining_iterations > 0:
            feedback_message += (
                "💡 <b>Оцените новую версию:</b>\n"
                "• ❤️ Нравится - отлично!\n"
                "• 👎 Не подходит - попробуем еще раз\n\n"
            )
            keyboard = get_feedback_keyboard(session_id, iteration_status.current_iteration)
        else:
            feedback_message += "✅ Используйте это письмо или создайте новое"
            keyboard = get_final_letter_keyboard()
        
        await update.message.reply_text(
            feedback_message,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка улучшения письма: {e}")
        
        try:
            await progress_msg.delete()
        except:
            pass
        
        await update.message.reply_text(
            "❌ <b>Ошибка при улучшении письма</b>\n\n"
            "🔧 Попробуйте еще раз или создайте новое письмо: /start",
            parse_mode='HTML'
        )
    
    return WAITING_FEEDBACK


async def handle_accept_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка принятия письма"""
    query = update.callback_query
    if not query:
        logger.error("❌ Accept letter: no query")
        return ConversationHandler.END
    
    logger.info(f"✅ Letter accepted by user: {query.data}")
    logger.info(f"🔍 User ID: {query.from_user.id}")
    logger.info(f"🔍 Chat ID: {query.message.chat_id if query.message else 'None'}")
    
    await query.answer("✅ Отлично! Удачи с этим письмом!")
    
    await query.edit_message_text(
        "✅ <b>Письмо принято!</b>\n\n"
        "🎯 <b>Что дальше:</b>\n"
        "• Скопируйте письмо\n"
        "• Адаптируйте под конкретную компанию\n"
        "• Отправляйте работодателю\n\n"
        "🔄 <b>Создать новое письмо:</b> /start\n"
        "💬 <b>Есть вопросы:</b> /support\n\n"
        "🍀 <b>Удачи в поиске работы!</b>",
        parse_mode='HTML'
    )
    
    # Очищаем данные
    if context.user_data:
        logger.info(f"🔍 Clearing context.user_data with keys: {list(context.user_data.keys())}")
        context.user_data.clear()
    else:
        logger.warning("⚠️ context.user_data is None when accepting letter")
    
    return ConversationHandler.END


async def handle_waiting_feedback_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка текстовых сообщений в состоянии ожидания обратной связи"""
    if update.message:
        await update.message.reply_text(
            "💡 <b>Используйте кнопки выше для оценки письма</b>\n\n"
            "🔄 <b>Или отправьте /start для создания нового письма</b>",
            parse_mode='HTML'
        )
    return WAITING_FEEDBACK


# ========================================
# ОБРАБОТЧИКИ СОГЛАСИЯ НА ОБРАБОТКУ ПД
# ========================================

async def handle_consent_agree(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка согласия пользователя на обработку ПД"""
    query = update.callback_query
    if not query:
        return WAITING_RESUME
    
    await query.answer("✅ Согласие получено!")
    
    # Извлекаем user_id из callback_data
    try:
        if not query.data:
            return WAITING_RESUME
        user_id = int(query.data.split('_')[-1])
        logger.info(f"✅ User {user_id} agreed to consent")
        
        # Сохраняем согласие в базе данных
        consent_saved = await save_user_consent(user_id, consent_version='v1.0', marketing_consent=False)
        
        if consent_saved:
            logger.info(f"✅ Consent saved for user {user_id}")
        else:
            logger.error(f"❌ Failed to save consent for user {user_id}")
        
        # Получаем сохраненное резюме из контекста
        resume_text = None
        if context.user_data:
            resume_text = context.user_data.get('pending_resume_text')
        
        if resume_text:
            # Продолжаем обработку резюме
            await query.edit_message_text(
                "✅ <b>Согласие получено!</b>\n\n"
                "🚀 Теперь отправьте ваше резюме еще раз для генерации письма:",
                parse_mode='HTML'
            )
            
            # Очищаем pending резюме - пользователь отправит резюме заново
            if context.user_data:
                context.user_data.pop('pending_resume_text', None)
            
            return WAITING_RESUME
        else:
            await query.edit_message_text(
                "✅ <b>Согласие получено!</b>\n\n"
                "❌ Резюме потеряно. Отправьте его еще раз:",
                parse_mode='HTML'
            )
            return WAITING_RESUME
            
    except Exception as e:
        logger.error(f"❌ Error processing consent agreement: {e}")
        await query.edit_message_text(
            "❌ <b>Ошибка при обработке согласия</b>\n\n"
            "Попробуйте еще раз или начните заново: /start",
            parse_mode='HTML'
        )
        return ConversationHandler.END


async def handle_consent_decline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка отказа от согласия"""
    query = update.callback_query
    if not query:
        return WAITING_RESUME
    
    await query.answer("Понимаем ваше решение")
    
    try:
        if not query.data:
            return WAITING_RESUME
        user_id = int(query.data.split('_')[-1])
        logger.info(f"❌ User {user_id} declined consent")
        
        await query.edit_message_text(
            "❌ <b>Согласие не дано</b>\n\n"
            "Понимаем! Без согласия мы не можем обработать ваше резюме согласно требованиям ФЗ-152.\n\n"
            "🔄 <b>Если передумаете:</b>\n"
            "Возвращайтесь в любое время - мы всегда готовы помочь! 😊\n\n"
            "🆕 <b>Создать новое письмо:</b> /start",
            parse_mode='HTML'
        )
        
        # Очищаем pending данные
        if context.user_data:
            context.user_data.pop('pending_resume_text', None)
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"❌ Error processing consent decline: {e}")
        return ConversationHandler.END


async def handle_show_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показать политику конфиденциальности"""
    query = update.callback_query
    if not query:
        return WAITING_RESUME
    
    await query.answer("Открываю политику конфиденциальности...")
    
    try:
        # Читаем политику конфиденциальности из файла
        with open('docs/legal/privacy_policy.md', 'r', encoding='utf-8') as f:
            privacy_content = f.read()
        
        # Убираем markdown заголовки для более читаемого вида в Telegram
        privacy_text = privacy_content.replace('# ', '').replace('## ', '').replace('### ', '')
        
        # Telegram лимит 4096 символов - разбиваем на части
        max_length = 4000  # Оставляем место для кнопок
        
        if len(privacy_text) <= max_length:
            # Текст помещается в одно сообщение
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Вернуться к согласию", callback_data="back_to_consent")]
            ])
            
            await query.edit_message_text(
                f"📄 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>\n\n{privacy_text}",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            # Разбиваем на части
            parts = []
            current_part = ""
            
            for line in privacy_text.split('\n'):
                if len(current_part + line + '\n') <= max_length:
                    current_part += line + '\n'
                else:
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = line + '\n'
            
            if current_part:
                parts.append(current_part.strip())
            
            # Отправляем первую часть
            if parts:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Вернуться к согласию", callback_data="back_to_consent")]
                ])
                
                await query.edit_message_text(
                    f"📄 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>\n<i>(часть 1 из {len(parts)})</i>\n\n{parts[0]}",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                
                # Отправляем остальные части отдельными сообщениями
                for i, part in enumerate(parts[1:], 2):
                    if query.message:
                        await query.message.reply_text(
                            f"📄 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>\n<i>(часть {i} из {len(parts)})</i>\n\n{part}",
                            parse_mode='HTML'
                        )
        
        return WAITING_RESUME
        
    except FileNotFoundError:
        await query.edit_message_text(
            "❌ <b>Политика конфиденциальности временно недоступна</b>\n\n"
            "Обратитесь в поддержку: /support",
            parse_mode='HTML'
        )
        return WAITING_RESUME
    except Exception as e:
        logger.error(f"❌ Error showing privacy policy: {e}")
        await query.edit_message_text(
            "❌ <b>Ошибка при загрузке политики</b>\n\n"
            "Попробуйте позже или обратитесь в поддержку: /support",
            parse_mode='HTML'
        )
        return WAITING_RESUME


async def handle_back_to_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вернуться к форме согласия из политики конфиденциальности"""
    query = update.callback_query
    if not query:
        return WAITING_RESUME
    
    await query.answer("Возвращаемся к согласию...")
    
    # Получаем user_id из контекста
    user_id = None
    if context.user_data:
        user_id = context.user_data.get('analytics_user_id')
    
    if not user_id:
        await query.edit_message_text(
            "❌ <b>Ошибка</b>\n\n"
            "Начните заново: /start",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    # Показываем форму согласия заново
    consent_message = (
        "🔒 <b>Согласие на обработку персональных данных</b>\n\n"
        "Для генерации персонализированного письма нужно согласие на обработку данных резюме согласно ФЗ-152.\n\n"
        "📋 <b>Что мы обрабатываем:</b>\n"
        "• Текст вашего резюме (только для анализа)\n"
        "• Информацию о вакансии\n\n"
        "🔐 <b>Гарантии безопасности:</b>\n"
        "• Данные НЕ сохраняются после генерации\n"
        "• Обработка происходит в реальном времени\n"
        "• Полная конфиденциальность\n\n"
        "📄 Подробности: /privacy\n\n"
        "Продолжить генерацию письма?"
    )
    
    # Создаем кнопки согласия
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Согласен и продолжить", callback_data=f"consent_agree_{user_id}")],
        [InlineKeyboardButton("❌ Отказаться", callback_data=f"consent_decline_{user_id}")],
        [InlineKeyboardButton("📄 Политика конфиденциальности", callback_data="show_privacy")]
    ])
    
    await query.edit_message_text(
        consent_message,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    return WAITING_RESUME


def get_conversation_handler():
    """Создает ConversationHandler для v7.2 с упрощенной системой оценок"""
    from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
    
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_conversation),
            CallbackQueryHandler(handle_start_work_callback, pattern=r'^start_work$')
        ],
        states={
            WAITING_VACANCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vacancy)
            ],
            WAITING_RESUME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_resume),
                # Обработчики кнопок согласия
                CallbackQueryHandler(handle_consent_agree, pattern=r'^consent_agree_'),
                CallbackQueryHandler(handle_consent_decline, pattern=r'^consent_decline_'),
                CallbackQueryHandler(handle_show_privacy, pattern=r'^show_privacy$'),
                CallbackQueryHandler(handle_back_to_consent, pattern=r'^back_to_consent$')
            ],
            WAITING_IMPROVEMENT_REQUEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_improvement_request)
            ],
            WAITING_FEEDBACK: [
                # Callback handlers для кнопок обратной связи (только лайки/дизлайки)
                CallbackQueryHandler(handle_feedback_button, pattern=r'^feedback_(like|dislike)_'),
                CallbackQueryHandler(handle_improve_letter, pattern=r'^improve_letter_'),
                CallbackQueryHandler(handle_retry_generation, pattern=r'^retry_generation_'),
                CallbackQueryHandler(start_conversation, pattern=r'^restart$'),
                # Текстовые сообщения в этом состоянии
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_waiting_feedback_message)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_conversation),
            CommandHandler('start', start_conversation)
        ],
        name="conversation_v7_2",
        persistent=False,
        per_message=False,  # False для работы с MessageHandler и CallbackQueryHandler
        per_chat=True,
        per_user=True
    )


def get_command_handlers():
    """Возвращает список обработчиков команд"""
    from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
    
    return [
        CommandHandler("help", help_command),
        CommandHandler("about", about_command),
        CommandHandler("support", support_command),
        # СКРЫТЫЕ команды (НЕ отображаются в меню)
        CommandHandler("privacy", privacy_command),
        CommandHandler("terms", terms_command),
        # Обработчик кнопки создания письма вне сессии
        CallbackQueryHandler(handle_start_work_callback, pattern=r'^start_work$'),
        # Обработчик кнопки "Вернуться к боту"
        CallbackQueryHandler(handle_back_to_bot, pattern=r'^back_to_bot$'),
        # Обработчик текстовых сообщений вне активной сессии (должен быть последним!)
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_outside_session)
    ]


# ============================================================================
# ОБРАБОТЧИК СООБЩЕНИЙ ВНЕ АКТИВНОЙ СЕССИИ
# ============================================================================

async def handle_message_outside_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик для сообщений, когда пользователь не находится в активной сессии создания письма
    """
    if not update.message or not update.message.text:
        return
    
    # КРИТИЧЕСКИ ВАЖНО: Проверяем, что пользователь НЕ в активной сессии ConversationHandler
    # Если есть активная сессия создания письма - НЕ обрабатываем сообщение
    if context.user_data and context.user_data.get('conversation_state'):
        logger.info(f"🔍 Пользователь в активной сессии, пропускаем outside_session handler")
        return
    
    user = update.effective_user
    user_name = f", {user.first_name}" if user and user.first_name else ""
    
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
    
    # Анализируем, что пользователь написал
    message_text = update.message.text.lower().strip()
    
    # Определяем тип сообщения для персонализированного ответа
    if any(word in message_text for word in ['привет', 'здравствуй', 'добро', 'hi', 'hello']):
        response_type = "greeting"
    elif any(word in message_text for word in ['помощь', 'help', 'что делать', 'как работает']):
        response_type = "help"
    elif any(word in message_text for word in ['письмо', 'резюме', 'вакансия', 'сопровод', 'работа']):
        response_type = "work_related"
    elif any(word in message_text for word in ['спасибо', 'благодарю', 'thanks']):
        response_type = "thanks"
    else:
        response_type = "general"
    
    # Формируем персонализированный ответ
    if response_type == "greeting":
        main_text = f"{time_greeting}{user_name}! 👋\n\nРад вас видеть!"
    elif response_type == "help":
        main_text = f"{time_greeting}{user_name}! 🤝\n\nПомогу вам создать отличное сопроводительное письмо!"
    elif response_type == "work_related":
        main_text = f"{time_greeting}{user_name}! 💼\n\nОтлично! Давайте создадим сопроводительное письмо, которое поможет вам получить работу мечты!"
    elif response_type == "thanks":
        main_text = f"Пожалуйста{user_name}! 😊\n\nВсегда рад помочь!"
    else:
        main_text = f"{time_greeting}{user_name}! 🤖\n\nЯ помогаю создавать сопроводительные письма для поиска работы."
    
    # Проверяем лимиты и подписку пользователя (если он зарегистрирован)
    limit_info = ""
    if context.user_data and context.user_data.get('analytics_user_id'):
        user_id = context.user_data['analytics_user_id']
        try:
            limits = await subscription_service.check_user_limits(user_id)
            subscription_info = subscription_service.format_subscription_info(limits)
            limit_info = f"\n{subscription_info}"
            
            if not limits['can_generate']:
                limit_info += f"⚠️ Лимит исчерпан - обратитесь в поддержку: /support"
        except Exception as e:
            logger.error(f"Error checking limits in outside session: {e}")
    
    response_message = f"""
{main_text}

🎯 <b>Что я умею:</b>
• Анализировать вакансии с помощью ИИ
• Создавать персональные сопроводительные письма
• Адаптировать письма под конкретные позиции
• Работать быстро (30-45 секунд)

💡 <b>Чтобы начать:</b>
Нажмите кнопку ниже или отправьте команду /start{limit_info}

🚀 <b>Готовы создать письмо, которое заметят?</b>
"""
    
    # Создаем клавиатуру с кнопкой начала работы
    keyboard = get_start_work_keyboard()
    
    await update.message.reply_text(
        response_message,
        parse_mode='HTML',
        reply_markup=keyboard
    )


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

@rate_limit('commands')
async def handle_start_work_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик кнопки 'Создать письмо' из сообщений вне сессии"""
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    
    await query.answer("🚀 Начинаем создание письма!")
    
    logger.info("🔍 START_WORK_CALLBACK: Вызываем start_conversation...")
    
    # Перенаправляем в стандартный флоу создания письма
    result = await start_conversation(update, context)
    logger.info(f"🔍 START_WORK_CALLBACK: start_conversation returned {result}")
    return result


# ========================================
# СКРЫТЫЕ КОМАНДЫ ДЛЯ ЮРИДИЧЕСКИХ ДОКУМЕНТОВ
# ========================================

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Скрытая команда для показа политики конфиденциальности"""
    if not update.message:
        return
    
    try:
        # Читаем политику конфиденциальности из файла
        with open('docs/legal/privacy_policy.md', 'r', encoding='utf-8') as f:
            privacy_content = f.read()
        
        # Убираем markdown заголовки для более читаемого вида в Telegram
        privacy_text = privacy_content.replace('# ', '').replace('## ', '').replace('### ', '')
        
        # Telegram лимит 4096 символов - разбиваем на части
        max_length = 4000  # Оставляем место для кнопок
        
        if len(privacy_text) <= max_length:
            # Текст помещается в одно сообщение
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Вернуться к боту", callback_data="back_to_bot")]
            ])
            
            await update.message.reply_text(
                f"📄 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>\n\n{privacy_text}",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            # Разбиваем на части
            parts = []
            current_part = ""
            
            for line in privacy_text.split('\n'):
                if len(current_part + line + '\n') <= max_length:
                    current_part += line + '\n'
                else:
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = line + '\n'
            
            if current_part:
                parts.append(current_part.strip())
            
            # Отправляем первую часть с кнопкой
            if parts:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Вернуться к боту", callback_data="back_to_bot")]
                ])
                
                await update.message.reply_text(
                    f"📄 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>\n<i>(часть 1 из {len(parts)})</i>\n\n{parts[0]}",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                
                # Отправляем остальные части отдельными сообщениями
                for i, part in enumerate(parts[1:], 2):
                    await update.message.reply_text(
                        f"📄 <b>ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>\n<i>(часть {i} из {len(parts)})</i>\n\n{part}",
                        parse_mode='HTML'
                    )
        
    except FileNotFoundError:
        await update.message.reply_text(
            "❌ <b>Политика конфиденциальности временно недоступна</b>\n\n"
            "Обратитесь в поддержку: /support",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"❌ Error showing privacy policy: {e}")
        await update.message.reply_text(
            "❌ <b>Ошибка при загрузке политики</b>\n\n"
            "Попробуйте позже или обратитесь в поддержку: /support",
            parse_mode='HTML'
        )


async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Скрытая команда для показа пользовательского соглашения"""
    if not update.message:
        return
    
    try:
        # Читаем пользовательское соглашение из файла
        with open('docs/legal/terms_of_service.md', 'r', encoding='utf-8') as f:
            terms_content = f.read()
        
        # Убираем markdown заголовки для более читаемого вида в Telegram
        terms_text = terms_content.replace('# ', '').replace('## ', '').replace('### ', '')
        
        # Telegram лимит 4096 символов - разбиваем на части  
        max_length = 4000  # Оставляем место для кнопок
        
        if len(terms_text) <= max_length:
            # Текст помещается в одно сообщение
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Вернуться к боту", callback_data="back_to_bot")]
            ])
            
            await update.message.reply_text(
                f"📋 <b>ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ</b>\n\n{terms_text}",
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            # Разбиваем на части
            parts = []
            current_part = ""
            
            for line in terms_text.split('\n'):
                if len(current_part + line + '\n') <= max_length:
                    current_part += line + '\n'
                else:
                    if current_part:
                        parts.append(current_part.strip())
                    current_part = line + '\n'
            
            if current_part:
                parts.append(current_part.strip())
            
            # Отправляем первую часть с кнопкой
            if parts:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Вернуться к боту", callback_data="back_to_bot")]
                ])
                
                await update.message.reply_text(
                    f"📋 <b>ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ</b>\n<i>(часть 1 из {len(parts)})</i>\n\n{parts[0]}",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                
                # Отправляем остальные части отдельными сообщениями
                for i, part in enumerate(parts[1:], 2):
                    await update.message.reply_text(
                        f"📋 <b>ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ</b>\n<i>(часть {i} из {len(parts)})</i>\n\n{part}",
                        parse_mode='HTML'
                    )
        
    except FileNotFoundError:
        await update.message.reply_text(
            "❌ <b>Пользовательское соглашение временно недоступно</b>\n\n"
            "Обратитесь в поддержку: /support",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"❌ Error showing terms of service: {e}")
        await update.message.reply_text(
            "❌ <b>Ошибка при загрузке соглашения</b>\n\n"
            "Попробуйте позже или обратитесь в поддержку: /support",
            parse_mode='HTML'
        )


async def handle_back_to_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Вернуться к боту'"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer("Возвращаемся к боту...")
    
    await query.edit_message_text(
        "👋 <b>Добро пожаловать обратно!</b>\n\n"
        "🎯 <b>Готовы создать сопроводительное письмо?</b>\n\n"
        "💡 Нажмите /start чтобы начать",
        parse_mode='HTML'
    )


 