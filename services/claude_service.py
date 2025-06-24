"""
Сервис для работы с Anthropic Claude API
"""
import asyncio
import logging
import time
from typing import Optional
import anthropic
from .ai_service import AIService
from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    CLAUDE_FALLBACK_MODEL,
    CLAUDE_TIMEOUT,
    CLAUDE_MAX_TOKENS,
    CLAUDE_TEMPERATURE,
    MAX_GENERATION_ATTEMPTS,
    MIN_RESPONSE_LENGTH
)

# Настройка логирования
logger = logging.getLogger(__name__)


def _extract_text_from_response(response) -> Optional[str]:
    """Безопасно извлекает текст из Claude response"""
    if not response or not response.content:
        return None
    
    for content_block in response.content:
        # Проверяем, что это TextBlock, а не ToolUseBlock
        if hasattr(content_block, 'text'):
            text = getattr(content_block, 'text', None)
            if text:
                return text
    return None


class ClaudeService(AIService):
    """Сервис для работы с Anthropic Claude API"""
    
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self._stats_callback = None
    
    def set_stats_callback(self, callback):
        """Установить callback для сбора статистики"""
        self._stats_callback = callback
    
    async def test_api_connection(self) -> bool:
        """
        Проверяет работу Claude API
        
        Returns:
            True если API работает, False в противном случае
        """
        try:
            logger.info("Проверяем подключение к Claude API...")
            
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=10,
                    temperature=0.1,
                    messages=[
                        {
                            "role": "user",
                            "content": "Привет! Это тест. Ответь одним словом: работаю"
                        }
                    ]
                ),
                timeout=30
            )
            
            if response.content and len(response.content) > 0:
                # Правильная обработка Claude API response
                text_content = _extract_text_from_response(response)
                if text_content:
                    logger.info("✅ Claude API работает нормально")
                    return True
                logger.error("❌ Claude API вернул некорректный формат ответа")
                return False
            else:
                logger.error("❌ Claude API вернул пустой ответ")
                return False
                
        except asyncio.TimeoutError:
            logger.error("❌ Таймаут при проверке Claude API")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке Claude API: {e}")
            
            # Попробуем fallback модель
            try:
                logger.info("Пробуем fallback модель...")
                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=CLAUDE_FALLBACK_MODEL,
                        max_tokens=5,
                        temperature=0.1,
                        messages=[
                            {
                                "role": "user", 
                                "content": "Тест"
                            }
                        ]
                    ),
                    timeout=30
                )
                
                if response.content and len(response.content) > 0:
                    text_content = _extract_text_from_response(response)
                    if text_content:
                        logger.info(f"✅ Fallback модель {CLAUDE_FALLBACK_MODEL} работает")
                        return True
                else:
                    logger.error("❌ Fallback модель не отвечает")
                    return False
                    
            except Exception as fallback_e:
                logger.error(f"❌ Fallback модель тоже не работает: {fallback_e}")
                return False
        
        # Если дошли до сюда, значит все попытки неуспешны
        return False

    async def get_completion(
        self, 
        prompt: str, 
        temperature: float = 0.7, 
        max_tokens: int = 1500,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_type: str = "completion"
    ) -> Optional[str]:
        """
        Универсальный метод для получения ответа от Claude
        
        Args:
            prompt: Промпт для Claude
            temperature: Температура для генерации
            max_tokens: Максимальное количество токенов
            user_id: ID пользователя для аналитики
            session_id: ID сессии для аналитики
            request_type: Тип запроса для аналитики
            
        Returns:
            Ответ от Claude или None в случае ошибки
        """
        start_time = time.time()
        used_model = CLAUDE_MODEL
        
        try:
            logger.info(f"🤖 Отправляю запрос к Claude (temp={temperature}, max_tokens={max_tokens}, timeout={CLAUDE_TIMEOUT}s)")
            logger.info(f"📝 Длина промпта: {len(prompt)} символов")
            
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                ),
                timeout=CLAUDE_TIMEOUT
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            text_content = _extract_text_from_response(response)
            if text_content:
                content = text_content
                logger.info(f"✅ Получен ответ от Claude: {len(content)} символов")
                
                # 📊 АНАЛИТИКА: Логируем успешный запрос
                await self._log_claude_request(
                    model=used_model,
                    request_type=request_type,
                    input_tokens=response.usage.input_tokens if response.usage else 0,
                    output_tokens=response.usage.output_tokens if response.usage else 0,
                    response_time_ms=response_time_ms,
                    success=True,
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Сохраняем статистику для анализатора (если есть callback)
                if hasattr(self, '_stats_callback') and self._stats_callback:
                    total_tokens = (response.usage.input_tokens if response.usage else 0) + (response.usage.output_tokens if response.usage else 0)
                    self._stats_callback(
                        model=used_model,
                        tokens=total_tokens
                    )
                
                return content
            else:
                logger.error("❌ Claude вернул пустой ответ")
                # 📊 АНАЛИТИКА: Логируем пустой ответ
                await self._log_claude_request(
                    model=used_model,
                    request_type=request_type,
                    input_tokens=0,
                    output_tokens=0,
                    response_time_ms=response_time_ms,
                    success=False,
                    user_id=user_id,
                    session_id=session_id,
                    error_message="Empty response"
                )
                return None
                
        except asyncio.TimeoutError:
            logger.error("❌ Таймаут запроса к Claude")
            # 📊 АНАЛИТИКА: Логируем таймаут
            await self._log_claude_request(
                model=used_model,
                request_type=request_type,
                input_tokens=0,
                output_tokens=0,
                response_time_ms=response_time_ms,
                success=False,
                user_id=user_id,
                session_id=session_id,
                error_message="Timeout"
            )
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к Claude: {e}")
            
            # 📊 АНАЛИТИКА: Логируем ошибку в базу данных
            try:
                import traceback
                from models.analytics_models import ErrorData
                from services.analytics_service import analytics  # Используем глобальный экземпляр
                
                error_data = ErrorData(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    user_id=user_id,
                    session_id=session_id,
                    stack_trace=traceback.format_exc(),
                    handler_name='claude_get_completion'
                )
                await analytics.log_error(error_data)
            except Exception as log_error:
                logger.error(f"Failed to log Claude error to database: {log_error}")
            
            # Пробуем fallback модель
            try:
                logger.info(f"🔄 Пробую fallback модель {CLAUDE_FALLBACK_MODEL}...")
                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=CLAUDE_FALLBACK_MODEL,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    ),
                    timeout=CLAUDE_TIMEOUT
                )
                
                text_content = _extract_text_from_response(response)
                if text_content:
                    logger.info(f"✅ Fallback модель ответила: {len(text_content)} символов")
                    return text_content
                else:
                    logger.error("❌ Fallback модель вернула пустой ответ")
                    return None
                    
            except Exception as fallback_e:
                logger.error(f"❌ Fallback модель тоже не работает: {fallback_e}")
                return None

    async def generate_personalized_letter(self, prompt: str, temperature: Optional[float] = None) -> Optional[str]:
        """
        Генерирует письмо по готовому персонализированному промпту
        
        Args:
            prompt: Готовый промпт для генерации
            temperature: Температура для генерации (если нужно переопределить)
            
        Returns:
            Сгенерированное письмо или None в случае ошибки
        """
        # Используем переданную температуру или берем из конфигурации
        temp = temperature if temperature is not None else CLAUDE_TEMPERATURE
        
        # Пробуем сгенерировать письмо с несколькими попытками
        for attempt in range(MAX_GENERATION_ATTEMPTS):
            try:
                logger.info(f"Персонализированная генерация #{attempt + 1} (temp={temp})")
                
                response = await asyncio.wait_for(
                    self._make_claude_request(prompt, temp),
                    timeout=CLAUDE_TIMEOUT
                )
                
                if response and self._is_response_complete(response):
                    logger.info("Успешно сгенерировано персонализированное письмо")
                    return response
                else:
                    logger.warning(f"Неполный ответ на попытке #{attempt + 1}")
                    
            except asyncio.TimeoutError:
                logger.error(f"Таймаут на попытке #{attempt + 1}")
            except Exception as e:
                logger.error(f"Ошибка на попытке #{attempt + 1}: {e}")
            
        logger.error("Все попытки персонализированной генерации неуспешны")
        return None

    async def _make_claude_request(self, prompt: str, temperature: float) -> Optional[str]:
        """
        Выполняет персонализированный запрос к Claude API
        
        Args:
            prompt: Промпт для генерации
            temperature: Температура генерации
            
        Returns:
            Ответ от Claude или None в случае ошибки
        """
        try:
            # Сначала пробуем основную модель
            response = await self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            text_content = _extract_text_from_response(response)
            if text_content:
                return text_content
            else:
                return None
            
        except Exception as e:
            logger.warning(f"Ошибка с моделью {CLAUDE_MODEL}: {e}")
            
            # Пробуем fallback модель
            try:
                response = await self.client.messages.create(
                    model=CLAUDE_FALLBACK_MODEL,
                    max_tokens=CLAUDE_MAX_TOKENS,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                text_content = _extract_text_from_response(response)
                if text_content:
                    return text_content
                else:
                    return None
                
            except Exception as fallback_e:
                logger.error(f"Ошибка с fallback моделью {CLAUDE_FALLBACK_MODEL}: {fallback_e}")
                return None

    def _is_response_complete(self, response: str) -> bool:
        """
        Проверяет, является ли ответ полным
        
        Args:
            response: Ответ от Claude
            
        Returns:
            True если ответ кажется полным
        """
        if not response or len(response.strip()) < MIN_RESPONSE_LENGTH:
            logger.warning(f"Ответ слишком короткий: {len(response.strip()) if response else 0} < {MIN_RESPONSE_LENGTH}")
            return False
        
        response = response.strip()
        
        # Проверяем разные варианты корректного окончания письма
        valid_endings = [
            # Обычные знаки препинания
            '.', '!', '?',
            # Подписи в письмах
            '[Ваше имя]', '[Ваше Имя]', '[Имя]', '[ваше имя]',
            # Другие варианты подписи
            'уважением', 'благодарностью', 'надеждой'
        ]
        
        # Проверяем, заканчивается ли ответ одним из допустимых вариантов
        for ending in valid_endings:
            if response.endswith(ending):
                return True
                
        # Дополнительная проверка - если письмо содержит "С уважением" в конце
        if 'уважением' in response[-100:] or 'благодарностью' in response[-100:]:
            return True
            
        logger.warning(f"Ответ не заканчивается корректно: '{response[-50:]}'")
        return False

    async def _log_claude_request(
        self,
        model: str,
        request_type: str,
        input_tokens: int,
        output_tokens: int,
        response_time_ms: int,
        success: bool,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Логирует запрос к Claude в базу данных
        """
        try:
            # Импортируем здесь чтобы избежать циклических импортов
            from services.analytics_service import analytics  # Используем глобальный экземпляр
            from models.analytics_models import OpenAIRequestData  # Используем ту же модель
            
            # Адаптируем под формат Claude
            request_data = OpenAIRequestData(
                model=model,
                request_type=request_type,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                response_time_ms=response_time_ms,
                success=success,
                user_id=user_id,
                session_id=session_id,
                error_message=error_message
            )
            
            await analytics.log_openai_request(request_data)  # Используем тот же метод
        except Exception as e:
            # Логируем ошибку, но не прерываем основной процесс
            logger.error(f"Ошибка при логировании Claude запроса: {e}")


# Глобальный экземпляр сервиса для быстрого доступа  
claude_service = ClaudeService()


async def generate_letter_with_claude(prompt: str, temperature: Optional[float] = None) -> Optional[str]:
    """
    Удобная функция для генерации письма с готовым промптом через Claude
    """
    return await claude_service.generate_personalized_letter(prompt, temperature) 