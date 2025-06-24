import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

from utils.database import SupabaseClient
from models.analytics_models import (
    UserData, LetterSessionData, EventData, ErrorData, OpenAIRequestData
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.supabase = SupabaseClient.get_client()
        self.enabled = SupabaseClient.is_available()
        
    async def _execute_async(self, func, *args, **kwargs):
        """Выполнить операцию асинхронно, чтобы не блокировать бота"""
        if not self.enabled:
            return None
            
        try:
            # Запускаем в отдельном потоке, чтобы не блокировать
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, func, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Analytics operation failed: {e}")
            return None
    
    # === УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ===
    
    async def track_user(self, user_data: UserData) -> Optional[int]:
        """Добавить или обновить пользователя"""
        def _track_user():
            try:
                # Проверяем, существует ли пользователь
                existing = self.supabase.table('users').select('id').eq(
                    'telegram_user_id', user_data.telegram_user_id
                ).execute()
                
                if existing.data:
                    # Обновляем существующего пользователя
                    result = self.supabase.table('users').update(
                        user_data.to_dict()
                    ).eq('telegram_user_id', user_data.telegram_user_id).execute()
                    return existing.data[0]['id']
                else:
                    # Создаем нового пользователя
                    result = self.supabase.table('users').insert(
                        user_data.to_dict()
                    ).execute()
                    return result.data[0]['id'] if result.data else None
                    
            except Exception as e:
                logger.error(f"Failed to track user: {e}")
                return None
        
        return await self._execute_async(_track_user)
    
    async def get_user_id(self, telegram_user_id: int) -> Optional[int]:
        """Получить внутренний ID пользователя"""
        def _get_user_id():
            try:
                result = self.supabase.table('users').select('id').eq(
                    'telegram_user_id', telegram_user_id
                ).execute()
                return result.data[0]['id'] if result.data else None
            except Exception as e:
                logger.error(f"Failed to get user ID: {e}")
                return None
        
        return await self._execute_async(_get_user_id)
    
    # === УПРАВЛЕНИЕ СЕССИЯМИ ГЕНЕРАЦИИ ПИСЕМ ===
    
    async def create_letter_session(self, session_data: LetterSessionData) -> Optional[str]:
        """Создать новую сессию генерации письма"""
        def _create_session():
            try:
                logger.info(f"📊 Создаю letter_session с данными: {session_data.to_dict()}")
                result = self.supabase.table('letter_sessions').insert(
                    session_data.to_dict()
                ).execute()
                session_id = result.data[0]['id'] if result.data else None
                logger.info(f"✅ Letter session создана успешно: {session_id}")
                return session_id
            except Exception as e:
                logger.error(f"❌ Failed to create letter session: {e}")
                logger.error(f"❌ Session data was: {session_data.to_dict()}")
                return None
        
        return await self._execute_async(_create_session)
    
    async def update_letter_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Обновить сессию генерации письма"""
        def _update_session():
            try:
                logger.info(f"📊 Обновляю сессию {session_id} с данными: {updates}")
                result = self.supabase.table('letter_sessions').update(updates).eq(
                    'id', session_id
                ).execute()
                logger.info(f"✅ Сессия {session_id} обновлена успешно")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка обновления сессии {session_id}: {e}")
                logger.error(f"Данные для обновления: {updates}")
                return False
        
        result = await self._execute_async(_update_session)
        return result is True
    
    async def complete_letter_session(self, session_id: str, 
                                    generated_letter: Optional[str] = None,
                                    generation_time: Optional[int] = None) -> bool:
        """Завершить сессию генерации письма"""
        updates = {
            'status': 'completed',
            'session_end': datetime.now().isoformat()
        }
        
        if generated_letter:
            updates['generated_letter'] = generated_letter
        if generation_time:
            updates['generation_time_sec'] = generation_time
            
        return await self.update_letter_session(session_id, updates)
    
    async def abandon_letter_session(self, session_id: str) -> bool:
        """Отметить сессию как брошенную"""
        updates = {
            'status': 'abandoned',
            'session_end': datetime.now().isoformat()
        }
        return await self.update_letter_session(session_id, updates)
    
    # === СОБЫТИЯ ===
    
    async def track_event(self, event_data: EventData) -> bool:
        """Отследить событие пользователя"""
        def _track_event():
            try:
                logger.info(f"📊 Трекаю событие: {event_data.to_dict()}")
                self.supabase.table('user_events').insert(
                    event_data.to_dict()
                ).execute()
                logger.info(f"✅ Событие '{event_data.event_type}' записано успешно")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to track event: {e}")
                logger.error(f"❌ Event data was: {event_data.to_dict()}")
                return False
        
        result = await self._execute_async(_track_event)
        return result is True
    
    # === УДОБНЫЕ МЕТОДЫ ДЛЯ LETTERGENIUS ===
    
    async def track_start_command(self, user_id: int, session_id: Optional[str] = None) -> bool:
        """Отследить команду /start"""
        event = EventData(
            user_id=user_id,
            event_type='start',
            session_id=session_id
        )
        return await self.track_event(event)
    
    async def track_vacancy_sent(self, user_id: int, session_id: str, 
                               vacancy_length: int) -> bool:
        """Отследить отправку вакансии"""
        logger.info(f"📊 Трекаю vacancy_sent: user_id={user_id}, session_id={session_id}, length={vacancy_length}")
        event = EventData(
            user_id=user_id,
            event_type='vacancy_sent',
            session_id=session_id,
            event_data={'vacancy_length': vacancy_length}
        )
        return await self.track_event(event)
    
    async def track_resume_sent(self, user_id: int, session_id: str, 
                              resume_length: int) -> bool:
        """Отследить отправку резюме"""
        logger.info(f"📊 Трекаю resume_sent: user_id={user_id}, session_id={session_id}, length={resume_length}")
        event = EventData(
            user_id=user_id,
            event_type='resume_sent',
            session_id=session_id,
            event_data={'resume_length': resume_length}
        )
        return await self.track_event(event)
    
    async def track_letter_generated(self, user_id: int, session_id: str,
                                   letter_length: int, generation_time: int) -> bool:
        """Отследить успешную генерацию письма"""
        logger.info(f"📊 Трекаю letter_generated: user_id={user_id}, session_id={session_id}, length={letter_length}, time={generation_time}")
        event = EventData(
            user_id=user_id,
            event_type='letter_generated',
            session_id=session_id,
            event_data={
                'letter_length': letter_length,
                'generation_time_sec': generation_time
            }
        )
        return await self.track_event(event)
    
    async def track_restart(self, user_id: int) -> bool:
        """Отследить нажатие кнопки 'Начать заново'"""
        event = EventData(
            user_id=user_id,
            event_type='restart'
        )
        return await self.track_event(event)
    
    # === ОШИБКИ ===
    
    async def log_error(self, error_data: ErrorData) -> bool:
        """Логировать ошибку"""
        def _log_error():
            try:
                self.supabase.table('error_logs').insert(
                    error_data.to_dict()
                ).execute()
                return True
            except Exception as e:
                logger.error(f"Failed to log error: {e}")
                return False
        
        result = await self._execute_async(_log_error)
        return result is True
    
    # === OPENAI ЗАПРОСЫ ===
    
    async def log_openai_request(self, request_data: OpenAIRequestData) -> bool:
        """Логировать запрос к OpenAI"""
        def _log_request():
            try:
                self.supabase.table('openai_requests').insert(
                    request_data.to_dict()
                ).execute()
                return True
            except Exception as e:
                logger.error(f"Failed to log OpenAI request: {e}")
                return False
        
        result = await self._execute_async(_log_request)
        return result is True

# Глобальный экземпляр сервиса
analytics = AnalyticsService() 