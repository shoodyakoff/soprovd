"""
Сервис для работы с OpenAI API
"""
import asyncio
import logging
import time
from typing import Optional
from openai import AsyncOpenAI
from .ai_service import AIService
from config import (
    OPENAI_API_KEY, 
    OPENAI_MODEL, 
    OPENAI_FALLBACK_MODEL,
    OPENAI_TIMEOUT,
    MAX_GENERATION_ATTEMPTS,
    MIN_RESPONSE_LENGTH,
    OPENAI_TEMPERATURE,
    OPENAI_TOP_P,
    OPENAI_PRESENCE_PENALTY,
    OPENAI_FREQUENCY_PENALTY
)
# Старый импорт удален - используется smart_analyzer_v6.py с встроенными промптами

# Настройка логирования
logger = logging.getLogger(__name__)

class OpenAIService(AIService):
    """Сервис для работы с OpenAI API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self._stats_callback = None
    
    def set_stats_callback(self, callback):
        """Установить callback для сбора статистики"""
        self._stats_callback = callback
    
    async def test_api_connection(self) -> bool:
        """
        Проверяет работу OpenAI API
        
        Returns:
            True если API работает, False в противном случае
        """
        try:
            logger.info("Проверяем подключение к OpenAI API...")
            
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": "Привет! Это тест. Ответь одним словом: работаю"
                        }
                    ],
                    max_tokens=10,
                    temperature=0.1
                ),
                timeout=30
            )
            
            if response.choices and response.choices[0].message.content:
                logger.info("✅ OpenAI API работает нормально")
                return True
            else:
                logger.error("❌ OpenAI API вернул пустой ответ")
                return False
                
        except asyncio.TimeoutError:
            logger.error("❌ Таймаут при проверке OpenAI API")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке OpenAI API: {e}")
            
            # Попробуем fallback модель
            try:
                logger.info("Пробуем fallback модель...")
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=OPENAI_FALLBACK_MODEL,
                        messages=[
                            {
                                "role": "user",
                                "content": "Тест"
                            }
                        ],
                        max_tokens=5,
                        temperature=0.1
                    ),
                    timeout=30
                )
                
                if response.choices and response.choices[0].message.content:
                    logger.info(f"✅ Fallback модель {OPENAI_FALLBACK_MODEL} работает")
                    return True
                else:
                    logger.error("❌ Fallback модель не отвечает")
                    return False
                    
            except Exception as fallback_e:
                logger.error(f"❌ Fallback модель тоже не работает: {fallback_e}")
                return False

    async def _make_openai_request(self, prompt: str) -> Optional[str]:
        """
        Выполняет запрос к OpenAI API
        
        Args:
            prompt: Промпт для генерации
            
        Returns:
            Ответ от OpenAI или None в случае ошибки
        """
        try:
            # Сначала пробуем основную модель
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=OPENAI_TEMPERATURE,
                top_p=OPENAI_TOP_P,
                presence_penalty=OPENAI_PRESENCE_PENALTY,
                frequency_penalty=OPENAI_FREQUENCY_PENALTY
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"Ошибка с моделью {OPENAI_MODEL}: {e}")
            
            # Пробуем fallback модель
            try:
                response = await self.client.chat.completions.create(
                    model=OPENAI_FALLBACK_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=1500,
                    temperature=OPENAI_TEMPERATURE,
                    top_p=OPENAI_TOP_P,
                    presence_penalty=OPENAI_PRESENCE_PENALTY,
                    frequency_penalty=OPENAI_FREQUENCY_PENALTY
                )
                
                return response.choices[0].message.content
                
            except Exception as fallback_e:
                logger.error(f"Ошибка с fallback моделью {OPENAI_FALLBACK_MODEL}: {fallback_e}")
                return None
    
    def _is_response_complete(self, response: str) -> bool:
        """
        Проверяет, является ли ответ полным
        
        Args:
            response: Ответ от OpenAI
            
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
        Универсальный метод для получения ответа от GPT
        
        Args:
            prompt: Промпт для GPT
            temperature: Температура для генерации
            max_tokens: Максимальное количество токенов
            user_id: ID пользователя для аналитики
            session_id: ID сессии для аналитики
            request_type: Тип запроса для аналитики
            
        Returns:
            Ответ от GPT или None в случае ошибки
        """
        start_time = time.time()
        used_model = OPENAI_MODEL
        
        try:
            logger.info(f"🤖 Отправляю запрос к GPT (temp={temperature}, max_tokens={max_tokens}, timeout={OPENAI_TIMEOUT}s)")
            logger.info(f"📝 Длина промпта: {len(prompt)} символов")
            
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                ),
                timeout=OPENAI_TIMEOUT
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content
                logger.info(f"✅ Получен ответ от GPT: {len(content)} символов")
                
                # 📊 АНАЛИТИКА: Логируем успешный запрос
                await self._log_openai_request(
                    model=used_model,
                    request_type=request_type,
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                    response_time_ms=response_time_ms,
                    success=True,
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Сохраняем статистику для анализатора (если есть callback)
                if hasattr(self, '_stats_callback') and self._stats_callback:
                    self._stats_callback(
                        model=used_model,
                        tokens=response.usage.total_tokens if response.usage else 0
                    )
                
                return content
            else:
                logger.error("❌ GPT вернул пустой ответ")
                # 📊 АНАЛИТИКА: Логируем пустой ответ
                await self._log_openai_request(
                    model=used_model,
                    request_type=request_type,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    response_time_ms=response_time_ms,
                    success=False,
                    user_id=user_id,
                    session_id=session_id,
                    error_message="Empty response"
                )
                return None
                
        except asyncio.TimeoutError:
            logger.error("❌ Таймаут запроса к GPT")
            # 📊 АНАЛИТИКА: Логируем таймаут
            await self._log_openai_request(
                model=used_model,
                request_type=request_type,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                response_time_ms=response_time_ms,
                success=False,
                user_id=user_id,
                session_id=session_id,
                error_message="Timeout"
            )
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к GPT: {e}")
            
            # 📊 АНАЛИТИКА: Логируем ошибку в базу данных
            try:
                import traceback
                from models.analytics_models import ErrorData
                from services.analytics_service import AnalyticsService
                
                error_data = ErrorData(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    user_id=user_id,
                    session_id=session_id,
                    stack_trace=traceback.format_exc(),
                    handler_name='openai_get_completion'
                )
                analytics = AnalyticsService()
                await analytics.log_error(error_data)
            except Exception as log_error:
                logger.error(f"Failed to log OpenAI error to database: {log_error}")
            
            # Пробуем fallback модель
            try:
                logger.info(f"🔄 Пробую fallback модель {OPENAI_FALLBACK_MODEL}...")
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=OPENAI_FALLBACK_MODEL,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature
                    ),
                    timeout=OPENAI_TIMEOUT
                )
                
                if response.choices and response.choices[0].message.content:
                    content = response.choices[0].message.content
                    logger.info(f"✅ Fallback модель ответила: {len(content)} символов")
                    return content
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
        temp = temperature if temperature is not None else OPENAI_TEMPERATURE
        
        # Пробуем сгенерировать письмо с несколькими попытками
        for attempt in range(MAX_GENERATION_ATTEMPTS):
            try:
                logger.info(f"Персонализированная генерация #{attempt + 1} (temp={temp})")
                
                response = await asyncio.wait_for(
                    self._make_personalized_request(prompt, temp),
                    timeout=OPENAI_TIMEOUT
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

    async def _make_personalized_request(self, prompt: str, temperature: float) -> Optional[str]:
        """
        Выполняет персонализированный запрос к OpenAI API
        
        Args:
            prompt: Промпт для генерации
            temperature: Температура генерации
            
        Returns:
            Ответ от OpenAI или None в случае ошибки
        """
        try:
            # Сначала пробуем основную модель
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=temperature,
                top_p=OPENAI_TOP_P,
                presence_penalty=OPENAI_PRESENCE_PENALTY,
                frequency_penalty=OPENAI_FREQUENCY_PENALTY
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"Ошибка с моделью {OPENAI_MODEL}: {e}")
            
            # Пробуем fallback модель
            try:
                response = await self.client.chat.completions.create(
                    model=OPENAI_FALLBACK_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=1500,
                    temperature=temperature,
                    top_p=OPENAI_TOP_P,
                    presence_penalty=OPENAI_PRESENCE_PENALTY,
                    frequency_penalty=OPENAI_FREQUENCY_PENALTY
                )
                
                return response.choices[0].message.content
                
            except Exception as fallback_e:
                logger.error(f"Ошибка с fallback моделью {OPENAI_FALLBACK_MODEL}: {fallback_e}")
                return None

    async def _log_openai_request(
        self,
        model: str,
        request_type: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        response_time_ms: int,
        success: bool,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Логирует запрос к OpenAI в базу данных
        """
        try:
            # Импортируем здесь чтобы избежать циклических импортов
            from services.analytics_service import AnalyticsService
            from models.analytics_models import OpenAIRequestData
            
            request_data = OpenAIRequestData(
                model=model,
                request_type=request_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_time_ms=response_time_ms,
                success=success,
                user_id=user_id,
                session_id=session_id,
                error_message=error_message
            )
            
            analytics = AnalyticsService()
            await analytics.log_openai_request(request_data)
        except Exception as e:
            # Логируем ошибку, но не прерываем основной процесс
            logger.error(f"Ошибка при логировании OpenAI запроса: {e}")


# Глобальный экземпляр сервиса для быстрого доступа  
openai_service = OpenAIService()


async def generate_letter_with_retry(prompt: str, temperature: Optional[float] = None) -> Optional[str]:
    """
    Удобная функция для генерации письма с готовым промптом
    """
    return await openai_service.generate_personalized_letter(prompt, temperature) 