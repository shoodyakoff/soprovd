"""
Simple Conversation Handler v7.2
Упрощенная система обратной связи: только лайки/дизлайки БЕЗ комментариев
Релизная версия с улучшенным UX
"""
import logging
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler
from services.smart_analyzer import generate_simple_letter, generate_improved_letter
from services.analytics_service import analytics
from services.subscription_service import subscription_service
from services.feedback_service import feedback_service
from services.acquisition_service import acquisition_service
from models.analytics_models import UserData, LetterSessionData
from models.feedback_models import LetterFeedbackData, LetterIterationImprovement
from utils.validators import InputValidator, ValidationMiddleware
from utils.keyboards import get_feedback_keyboard, get_iteration_keyboard, get_final_letter_keyboard, get_retry_keyboard, get_start_work_keyboard, get_premium_info_keyboard, get_post_generation_keyboard, get_limit_reached_keyboard, get_iteration_upsell_keyboard
from utils.database import save_user_consent, get_user_consent_status
from utils.rate_limiter import rate_limit, rate_limiter
from config import RATE_LIMITING_ENABLED, ADMIN_TELEGRAM_IDS
import asyncio

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
            """🚀 <b>КАК ПОЛУЧИТЬ РАБОТУ БЫСТРЕЕ?</b>

❌ <b>Проблема:</b> Шаблонные письма игнорируют.
✅ <b>Решение:</b> Персональные письма получают ответы.

🎯 <b>/start</b> - Создать письмо-магнит для HR.
💎 <b>/premium</b> - Получить в 7 раз больше писем и лучшее качество.
📞 <b>/support</b> - Связаться с создателями.

⚡ <b>Процесс простой:</b>
1. Скидываешь вакансию.
2. Скидываешь резюме.
3. Через 30 секунд получаешь письмо, которое цепляет.""",
            parse_mode='HTML'
        )
        

@rate_limit('commands')
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Информация о боте"""
    if update.message:
        # Отправляем информацию частями для лучшего отображения
        await update.message.reply_text(
            """🤖 <b>СЕКРЕТ ПИСЕМ, КОТОРЫЕ ЧИТАЮТ ДО КОНЦА</b>

❌ <b>99% соискателей пишут так:</b>
"Здравствуйте! Меня заинтересовала ваша вакансия..."
(HR засыпает на первой строчке)

✅ <b>Мы пишем так:</b>
"В вашей вакансии Junior разработчика меня зацепило требование знания Python. За последний год я как раз создал 3 проекта на этом стеке..."
(HR читает дальше!)

🔥 <b>ПОЧЕМУ ЭТО РАБОТАЕТ:</b>
• Анализируем каждое слово вакансии.
• Находим "крючки", важные для HR.
• Подсвечиваем ваши сильные стороны и конкретику.
• Работаем на GPT-4o + Claude-3.5 для максимального качества.

🎯 <b>Ваш результат:</b> экономия 2 часов на каждом письме и больше приглашений на собеседования.""",
            parse_mode='HTML'
        )
        

@rate_limit('commands')
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Контакты поддержки"""
    if update.message:
        await update.message.reply_text(
            """📞 <b>ЕСТЬ ВОПРОС? НУЖНА ПОМОЩЬ?</b>

💎 Хотите подключить Premium?
💡 Есть идея, как сделать бота лучше?
🐛 Что-то пошло не так?

✉️ <b>Пишите напрямую создателю:</b> @shoodyakoff

⚡ Отвечаю быстро и помогаю решить любые вопросы. Каждое обращение делает бот лучше!""",
            parse_mode='HTML'
        )


@rate_limit('commands')
async def start_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога v6.0"""
    logger.info("🚀 Начинаем диалог v6.0")
    
    # Защита от двойных нажатий - сохраняем важные данные перед очисткой
    saved_improvement_session_id = None
    if context.user_data is not None:
        # Сохраняем ID сессии улучшения если есть
        saved_improvement_session_id = context.user_data.get('improvement_session_id')
        
        context.user_data.clear()
        # Устанавливаем флаги активной сессии и инициализации
        context.user_data['conversation_state'] = 'active'
        context.user_data['initialized'] = True  # ВСЕГДА устанавливаем для ConversationHandler
        
        # Восстанавливаем ID сессии улучшения если был, но БЕЗ активного режима
        if saved_improvement_session_id:
            context.user_data['improvement_session_id'] = saved_improvement_session_id
            # НЕ восстанавливаем in_improvement_mode - пользователь начинает новую сессию
            logger.info(f"🔄 Restored improvement_session_id: {saved_improvement_session_id} (without active mode)")
    
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
{time_greeting}, {user_name}! Устал от отказов и шаблонных писем?

Я пишу сопроводительные, от которых HR не может оторваться. Я знаю, что работает, потому что проанализировал тысячи успешных кейсов.

<b>Что от тебя нужно:</b>
1. Полный текст вакансии.
2. Твоё резюме.

Через 30 секунд у тебя будет письмо, которое выделит тебя среди сотен других.

<b>Начнём с вакансии.</b> Просто скопируй текст с HeadHunter или сайта компании.
"""
        # Помечаем что показали полное объяснение
        if context.user_data is not None:
            context.user_data['shown_full_intro'] = True
    else:
        # Сокращенное сообщение для повторных использований
        message = f"""
{time_greeting}, {user_name}! Снова за дело?

Давай напишем еще одно письмо, которое принесет тебе приглашение на собеседование.

<b>Начнём с вакансии.</b> Просто скопируй текст.
"""
    
    # Добавляем информацию о подписке и лимитах
    if user_id:
        # Убеждаемся что подписка существует (исправление проблемы 3)
        subscription = await analytics.get_or_create_subscription(user_id)
        if not subscription:
            logger.error(f"❌ Critical: Failed to create subscription for user {user_id}")
        
        # ИСПРАВЛЕНИЕ: Принудительно сбрасываем лимиты если период истек
        await subscription_service._check_and_reset_period(user_id)
        
        limits = await subscription_service.check_user_limits(user_id, force_refresh=True)
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
    
    # Проверяем согласие пользователя для показа соответствующего текста
    user_id = None
    if context.user_data is not None:
        user_id = context.user_data.get('analytics_user_id')
    
    logger.info(f"🔍 RAILWAY DEBUG: Checking consent for user_id: {user_id}")
    
    # Проверяем флаг согласия в БД
    consent_given = False
    if user_id:
        try:
            logger.info(f"🔍 RAILWAY DEBUG: Calling get_user_consent_status...")
            consent_status = await get_user_consent_status(user_id)
            logger.info(f"🔍 RAILWAY DEBUG: consent_status result: {consent_status}")
            if consent_status and consent_status.get('consent_given'):
                consent_given = True
                logger.info(f"🔍 RAILWAY DEBUG: consent_given = True")
            else:
                logger.info(f"🔍 RAILWAY DEBUG: consent_given = False")
        except Exception as e:
            logger.error(f"❌ Error checking consent status: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    logger.info(f"🔍 RAILWAY DEBUG: Final consent_given: {consent_given}")
    
    # Формируем текст в зависимости от статуса согласия
    if consent_given:
        # Обычный текст для пользователей с согласием
        message_text = (
            """✅ <b>Отлично! Вакансию изучил.</b>

Уже вижу, на какие ключевые требования HR нужно сделать акцент в письме.

<b>Шаг 2 из 2:</b> Теперь скинь своё резюме.

Можно просто скопировать текст с HeadHunter или из файла. Чем больше деталей, тем точнее "выстрелим" в сердце работодателя."""
        )
    else:
        # Текст с согласием для новых пользователей
        message_text = (
            """✅ <b>Отлично! Вакансию изучил.</b>

Уже вижу, на какие ключевые требования HR нужно сделать акцент в письме.

<b>Шаг 2 из 2:</b> Теперь скинь своё резюме.

Можно просто скопировать текст с HeadHunter или из файла. Чем больше деталей, тем точнее "выстрелим" в сердце работодателя.

💡 <b>Продолжая работу с ботом, вы соглашаетесь с:</b>
• 📄 Политика конфиденциальности: https://clck.ru/3Mnzwf
• 📋 Пользовательское соглашение: https://clck.ru/3MnztY

🔒 <b>Ваши данные НЕ сохраняются после генерации письма</b>"""
        )
    
    logger.info(f"🔍 RAILWAY DEBUG: Sending message and returning WAITING_RESUME")
    await update.message.reply_text(message_text, parse_mode='HTML')
    
    logger.info(f"🔍 RAILWAY DEBUG: handle_vacancy completed successfully, returning WAITING_RESUME")
    return WAITING_RESUME


@rate_limit('ai_requests', check_text_size=True)
@ValidationMiddleware.require_initialization
@ValidationMiddleware.require_text_message
async def handle_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка резюме и запуск генерации письма"""
    if not update.message or not update.message.text or not update.message.from_user:
        return WAITING_RESUME

    telegram_user_id = update.message.from_user.id
    resume_text = update.message.text
    
    # Проверка длины резюме
    is_valid, error_msg = InputValidator.validate_resume_text(resume_text)
    if not is_valid:
        await update.message.reply_text(error_msg, parse_mode='HTML')
        return WAITING_RESUME

    if context.user_data is not None:
        context.user_data['resume'] = resume_text

    # Получаем внутренний user_id для проверки лимитов
    analytics_user_id = context.user_data.get('analytics_user_id') if context.user_data else None
    if not analytics_user_id:
        logger.error(f"❌ No analytics_user_id found for telegram_user {telegram_user_id}")
        await update.message.reply_text("❌ Ошибка: не удалось определить пользователя. Попробуйте /start")
        return WAITING_RESUME

    # Получаем лимиты пользователя, чтобы определить max_iterations
    limits = await subscription_service.check_user_limits(analytics_user_id)
    
    # Устанавливаем лимит итераций в зависимости от тарифа
    if limits and limits.get('plan_type') == 'premium':
        max_iterations = 3  # Premium: 1 основная + 2 итерации правок
    else:
        max_iterations = 2  # Free: 1 основная + 1 итерация правок

    processing_msg = await update.message.reply_text(
        """🚀 <b>МАГИЯ НАЧАЛАСЬ!</b>

⚡ <b>Что происходит прямо сейчас:</b>
- Анализирую требования работодателя.
- Нахожу пересечения с твоим опытом.
- Формирую цепляющий заголовок и структуру.
- Добавляю эмоцию и факты.

⏳ <b>Осталось 30 секунд...</b>

💎 *Создаю то самое письмо, которое HR прочитает до конца.*""",
        parse_mode='HTML'
    )
    
    if context.user_data:
        vacancy_text = context.user_data.get('vacancy_text', '')
        asyncio.create_task(
            _process_and_respond(
                update, 
                context, 
                processing_msg, 
                analytics_user_id, 
                vacancy_text, 
                resume_text,
                max_iterations=max_iterations
            )
        )

    return WAITING_FEEDBACK

def _is_error_response(generated_letter: str) -> bool:
    """Проверяет, является ли ответ от Claude ошибкой или запросом дополнительной информации"""
    if not generated_letter or len(generated_letter.strip()) < 50:
        return True
    
    generated_lower = generated_letter.lower()
    
    # Прямые индикаторы ошибки (высокая точность)
    error_indicators = [
        "не вижу в предоставленных входных данных",
        "отсутствует описание вакансии",
        "мне нужно:",
        "предоставьте, пожалуйста",
        "извините, но я не вижу",
        "у меня есть только",
        "необходимо предоставить",
        "чтобы создать действительно эффективное"
    ]
    
    # Проверяем наличие прямых индикаторов ошибок
    for indicator in error_indicators:
        if indicator.lower() in generated_lower:
            return True
    
    # Улучшенная проверка: короткое сообщение с множественными вопросами
    question_count = generated_letter.count('?')
    if len(generated_letter) < 200 and question_count >= 2:
        return True
    
    # Проверка на запрос дополнительной информации (более точная)
    request_phrases = ['нужно', 'требуется', 'необходимо']
    request_count = sum(1 for phrase in request_phrases if phrase in generated_lower)
    if len(generated_letter) < 300 and request_count >= 2:
        return True
    
    # Проверка на отсутствие структуры письма
    if len(generated_letter) < 150 and not any(word in generated_lower for word in ['уважением', 'опыт', 'компания', 'позиция']):
        return True
    
    return False


async def _process_and_respond(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE, 
    processing_msg: Message, 
    user_id: int, 
    vacancy_text: str, 
    resume_text: str,
    max_iterations: int
):
    """Приватная корутина для фоновой обработки"""
    if not update.effective_user:
        logger.error("Не удалось получить effective_user в _process_and_respond")
        return

    is_generation_successful = False
    generated_letter = None
    session_id = None
    iteration_status = None
    
    try:
        start_time = time.time()
        # Создаем сессию аналитики
        session_data = LetterSessionData(
            user_id=user_id,
            mode="v6.0",
            job_description=vacancy_text,
            job_description_length=len(vacancy_text),
            resume_text=resume_text,
            resume_length=len(resume_text),
            max_iterations=max_iterations
        )
        session_id = await analytics.create_letter_session(session_data)

        # Проверяем лимиты пользователя
        limits = await subscription_service.check_user_limits(user_id)
        if limits and not limits.get('can_generate'):
            await processing_msg.edit_text(
                subscription_service.format_limit_message(limits),
                reply_markup=get_premium_info_keyboard()
            )
            return

        # Проверяем что session_id не None
        if not session_id:
            logger.error("❌ session_id is None, cannot proceed")
            await processing_msg.edit_text("❌ Ошибка создания сессии. Попробуйте /start")
            return

        generated_letter = await generate_simple_letter(vacancy_text, resume_text, user_id=user_id, session_id=session_id)
        generation_time = int(time.time() - start_time)
        
        await processing_msg.delete()

        # Проверяем качество ответа - не только наличие текста, но и отсутствие ошибок
        is_generation_successful = bool(generated_letter) and not _is_error_response(generated_letter)

        if is_generation_successful:
            await update.effective_user.send_message(
                f"✍️ <b>ПИСЬМО:</b>\n\n{generated_letter}",
                parse_mode='HTML'
            )
            # Увеличиваем счетчик использованных писем при успешной генерации
            await subscription_service.increment_usage(user_id)
            await analytics.update_letter_session(session_id, {
                'generated_letter': generated_letter[:2000],
                'generated_letter_length': len(generated_letter),
                'generation_time_seconds': generation_time,
                'status': 'completed'
            })
        else:
            # Для ошибочных ответов показываем сам ответ Claude (с объяснением проблемы)
            if generated_letter:
                await update.effective_user.send_message(
                    f"⚠️ <b>ВНИМАНИЕ:</b>\n\n{generated_letter}",
                    parse_mode='HTML'
                )
            await analytics.update_letter_session(session_id, {'status': 'failed'})

        iteration_status = await feedback_service.get_session_iteration_status(session_id)
        
        # Формируем сообщение и кнопки
        if is_generation_successful:
            feedback_message = f"""🎉 <b>ПИСЬМО-МАГНИТ ГОТОВО! ({generation_time} сек)</b>

🎯 <b>Что получилось:</b>
- Письмо заточено под эту вакансию.
- Подсвечены твои сильные стороны.
- Добавлены ключевые слова, которые ищет HR.

💡 <b>Как тебе?</b>
• ❤️ <b>Супер!</b> - Готов отправлять.
• 👎 <b>Нужно доработать</b> - Давай улучшим.

🚀 *Твоя оценка помогает мне писать еще круче!*"""
            keyboard = get_post_generation_keyboard(session_id, iteration_status.current_iteration if iteration_status else 1)
        else:
            feedback_message = """❌ <b>Упс! Что-то пошло не так</b>

🔧 <b>Не переживайте, такое иногда бывает:</b>
• 🔄 Повторить попытку - часто помогает
• 🆕 Начать заново - с новыми данными

💪 <b>Каждая попытка улучшает результат!</b>

💡 <i>Попробуйте сделать описание вакансии и резюме более подробными</i>"""
            keyboard = get_retry_keyboard(session_id)

        await update.effective_user.send_message(
            feedback_message,
            parse_mode='HTML',
            reply_markup=keyboard
        )

        if context.user_data:
            context.user_data['session_id_for_feedback'] = session_id
            context.user_data['session_id_for_improvement'] = session_id
            # ИСПРАВЛЕНИЕ v9.10: Сохраняем session_id для возможности улучшения
            if is_generation_successful:
                context.user_data['improvement_session_id'] = session_id
                logger.info(f"💾 Saved improvement_session_id: {session_id}")

    except Exception as e:
        logger.error(f"Ошибка в _process_and_respond: {e}", exc_info=True)
        try:
            await processing_msg.delete()
            await update.effective_user.send_message(
                "❌ Произошла критическая ошибка. Попробуйте /start снова."
            )
        except Exception as e_inner:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю: {e_inner}")

    # Состояние ожидания обратной связи
    # return WAITING_FEEDBACK # Это не работает в create_task, состояние устанавливается в родительской функции


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога"""
    if context.user_data is not None:
        context.user_data.clear()
    
    if update.message:
        await update.message.reply_text(
            """❌ <b>Создание письма остановлено.</b>

Жаль, что мы не закончили.

Если передумаешь, я всегда здесь. Просто нажми /start.

🚀 *Помни: каждое хорошее письмо — это шаг к работе мечты!*""",
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
    
    # ИСПРАВЛЕНИЕ v9.10: Сохраняем session_id для возможности улучшения
    if context.user_data and iteration_status.can_iterate:
        context.user_data['improvement_session_id'] = session_id
        logger.info(f"💾 Saved improvement_session_id from feedback: {session_id}")
    
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
    
    # UPSELL TOUCHPOINT - показываем premium предложение при повторных запросах
    keyboard = get_iteration_upsell_keyboard(session_id, iteration_status.remaining_iterations)
    
    # Трекаем показ premium предложения
    if user_id:
        await analytics.track_premium_offer_shown(user_id, 'iteration')
    
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
        # ИСПРАВЛЕНИЕ v9.10: Устанавливаем флаг активного режима улучшения
        context.user_data['in_improvement_mode'] = True
        logger.info(f"🔄 Entered improvement mode for session {session_id}")
        
        # Восстанавливаем данные из сессии если их нет в context
        if not context.user_data.get('vacancy_text') or not context.user_data.get('resume_text'):
            logger.info("🔍 Восстанавливаем данные из сессии...")
            try:
                session_response = await analytics.get_letter_session_by_id(session_id)
                if session_response:
                    context.user_data['vacancy_text'] = session_response.get('job_description', '')
                    context.user_data['resume_text'] = session_response.get('resume_text', '')
                    logger.info("✅ Данные восстановлены из сессии")
                else:
                    logger.error("❌ Сессия не найдена в БД")
                    await query.edit_message_text(
                        "❌ <b>Сессия не найдена</b>\n\n"
                        "Создайте новое письмо: /start",
                        parse_mode='HTML'
                    )
                    return ConversationHandler.END
            except Exception as e:
                logger.error(f"❌ Ошибка восстановления данных: {e}")
                await query.edit_message_text(
                    "❌ <b>Ошибка восстановления данных</b>\n\n"
                    "Создайте новое письмо: /start",
                    parse_mode='HTML'
                )
                return ConversationHandler.END
    
    # НОВАЯ ЛОГИКА: показываем только текст БЕЗ кнопок
    prompt_text = feedback_service.get_improvement_prompt_text(iteration_status.remaining_iterations)
    
    await query.edit_message_text(
        """🔄 <b>ПОНЯЛ. ДАВАЙ СДЕЛАЕМ ЕГО ИДЕАЛЬНЫМ.</b>

Что именно поправить? Чем конкретнее, тем лучше.

<b>Например:</b>
- "Больше про мой опыт с Python"
- "Сделай тон более официальным"
- "Убери упоминание про фриланс"

✍️ *Напиши свои пожелания одним сообщением...*""",
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
            
            # SOFT SELL TOUCHPOINT - после retry генерации
        keyboard = get_post_generation_keyboard(session_id, iteration_status.current_iteration if iteration_status else 1)
        
        # Трекаем показ premium предложения
        if user_id:
            await analytics.track_premium_offer_shown(user_id, 'post_generation')
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
            # НЕ увеличиваем счетчик - это повторная генерация, не новое письмо
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
    """Обработка запроса на улучшение письма"""
    if not update.message or not update.message.text or not context.user_data or not update.message.from_user:
        return WAITING_IMPROVEMENT_REQUEST

    # Получаем internal_user_id из context, а не telegram_user_id из update
    user_id = context.user_data.get('analytics_user_id')
    if not user_id:
        logger.error("❌ No analytics_user_id in context for improvement request")
        await update.message.reply_text("❌ Ошибка авторизации. Начните заново: /start")
        return ConversationHandler.END
        
    session_id = context.user_data.get('improvement_session_id')
    improvement_request = update.message.text
    
    if not session_id:
        await update.message.reply_text("❌ Не могу найти исходное письмо для улучшения. Начните заново /start")
        context.user_data.clear()
        return ConversationHandler.END

    iteration_status = await feedback_service.get_session_iteration_status(session_id)
    if not iteration_status or not iteration_status.can_iterate:
        await update.message.reply_text(
            "❌ Вы уже использовали все доступные улучшения для этого письма. "
            "Чтобы получить больше правок, рассмотрите /premium или создайте новое письмо через /start."
        )
        context.user_data.clear()
        return ConversationHandler.END

    processing_msg = await update.message.reply_text(
        "🔄 <b>Улучшаю письмо с учетом ваших пожеланий...</b>\n\n"
        "Это займет около 20-30 секунд.",
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
        
        # Получаем vacancy_text из context
        vacancy_text = context.user_data.get('vacancy_text', '')
        if not vacancy_text:
            logger.error("❌ vacancy_text not found in context")
            await processing_msg.edit_text("❌ Данные вакансии потеряны. Начните заново: /start")
            return WAITING_IMPROVEMENT_REQUEST

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
        await processing_msg.delete()
        
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
                "<b>Premium:</b> 20 писем в день, GPT-4o + Claude-3.5 работают вместе\n\n"
            )
            # SOFT SELL TOUCHPOINT - после улучшения
            keyboard = get_post_generation_keyboard(session_id, iteration_status.current_iteration)
            
            # Трекаем показ premium предложения
            if user_id:
                await analytics.track_premium_offer_shown(user_id, 'post_generation')
        else:
            feedback_message += "✅ Используйте это письмо или создайте новое"
            keyboard = get_final_letter_keyboard()
        
        await update.message.reply_text(
            feedback_message,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        # ИСПРАВЛЕНИЕ v9.10: Очищаем флаг активного режима улучшения после завершения
        if context.user_data:
            context.user_data.pop('in_improvement_mode', None)
            logger.info("🔄 Cleared in_improvement_mode flag after improvement completion")
        
    except Exception as e:
        logger.error(f"❌ Ошибка улучшения письма: {e}")
        
        try:
            await processing_msg.delete()
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
            """💡 <b>Используйте кнопки выше для оценки письма</b>

👆 <b>Нажмите:</b>
• ❤️ если письмо понравилось
• 👎 если нужно переделать
• 🔄 чтобы попробовать еще раз

🆕 <b>Или создайте новое письмо: /start</b>

⚡ <i>Кнопки работают быстрее текстовых команд!</i>""",
            parse_mode='HTML'
        )
    return WAITING_FEEDBACK


# ========================================
# ОБРАБОТЧИКИ СОГЛАСИЯ НА ОБРАБОТКУ ПД - УДАЛЕНЫ
# Теперь используется неявное согласие через действие
# ========================================


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
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_resume)
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
        # PREMIUM команда v9.3
        CommandHandler("premium", premium_command),
        # СКРЫТЫЕ команды (НЕ отображаются в меню)
        CommandHandler("privacy", privacy_command),
        CommandHandler("terms", terms_command),
        # Обработчик кнопки создания письма вне сессии
        CallbackQueryHandler(handle_start_work_callback, pattern=r'^start_work$'),
        # Обработчик кнопки "Вернуться к боту"
        CallbackQueryHandler(handle_back_to_bot, pattern=r'^back_to_bot$'),
        # PREMIUM CALLBACK HANDLERS v9.3
        CallbackQueryHandler(handle_premium_inquiry, pattern=r'^premium_inquiry$'),
        CallbackQueryHandler(handle_contact_support, pattern=r'^contact_support$'),
        CallbackQueryHandler(handle_premium_info, pattern=r'^premium_info$'),
        CallbackQueryHandler(handle_unlock_limits, pattern=r'^unlock_limits$'),
        CallbackQueryHandler(handle_back_to_premium, pattern=r'^back_to_premium$'),
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
                limit_info += f"\n🚫 <b>Лимит бесплатных писем исчерпан</b> ({limits['used']}/{limits['limit']})\n💎 Premium дает 20 писем в день + лучшее качество"
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
    
    # Создаем клавиатуру - показываем premium кнопки если лимит исчерпан
    if context.user_data and context.user_data.get('analytics_user_id'):
        user_id = context.user_data['analytics_user_id']
        try:
            limits = await subscription_service.check_user_limits(user_id)
            if not limits['can_generate']:
                # ГЛАВНЫЙ TOUCHPOINT - при исчерпании лимита
                from utils.keyboards import get_limit_reached_keyboard
                keyboard = get_limit_reached_keyboard()
                
                # Трекаем показ premium предложения
                await analytics.track_premium_offer_shown(user_id, 'limit_reached')
            else:
                keyboard = get_start_work_keyboard()
        except Exception as e:
            logger.error(f"Error checking limits for keyboard: {e}")
            keyboard = get_start_work_keyboard()
    else:
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
    """Обработчик кнопки 'Вернуться к боту' (исправленная логика v9.11)"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer("Возвращаемся к боту...")
    
    in_improvement_mode = context.user_data.get('in_improvement_mode') if context.user_data else False
    improvement_session_id = context.user_data.get('improvement_session_id') if context.user_data else None
    
    # СЛУЧАЙ 1: Активный режим улучшения
    if in_improvement_mode and improvement_session_id:
        # Возвращаемся к экрану улучшения письма
        from services.feedback_service import feedback_service
        
        try:
            iteration_status = await feedback_service.get_session_iteration_status(improvement_session_id)
            if iteration_status and iteration_status.can_iterate:
                await query.edit_message_text(
                    """🔄 <b>ПОНЯЛ. ДАВАЙ СДЕЛАЕМ ЕГО ИДЕАЛЬНЫМ.</b>

Что именно поправить? Чем конкретнее, тем лучше.

<b>Например:</b>
- "Больше про мой опыт с Python"
- "Сделай тон более официальным"
- "Убери упоминание про фриланс"

✍️ *Напиши свои пожелания одним сообщением...*""",
                    parse_mode='HTML'
                )
                logger.info(f"🔄 Returned to improvement screen for session {improvement_session_id}")
                return
        except Exception as e:
            logger.error(f"Error returning to improvement screen: {e}")
    
    # СЛУЧАЙ 2: Есть активная сессия письма (НО НЕ в режиме улучшения)
    if improvement_session_id:
        # Возвращаемся к экрану с кнопками оценки письма
        from services.feedback_service import feedback_service
        
        try:
            iteration_status = await feedback_service.get_session_iteration_status(improvement_session_id)
            if iteration_status:
                feedback_message = f"""❤️ <b>Спасибо за оценку!</b>

🙏 Мы ценим ваш отзыв! Это помогает нам создавать лучшие письма.

🔄 <b>У вас есть ещё {iteration_status.remaining_iterations} итерации правок</b> для этой пары вакансия-резюме, или можете создать новое письмо для другой вакансии.

💡 <b>Что вы хотите сделать дальше?</b>"""
                
                keyboard = get_iteration_upsell_keyboard(improvement_session_id, iteration_status.remaining_iterations)
                
                await query.edit_message_text(
                    feedback_message,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                logger.info(f"🔄 Returned to feedback screen for session {improvement_session_id}")
                return
        except Exception as e:
            logger.error(f"Error returning to feedback screen: {e}")
    
    # СЛУЧАЙ 3: Обычный возврат к стартовому экрану
    await query.edit_message_text(
        "👋 <b>Добро пожаловать обратно!</b>\n\n"
        "🎯 <b>Готовы создать сопроводительное письмо?</b>\n\n"
        "💡 Нажмите /start чтобы начать",
        parse_mode='HTML'
    )


# ============================================================================
# MONETIZATION HANDLERS v9.3
# ============================================================================

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /premium - информация о Premium подписке"""
    if not update.message:
        return
    
    user = update.effective_user
    user_id = None
    if user:
        user_id = await analytics.get_user_id(user.id)
        if user_id:
            await analytics.track_premium_info_viewed(user_id, source='command')
    
    premium_text = """
<b>ГЛАВНЫЙ ЗАКОН НАЙМА: УНИКАЛЬНЫЕ ПИСЬМА → БОЛЬШЕ СОБЕСЕДОВАНИЙ</b>

Рассылать индивидуальные письма в каждую компанию нереально тяжело. Ещё тестовые делать, собеседоваться. А жить когда?

Мы сделали бота, который пишет человечные письма за тебя. Обучен на промптах от HR и копирайтеров: изучает вакансию, твой опыт и создает письмо, которое не отличить от человеческого.

<b>🆓 БЕСПЛАТНО</b>
3 письма в месяц
Базовый GPT-4o

<b>💎 PREMIUM</b>
20 писем в день
GPT-4o + Claude-3.5 работают вместе
Двойная проверка = выше качество

<b>199 рублей/месяц</b>

Можешь пользоваться бесплатно, можешь инвестировать в скорость. Когда найдешь работу мечты — окупится в тысячи раз.

Попробовать Premium — пиши @shoodyakoff
"""
    
    keyboard = get_premium_info_keyboard()
    
    await update.message.reply_text(
        premium_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )


async def handle_premium_inquiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Получить Premium'"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer("Переходим к оформлению Premium...")
    
    user = update.effective_user
    user_id = None
    if user:
        user_id = await analytics.get_user_id(user.id)
        if user_id:
            await analytics.track_premium_button_clicked(user_id, 'premium_inquiry', 'button')
            await analytics.track_contact_initiated(user_id)
    
    await query.edit_message_text(
        "<b>Получить Premium за 199₽/месяц</b>\n\n"
        "Напишите @shoodyakoff:\n"
        "\"Хочу Premium подписку\"\n\n"
        "Активация в течение часа после оплаты",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_premium")]
        ])
    )


async def handle_contact_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Связаться с нами'"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer("Переходим к контактам...")
    
    user = update.effective_user
    user_id = None
    if user:
        user_id = await analytics.get_user_id(user.id)
        if user_id:
            await analytics.track_premium_button_clicked(user_id, 'contact_support', 'button')
            await analytics.track_contact_initiated(user_id)
    
    await query.edit_message_text(
        "<b>Связаться с нами</b>\n\n"
        "Telegram: @shoodyakoff\n\n"
        "Отвечаем в течение 2-4 часов",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_premium")]
        ])
    )


async def handle_premium_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Узнать больше о Premium'"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer("Показываем информацию о Premium...")
    
    user = update.effective_user
    user_id = None
    if user:
        user_id = await analytics.get_user_id(user.id)
        if user_id:
            await analytics.track_premium_button_clicked(user_id, 'premium_info', 'post_generation')
            await analytics.track_premium_info_viewed(user_id, source='button')
    
    premium_info = """
<b>ЗАКОН РЫНКА НАЙМА: БОЛЬШЕ ОТКЛИКОВ — БОЛЬШЕ ШАНСОВ</b>

Рассылать индивидуальные письма в каждую компанию нереально тяжело. Ещё тестовые делать, собеседоваться. А жить когда?

Мы сделали бота, который пишет человечные письма за тебя. Обучен на промптах от HR и копирайтеров: изучает вакансию, твой опыт и создает письмо, которое не отличить от человеческого.

<b>🆓 БЕСПЛАТНО</b>
3 письма в месяц
Базовый GPT-4o
1 улучшение письма

<b>💎 PREMIUM</b>
20 писем в день
GPT-4o + Claude-3.5 работают вместе
Двойная проверка = выше качество
3 улучшения письма

<b>199 рублей/месяц</b>

Можешь пользоваться бесплатно, можешь инвестировать в скорость. Когда найдешь работу мечты — окупится в тысячи раз.

Попробовать Premium — пиши @shoodyakoff
"""
    
    keyboard = get_premium_info_keyboard()
    
    await query.edit_message_text(
        premium_info,
        parse_mode='HTML',
        reply_markup=keyboard
    )


async def handle_unlock_limits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показываем полный Premium экран (упрощенная логика v9.10)"""
    await handle_premium_info(update, context)


async def handle_back_to_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат к экрану Premium информации (исправленная логика v9.11)"""
    # Просто возвращаемся к экрану Premium информации
    await handle_premium_info(update, context)


 