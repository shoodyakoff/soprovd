"""
Персонализированный диалог с анализом профиля и предложением стиля
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from services.profile_analyzer import analyze_profile
from services.personalized_prompt import generate_personalized_prompt
from services.openai_service import generate_letter_with_retry
from models.style_definitions import DEFAULT_STYLES

logger = logging.getLogger(__name__)

# Состояния разговора для персонализированного режима
WAITING_JOB_DESCRIPTION = 10
WAITING_RESUME = 11
ANALYZING_AND_SUGGESTING = 12
WAITING_STYLE_CONFIRMATION = 13
GENERATING_LETTER = 14


async def start_personalized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало персонализированного диалога"""
    if not update.effective_user or not update.message:
        return ConversationHandler.END
        
    logger.info(f"User {update.effective_user.id} started personalized flow")
    
    message = """🎯 <b>Персонализированный генератор писем</b>

Я проанализирую вашу профессию и уровень, чтобы подобрать идеальный стиль письма!

<b>Как это работает:</b>
1️⃣ Вы присылаете описание вакансии
2️⃣ Затем ваше резюме  
3️⃣ Я анализирую и предлагаю стиль
4️⃣ Генерирую персонализированное письмо

Готовы? Пришлите описание вакансии 👇"""

    await update.message.reply_text(message, parse_mode='HTML')
    return WAITING_JOB_DESCRIPTION


async def receive_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение описания вакансии"""
    logger.info(f"🔥 receive_job_description вызвана! User: {update.effective_user.id if update.effective_user else None}")
    
    if not update.effective_user or not update.message:
        logger.error(f"❌ Missing data: user={update.effective_user}, message={update.message}")
        return ConversationHandler.END
        
    job_description = update.message.text.strip() if update.message.text else ""
    logger.info(f"🔥 Получено описание вакансии длиной {len(job_description)} символов")
    
    # Проверка длины
    if len(job_description) < 50:
        await update.message.reply_text(
            "⚠️ Описание вакансии слишком короткое. Пожалуйста, добавьте больше деталей о требованиях и обязанностях."
        )
        return WAITING_JOB_DESCRIPTION
    
    if len(job_description) > 4000:
        await update.message.reply_text(
            "⚠️ Описание вакансии слишком длинное. Сократите до 4000 символов."
        )
        return WAITING_JOB_DESCRIPTION
    
    # Сохраняем данные
    context.user_data['job_description'] = job_description
    
    logger.info(f"User {update.effective_user.id} provided job description ({len(job_description)} chars)")
    
    await update.message.reply_text(
        "✅ Отлично! Теперь пришлите ваше резюме текстом.\n\n"
        "💡 Можете скопировать и вставить его сюда целиком."
    )
    
    return WAITING_RESUME


async def receive_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение резюме и анализ профиля"""
    if not update.effective_user or not update.message:
        return ConversationHandler.END
        
    resume = update.message.text.strip() if update.message.text else ""
    
    # Проверка длины
    if len(resume) < 100:
        await update.message.reply_text(
            "⚠️ Резюме слишком короткое. Добавьте больше информации о вашем опыте и навыках."
        )
        return WAITING_RESUME
    
    if len(resume) > 6000:
        await update.message.reply_text(
            "⚠️ Резюме слишком длинное. Сократите до 6000 символов."
        )
        return WAITING_RESUME
    
    # Сохраняем данные
    context.user_data['resume'] = resume
    
    # Показываем процесс анализа
    analyzing_message = await update.message.reply_text(
        "🔍 <b>Анализирую ваш профиль...</b>\n\n"
        "⏳ Определяю профессию и уровень...",
        parse_mode='HTML'
    )
    
    try:
        # Анализируем профиль
        job_description = context.user_data['job_description']
        profile = analyze_profile(job_description, resume)
        
        # Сохраняем результат анализа
        context.user_data['analyzed_profile'] = profile
        
        logger.info(f"Profile analyzed for user {update.effective_user.id}: {profile.profession}/{profile.level}, confidence: {profile.confidence_score:.2f}")
        
        # Удаляем сообщение о процессе
        await analyzing_message.delete()
        
        # Формируем ответ с результатами анализа
        await send_analysis_results(update, context, profile)
        
        return WAITING_STYLE_CONFIRMATION
        
    except Exception as e:
        logger.error(f"Error analyzing profile for user {update.effective_user.id}: {e}")
        
        await analyzing_message.edit_text(
            "❌ Произошла ошибка при анализе. Попробуйте еще раз или начните заново /start"
        )
        return ConversationHandler.END


async def send_analysis_results(update: Update, context: ContextTypes.DEFAULT_TYPE, profile):
    """Отправляет результаты анализа и предлагает выбор стиля"""
    if not update.message:
        return
    
    # Определяем эмодзи для профессии  
    profession_emoji = get_profession_emoji(profile.profession)
    
    # Определяем уровень на русском
    level_ru = get_level_russian(profile.level)
    
    # Формируем сообщение
    if profile.confidence_score >= 0.7:
        # Высокая уверенность - предлагаем найденный стиль
        message = f"""🎯 <b>Анализ завершен!</b>

{profession_emoji} <b>Профессия:</b> {profile.profession.title()}
📊 <b>Уровень:</b> {level_ru}
📈 <b>Уверенность:</b> {profile.confidence_score:.0%}

💡 <b>Рекомендуемый стиль:</b> 
<i>"{profile.suggested_style.tone_description}"</i>

Как поступим?"""
        
        # Создаем кнопки
        keyboard = [
            [InlineKeyboardButton("✅ Окей, подходит", callback_data="style_accept")],
            [InlineKeyboardButton("🎨 Хочу креативнее", callback_data="style_creative")],
            [InlineKeyboardButton("📘 Строже, формально", callback_data="style_formal")]
        ]
        
    else:
        # Низкая уверенность - предлагаем выбрать стиль вручную
        message = f"""🤔 <b>Не удалось точно определить стиль</b>

{profession_emoji} <b>Профессия:</b> {profile.profession.title() if profile.profession != 'unknown' else 'Не определена'}
📊 <b>Уровень:</b> {level_ru}

Выберите подходящий стиль письма:"""
        
        keyboard = [
            [InlineKeyboardButton("⚖️ Нейтральный стиль", callback_data="style_neutral")],
            [InlineKeyboardButton("🎨 Креативный стиль", callback_data="style_creative")], 
            [InlineKeyboardButton("📘 Формальный стиль", callback_data="style_formal")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')


def get_profession_emoji(profession: str) -> str:
    """Возвращает эмодзи для профессии"""
    emoji_map = {
        "product manager": "📱",
        "ux/ui designer": "🎨", 
        "frontend developer": "💻",
        "backend developer": "⚙️",
        "qa engineer": "🔍",
        "product analyst": "📊",
        "business analyst": "📈",
        "marketing specialist": "📢",
        "cto": "🏗️",
        "head of design": "🎨",
        "cpo": "🚀",
        "unknown": "🤷‍♂️"
    }
    return emoji_map.get(profession, "💼")


def get_level_russian(level: str) -> str:
    """Переводит уровень на русский"""
    level_map = {
        "junior": "Junior",
        "middle": "Middle", 
        "senior": "Senior",
        "lead": "Lead",
        "c-level": "C-Level"
    }
    return level_map.get(level, level.title())


def get_style_name(style: str) -> str:
    """Возвращает название стиля на русском"""
    style_names = {
        "neutral": "нейтральный",
        "creative": "креативный",
        "confident": "уверенный",
        "formal": "формальный"
    }
    return style_names.get(style, style)


def get_profession_display(profession: str) -> str:
    """Возвращает отображаемое название профессии"""
    if profession == "unknown":
        return "универсальный профиль"
    
    profession_map = {
        "product manager": "Product Manager",
        "ux/ui designer": "UX/UI Designer",
        "frontend developer": "Frontend Developer",
        "backend developer": "Backend Developer",
        "qa engineer": "QA Engineer",
        "product analyst": "Product Analyst",
        "business analyst": "Business Analyst",
        "marketing specialist": "Marketing Specialist",
        "cto": "CTO",
        "head of design": "Head of Design",
        "cpo": "CPO"
    }
    return profession_map.get(profession, profession.title())


async def handle_style_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора стиля"""
    if not update.callback_query or not update.effective_user or not update.effective_chat or not context.user_data:
        return ConversationHandler.END
        
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    profile = context.user_data.get('analyzed_profile')
    
    if not profile:
        await query.edit_message_text("❌ Данные потеряны. Начните заново с /start")
        return ConversationHandler.END
    
    # Определяем финальный стиль
    if choice == "style_accept":
        final_style = profile.suggested_style
        style_name = get_style_name(profile.suggested_style.style)
    elif choice == "style_creative":
        final_style = DEFAULT_STYLES["creative"] 
        style_name = "креативный"
    elif choice == "style_formal":
        final_style = DEFAULT_STYLES["formal"]
        style_name = "формальный"  
    elif choice == "style_neutral":
        final_style = DEFAULT_STYLES["neutral"]
        style_name = "нейтральный"
    else:
        await query.edit_message_text("❌ Неизвестный выбор. Попробуйте еще раз.")
        return WAITING_STYLE_CONFIRMATION
    
    # Обновляем профиль с выбранным стилем
    profile.suggested_style = final_style
    context.user_data['analyzed_profile'] = profile
    
    logger.info(f"User {update.effective_user.id} chose {style_name} style")
    
    # Показываем процесс генерации
    await query.edit_message_text(
        f"✅ Выбран {style_name} стиль!\n\n"
        "⏳ <b>Генерирую персонализированное письмо...</b>",
        parse_mode='HTML'
    )
    
    # Генерируем письмо
    try:
        job_description = context.user_data['job_description']
        resume = context.user_data['resume']
        
        # Создаем персонализированный промпт
        personalized_prompt = generate_personalized_prompt(job_description, resume, profile)
        
        # Генерируем письмо с персонализированной температурой
        # Получаем температуру из генератора промптов
        from services.personalized_prompt import prompt_generator
        temperature = prompt_generator._get_temperature(profile.suggested_style)
        
        letter = await generate_letter_with_retry(
            prompt=personalized_prompt, 
            temperature=temperature
        )
        
        if letter:
            # Отправляем результат
            result_message = f"""✅ <b>Ваше персонализированное письмо готово!</b>

<i>Стиль: {style_name}</i>

{letter}

💡 Письмо адаптировано под {get_profession_display(profile.profession)} уровня {get_level_russian(profile.level)}."""

            # Отправляем результат (если слишком длинный, Telegram сам обрежет)
            try:
                await query.edit_message_text(result_message, parse_mode='HTML')
            except Exception as e:
                # Если не удалось отправить длинное сообщение, отправляем по частям
                logger.warning(f"Failed to send long message, splitting: {e}")
                header = f"✅ <b>Ваше персонализированное письмо готово!</b>\n\n<i>Стиль: {style_name}</i>"
                await query.edit_message_text(header, parse_mode='HTML')
                
                # Отправляем письмо через context.bot
                await context.bot.send_message(chat_id=update.effective_chat.id, text=letter)
                
                # Отправляем информацию о профиле
                footer = f"💡 Письмо адаптировано под {get_profession_display(profile.profession)} уровня {get_level_russian(profile.level)}."
                await context.bot.send_message(chat_id=update.effective_chat.id, text=footer)
            
            logger.info(f"Personalized letter generated successfully for user {update.effective_user.id}")
            
        else:
            await query.edit_message_text(
                "❌ Не удалось сгенерировать письмо. Попробуйте еще раз или начните заново с /start"
            )
            
    except Exception as e:
        logger.error(f"Error generating personalized letter for user {update.effective_user.id}: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при генерации письма. Попробуйте еще раз или начните заново с /start"
        )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_personalized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена персонализированного диалога"""
    if not update.effective_user or not update.message or not context.user_data:
        return ConversationHandler.END
        
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Персонализированная генерация отменена.\n\n"
        "Для новой попытки используйте /start"
    )
    logger.info(f"User {update.effective_user.id} canceled personalized flow")
    return ConversationHandler.END 