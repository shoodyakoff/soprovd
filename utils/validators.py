"""
Валидация входных данных для бота Сопровод v7.0
Обработка corner-кейсов и пользовательских ошибок
"""
import re
from typing import Tuple
from telegram import Update


class InputValidator:
    """Валидатор входных данных пользователя"""
    
    # Константы для валидации
    MIN_VACANCY_LENGTH = 100
    MAX_VACANCY_LENGTH = 10000
    MIN_RESUME_LENGTH = 300
    MAX_RESUME_LENGTH = 15000
    
    # Паттерны для обнаружения файловых ссылок (которые нужно блокировать)
    FILE_SHARING_PATTERNS = [
        r'docs\.google\.com',
        r'drive\.google\.com',
        r'dropbox\.com',
        r'yandex\.ru/disk',
        r'cloud\.mail\.ru',
        r'onedrive\.live\.com',
        r'sharepoint\.com'
    ]
    
    @staticmethod
    def validate_user_initialized(context) -> Tuple[bool, str]:
        """Проверяет, что пользователь инициализирован"""
        if not context.user_data or not context.user_data.get('initialized'):
            return False, (
                "👋 Пожалуйста, начните с команды /start, чтобы бот знал, что делать."
            )
        return True, ""
    
    @staticmethod
    def validate_message_type(update: Update) -> Tuple[bool, str]:
        """Проверяет тип сообщения (только текст)"""
        if not update.message:
            return False, "Ошибка обработки сообщения"
            
        message = update.message
        
        # Проверяем на файлы
        if (message.document or message.photo or message.voice or 
            message.video or message.animation or message.sticker or
            message.audio or message.video_note):
            return False, (
                "⚠️ Сейчас бот поддерживает только текст. "
                "Пожалуйста, вставьте текст вручную."
            )
        
        # Проверяем наличие текста
        if not message.text:
            return False, (
                "📝 Пожалуйста, отправьте текстовое сообщение."
            )
            
        return True, ""
    
    @staticmethod
    def validate_vacancy_text(text: str) -> Tuple[bool, str]:
        """Валидация текста вакансии"""
        if not text or not text.strip():
            return False, "📄 Вакансия не может быть пустой"
        
        text_length = len(text.strip())
        
        if text_length < InputValidator.MIN_VACANCY_LENGTH:
            return False, (
                f"❌ <b>Описание вакансии слишком короткое</b>\n\n"
                f"📊 Получено: {text_length} символов\n"
                f"📋 Нужно минимум: {InputValidator.MIN_VACANCY_LENGTH} символов\n\n"
                f"💡 <b>Что добавить:</b>\n"
                f"• Требования к кандидату\n"
                f"• Обязанности\n"
                f"• Условия работы\n"
                f"• Информация о компании"
            )
        
        if text_length > InputValidator.MAX_VACANCY_LENGTH:
            return False, (
                f"❌ <b>Описание вакансии слишком длинное</b>\n\n"
                f"📊 Получено: {text_length} символов\n"
                f"📋 Максимум: {InputValidator.MAX_VACANCY_LENGTH} символов\n\n"
                f"💡 Сократите текст, оставив самое важное"
            )
        
        # Проверяем на файловые ссылки (Google Drive, Dropbox и т.д.)
        if InputValidator._has_file_sharing_links(text):
            return False, (
                "🔗 <b>Обнаружены ссылки на файлы</b>\n\n"
                "Пока что ссылки на Google Drive, Dropbox и другие файловые сервисы не обрабатываются.\n\n"
                "💡 Скопируйте содержимое страницы и вставьте как текст"
            )
        
        return True, ""
    
    @staticmethod
    def validate_resume_text(text: str) -> Tuple[bool, str]:
        """Валидация текста резюме"""
        if not text or not text.strip():
            return False, "📄 Резюме не может быть пустым"
        
        text_length = len(text.strip())
        
        if text_length < InputValidator.MIN_RESUME_LENGTH:
            return False, (
                f"❌ <b>Резюме слишком короткое</b>\n\n"
                f"📊 Получено: {text_length} символов\n"
                f"📋 Нужно минимум: {InputValidator.MIN_RESUME_LENGTH} символов\n\n"
                f"💡 <b>Добавьте в резюме:</b>\n"
                f"• Опыт работы (должности, достижения)\n"
                f"• Навыки и компетенции\n"
                f"• Образование\n"
                f"• Дополнительную информацию"
            )
        
        if text_length > InputValidator.MAX_RESUME_LENGTH:
            return False, (
                f"❌ <b>Резюме слишком длинное</b>\n\n"
                f"📊 Получено: {text_length} символов\n"
                f"📋 Максимум: {InputValidator.MAX_RESUME_LENGTH} символов\n\n"
                f"💡 Сократите текст, оставив самое важное"
            )
        
        # Для резюме ссылки разрешены (сайты компаний, портфолио и т.д.)
        # Проверка ссылок убрана
        
        return True, ""
    
    @staticmethod
    def _has_file_sharing_links(text: str) -> bool:
        """Проверяет наличие файловых ссылок в тексте"""
        text_lower = text.lower()
        return any(
            re.search(pattern, text_lower) 
            for pattern in InputValidator.FILE_SHARING_PATTERNS
        )
    
    @staticmethod
    def sanitize_for_logging(text: str) -> str:
        """Санитизация текста для логирования (убираем PII)"""
        # Убираем номера карт
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', text)
        
        # Убираем email адреса  
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Убираем номера телефонов
        text = re.sub(r'\b\+?[1-9]\d{1,14}\b', '[PHONE]', text)
        
        # Убираем ИНН
        text = re.sub(r'\b\d{10,12}\b', '[INN]', text)
        
        return text


class ValidationMiddleware:
    """Middleware для автоматической валидации"""
    
    @staticmethod
    def require_initialization(func):
        """Декоратор для проверки инициализации пользователя"""
        async def wrapper(update, context):
            import logging
            logger = logging.getLogger(__name__)
            
            # Пропускаем проверку для команды /start
            if update.message and update.message.text == '/start':
                logger.info("🔍 VALIDATOR: Skipping initialization check for /start command")
                return await func(update, context)
            
            logger.info(f"🔍 VALIDATOR: Checking initialization for function {func.__name__}")
            logger.info(f"🔍 VALIDATOR: context.user_data = {context.user_data}")
            
            is_valid, error_msg = InputValidator.validate_user_initialized(context)
            logger.info(f"🔍 VALIDATOR: is_valid = {is_valid}, error_msg = '{error_msg}'")
            
            if not is_valid and update.message:
                logger.warning(f"🔍 VALIDATOR: Blocking {func.__name__} due to initialization check")
                await update.message.reply_text(error_msg, parse_mode='HTML')
                return
            
            logger.info(f"🔍 VALIDATOR: Initialization check passed, calling {func.__name__}")
            return await func(update, context)
        return wrapper
    
    @staticmethod  
    def require_text_message(func):
        """Декоратор для проверки типа сообщения"""
        async def wrapper(update, context):
            is_valid, error_msg = InputValidator.validate_message_type(update)
            if not is_valid and update.message:
                await update.message.reply_text(error_msg, parse_mode='HTML')
                return
                
            return await func(update, context)
        return wrapper 