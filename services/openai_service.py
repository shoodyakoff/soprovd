"""
Сервис для работы с OpenAI API
"""
import asyncio
import logging
from typing import Optional
from openai import AsyncOpenAI
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
from utils.prompts import get_cover_letter_prompt

# Настройка логирования
logger = logging.getLogger(__name__)

class OpenAIService:
    """Сервис для работы с OpenAI API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
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

    async def generate_cover_letter(
        self, 
        job_description: str, 
        resume: str, 
        style: str
    ) -> Optional[str]:
        """
        Генерирует сопроводительное письмо с использованием OpenAI API
        
        Args:
            job_description: Описание вакансии
            resume: Резюме кандидата
            style: Стиль письма (neutral, bold, formal)
            
        Returns:
            Сгенерированное письмо или None в случае ошибки
        """
        
        prompt = get_cover_letter_prompt(job_description, resume, style)
        
        # Пробуем сгенерировать письмо с несколькими попытками
        for attempt in range(MAX_GENERATION_ATTEMPTS):
            try:
                logger.info(f"Попытка генерации #{attempt + 1} (temp={OPENAI_TEMPERATURE}, top_p={OPENAI_TOP_P}, presence={OPENAI_PRESENCE_PENALTY}, frequency={OPENAI_FREQUENCY_PENALTY})")
                
                response = await asyncio.wait_for(
                    self._make_openai_request(prompt),
                    timeout=OPENAI_TIMEOUT
                )
                
                if response and self._is_response_complete(response):
                    logger.info("Успешно сгенерировано письмо")
                    return response
                else:
                    # Логируем детали для отладки
                    response_length = len(response) if response else 0
                    response_preview = response[:200] if response else "None"
                    logger.warning(f"Неполный ответ на попытке #{attempt + 1}. Длина: {response_length}, Превью: {response_preview}")
                    if response:
                        ends_properly = response.strip().endswith(('.', '!', '?'))
                        logger.warning(f"Заканчивается правильно: {ends_properly}, Последние 50 символов: '{response[-50:]}'")
                    
            except asyncio.TimeoutError:
                logger.error(f"Таймаут на попытке #{attempt + 1}")
            except Exception as e:
                logger.error(f"Ошибка на попытке #{attempt + 1}: {e}")
        
        logger.error("Все попытки генерации неуспешны")
        return None
    
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