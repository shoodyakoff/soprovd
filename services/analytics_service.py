import asyncio
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime
import traceback

from utils.database import SupabaseClient
from models.analytics_models import (
    UserData, LetterSessionData, EventData, ErrorData, OpenAIRequestData
)
from models.subscription_models import (
    SubscriptionData, PaymentData, LetterIterationData
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.supabase = SupabaseClient.get_client()
        self.enabled = SupabaseClient.is_available()
        
    def _has_supabase(self) -> bool:
        """Проверяет наличие Supabase клиента"""
        return self.supabase is not None and hasattr(self.supabase, 'table')
        
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
                if not self.supabase:
                    logger.warning("Supabase client not available")
                    return None
                    
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
                if not self.supabase:
                    return None
                    
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
                if not self.supabase:
                    logger.warning("Supabase client not available")
                    return None
                    
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
                if not self.supabase:
                    logger.warning("Supabase client not available")
                    return False
                    
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
    
    async def get_letter_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получить данные сессии по ID"""
        def _get_session():
            try:
                if not self.supabase:
                    return None
                    
                response = self.supabase.table('letter_sessions').select('*').eq(
                    'id', session_id
                ).execute()
                
                if response.data and len(response.data) > 0:
                    return response.data[0]
                return None
                
            except Exception as e:
                logger.error(f"❌ Ошибка получения сессии {session_id}: {e}")
                return None
        
        result = await self._execute_async(_get_session)
        return result if result is not None else None
    
    async def complete_letter_session(self, session_id: str, 
                                    generated_letter: Optional[str] = None,
                                    generation_time: Optional[int] = None) -> bool:
        """Завершить сессию генерации письма"""
        updates: Dict[str, Union[str, int]] = {
            'status': 'completed',
            'session_end': datetime.now().isoformat()
        }
        
        if generated_letter:
            updates['generated_letter'] = generated_letter
        if generation_time:
            updates['generation_time_seconds'] = generation_time
            
        return await self.update_letter_session(session_id, updates)
    
    async def abandon_letter_session(self, session_id: str) -> bool:
        """Отметить сессию как брошенную"""
        updates: Dict[str, str] = {
            'status': 'abandoned',
            'session_end': datetime.now().isoformat()
        }
        return await self.update_letter_session(session_id, updates)
    
    # === СОБЫТИЯ ===
    
    async def track_event(self, event_data: EventData) -> bool:
        """Отследить событие пользователя"""
        def _track_event():
            try:
                if not self.supabase:
                    logger.warning("Supabase client not available")
                    return False
                    
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
                'generation_time_seconds': generation_time
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
                if not self.supabase:
                    return False
                    
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
                if not self.supabase:
                    logger.warning("Supabase client not available")
                    return False
                    
                self.supabase.table('openai_requests').insert(
                    request_data.to_dict()
                ).execute()
                return True
            except Exception as e:
                logger.error(f"Failed to log OpenAI request: {e}")
                return False
        
        result = await self._execute_async(_log_request)
        return result is True
    
    # ===================================================
    # НОВЫЕ МЕТОДЫ ДЛЯ V7.0 - ПОДПИСКИ И ИТЕРАЦИИ
    # ===================================================
    
    async def get_or_create_subscription(self, user_id: int) -> Optional[dict]:
        """Получить или создать подписку пользователя (исправлена для v9.10)"""
        def _get_or_create():
            try:
                if not self.supabase:
                    logger.error(f"❌ No Supabase client for user {user_id}")
                    return None
                    
                # Пытаемся найти существующую подписку
                response = self.supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()
                
                if response.data:
                    logger.info(f"✅ Found existing subscription for user {user_id}")
                    return response.data[0]
                
                # Создаем новую подписку
                logger.info(f"🔄 Creating new subscription for user {user_id}")
                subscription_data = SubscriptionData(user_id=user_id)
                response = self.supabase.table('subscriptions').insert(subscription_data.to_dict()).execute()
                
                if response.data:
                    logger.info(f"✅ Successfully created subscription for user {user_id}")
                    return response.data[0]
                else:
                    logger.error(f"❌ Failed to create subscription - no data returned for user {user_id}")
                    
                return None
                
            except Exception as e:
                logger.error(f"❌ Exception in get_or_create_subscription for user {user_id}: {e}")
                return None
        
        result = await self._execute_async(_get_or_create)
        if not result:
            logger.error(f"❌ CRITICAL: get_or_create_subscription failed for user {user_id}")
        return result
    
    async def update_subscription(self, user_id: int, updates: dict) -> bool:
        """Обновить подписку пользователя"""
        def _update():
            try:
                if not self.supabase:
                    return False
                    
                self.supabase.table('subscriptions').update(updates).eq('user_id', user_id).execute()
                return True
                
            except Exception as e:
                logger.error(f"Failed to update subscription: {e}")
                return False
        
        result = await self._execute_async(_update)
        return result is True
    
    async def increment_letters_used(self, user_id: int) -> bool:
        """Увеличить счетчик использованных писем"""
        def _increment():
            try:
                if not self.supabase:
                    return False
                    
                # Получаем текущее значение
                response = self.supabase.table('subscriptions').select('letters_used').eq('user_id', user_id).execute()
                
                if response.data:
                    current_used = response.data[0]['letters_used']
                    new_used = current_used + 1
                    
                    self.supabase.table('subscriptions').update({'letters_used': new_used}).eq('user_id', user_id).execute()
                    return True
                    
                return False
                
            except Exception as e:
                logger.error(f"Failed to increment letters used: {e}")
                return False
        
        result = await self._execute_async(_increment)
        return result is True
    
    async def log_payment(self, payment_data: PaymentData) -> bool:
        """Логировать платеж"""
        def _log_payment():
            try:
                if not self.supabase:
                    return False
                    
                self.supabase.table('payments').insert(payment_data.to_dict()).execute()
                return True
                
            except Exception as e:
                logger.error(f"Failed to log payment: {e}")
                return False
        
        result = await self._execute_async(_log_payment)
        return result is True
    
    async def update_payment_status(self, payment_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Обновить статус платежа"""
        def _update_payment():
            try:
                if not self.supabase:
                    return False
                    
                updates: Dict[str, Any] = {'status': status}
                if metadata:
                    updates['metadata'] = metadata
                    
                self.supabase.table('payments').update(updates).eq('payment_id', payment_id).execute()
                return True
                
            except Exception as e:
                logger.error(f"Failed to update payment status: {e}")
                return False
        
        result = await self._execute_async(_update_payment)
        return result is True
    
    async def log_letter_iteration(self, iteration_data: LetterIterationData) -> bool:
        """Логировать итерацию письма"""
        def _log_iteration():
            try:
                if not self.supabase:
                    return False
                    
                self.supabase.table('letter_iterations').insert(iteration_data.to_dict()).execute()
                return True
                
            except Exception as e:
                logger.error(f"Failed to log letter iteration: {e}")
                return False
        
        result = await self._execute_async(_log_iteration)
        return result is True
    
    async def get_session_iterations_count(self, session_id: str) -> int:
        """Получить количество итераций для сессии"""
        def _get_count():
            try:
                if not self.supabase:
                    return 0
                    
                response = self.supabase.table('letter_iterations').select('id').eq('session_id', session_id).execute()
                return len(response.data) if response.data else 0
                
            except Exception as e:
                logger.error(f"Failed to get iterations count: {e}")
                return 0
        
        result = await self._execute_async(_get_count)
        return result if result is not None else 0

    # ===================================================
    # MONETIZATION TRACKING v9.3
    # ===================================================
    
    async def track_premium_offer_shown(self, user_id: int, touchpoint_location: str, 
                                      user_generation_count: int = 0, session_duration: int = 0) -> bool:
        """Отследить показ premium предложения"""
        logger.info(f"💰 Трекаю premium_offer_shown: user_id={user_id}, location={touchpoint_location}")
        event = EventData(
            user_id=user_id,
            event_type='premium_offer_shown',
            event_data={
                'touchpoint_location': touchpoint_location,
                'user_generation_count': user_generation_count,
                'session_duration': session_duration
            }
        )
        return await self.track_event(event)
    
    async def track_premium_button_clicked(self, user_id: int, button_type: str, 
                                         touchpoint_location: str) -> bool:
        """Отследить клик на premium кнопку"""
        logger.info(f"💰 Трекаю premium_button_clicked: user_id={user_id}, button={button_type}, location={touchpoint_location}")
        event = EventData(
            user_id=user_id,
            event_type='premium_button_clicked',
            event_data={
                'button_type': button_type,
                'touchpoint_location': touchpoint_location
            }
        )
        return await self.track_event(event)
    
    async def track_contact_initiated(self, user_id: int, contact_method: str = 'telegram') -> bool:
        """Отследить инициирование контакта с поддержкой"""
        logger.info(f"💰 Трекаю contact_initiated: user_id={user_id}, method={contact_method}")
        event = EventData(
            user_id=user_id,
            event_type='contact_initiated',
            event_data={
                'contact_method': contact_method
            }
        )
        return await self.track_event(event)
    
    async def track_premium_info_viewed(self, user_id: int, source: str = 'command') -> bool:
        """Отследить просмотр информации о premium"""
        logger.info(f"💰 Трекаю premium_info_viewed: user_id={user_id}, source={source}")
        event = EventData(
            user_id=user_id,
            event_type='premium_info_viewed',
            event_data={
                'source': source
            }
        )
        return await self.track_event(event)

# Глобальный экземпляр сервиса
analytics = AnalyticsService() 