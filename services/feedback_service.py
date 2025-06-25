"""
Сервис управления обратной связью и итерациями писем v7.2
УПРОЩЕННАЯ ВЕРСИЯ: только лайки/дизлайки БЕЗ комментариев
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from utils.database import SupabaseClient
from models.feedback_models import (
    LetterFeedbackData, LetterIterationImprovement, SessionIterationStatus
)

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self):
        self.supabase = SupabaseClient.get_client()
        self.enabled = SupabaseClient.is_available()
        
    async def _execute_async(self, func, *args, **kwargs):
        """Выполнить операцию асинхронно"""
        if not self.enabled:
            return None
            
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, func, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Feedback operation failed: {e}")
            return None
    
    # === УПРАВЛЕНИЕ СТАТУСОМ ИТЕРАЦИЙ ===
    
    async def get_session_iteration_status(self, session_id: str) -> Optional[SessionIterationStatus]:
        """Получить статус итераций для сессии"""
        def _get_status():
            try:
                if not self.supabase:
                    return None
                
                # Получаем данные сессии
                response = self.supabase.table('letter_sessions').select(
                    'current_iteration, max_iterations, has_feedback'
                ).eq('id', session_id).execute()
                
                if not response.data:
                    return None
                
                session = response.data[0]
                current = session['current_iteration'] or 1
                max_iter = session['max_iterations'] or 3
                has_feedback = session['has_feedback'] or False
                
                remaining = max(0, max_iter - current)
                can_iterate = remaining > 0
                
                return SessionIterationStatus(
                    session_id=session_id,
                    current_iteration=current,
                    max_iterations=max_iter,
                    has_feedback=has_feedback,
                    can_iterate=can_iterate,
                    remaining_iterations=remaining
                )
                
            except Exception as e:
                logger.error(f"Error getting session status: {e}")
                return None
        
        return await self._execute_async(_get_status)
    
    async def increment_session_iteration(self, session_id: str) -> bool:
        """Увеличить номер итерации сессии"""
        def _increment():
            try:
                if not self.supabase:
                    return False
                
                # Получаем текущую итерацию
                response = self.supabase.table('letter_sessions').select(
                    'current_iteration'
                ).eq('id', session_id).execute()
                
                if not response.data:
                    return False
                
                current = response.data[0]['current_iteration'] or 1
                new_iteration = current + 1
                
                # Обновляем
                self.supabase.table('letter_sessions').update({
                    'current_iteration': new_iteration
                }).eq('id', session_id).execute()
                
                logger.info(f"Session {session_id} iteration incremented: {current} -> {new_iteration}")
                return True
                
            except Exception as e:
                logger.error(f"Error incrementing iteration: {e}")
                return False
        
        result = await self._execute_async(_increment)
        return result is True
    
    # === СОХРАНЕНИЕ ОБРАТНОЙ СВЯЗИ ===
    
    async def save_feedback(self, feedback_data: LetterFeedbackData) -> bool:
        """Сохранить оценку пользователя (только лайк/дизлайк)"""
        def _save_feedback():
            try:
                if not self.supabase:
                    logger.warning("Supabase not available for feedback saving")
                    return False
                
                logger.info(f"💬 Сохраняю обратную связь: {feedback_data.feedback_type} для сессии {feedback_data.session_id}")
                
                # Проверяем, что сессия существует
                session_check = self.supabase.table('letter_sessions').select('id').eq(
                    'id', feedback_data.session_id
                ).execute()
                
                if not session_check.data:
                    logger.error(f"❌ Session {feedback_data.session_id} not found")
                    return False
                
                # Сохраняем обратную связь
                self.supabase.table('letter_feedback').insert(
                    feedback_data.to_dict()
                ).execute()
                
                logger.info(f"✅ Обратная связь сохранена успешно")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error saving feedback: {e}")
                logger.error(f"❌ Feedback data: {feedback_data.to_dict()}")
                return False
        
        result = await self._execute_async(_save_feedback)
        return result is True
    
    async def get_session_feedback(self, session_id: str) -> List[Dict[str, Any]]:
        """Получить всю обратную связь по сессии"""
        def _get_feedback():
            try:
                if not self.supabase:
                    return []
                
                response = self.supabase.table('letter_feedback').select('*').eq(
                    'session_id', session_id
                ).order('iteration_number').execute()
                
                return response.data or []
                
            except Exception as e:
                logger.error(f"Error getting session feedback: {e}")
                return []
        
        result = await self._execute_async(_get_feedback)
        return result or []
    
    # === ГЕНЕРАЦИЯ УЛУЧШЕННЫХ ПИСЕМ ===
    
    async def save_letter_iteration(self, iteration_data: LetterIterationImprovement, 
                                  generated_letter: str, generation_time: int) -> bool:
        """Сохранить итерацию улучшенного письма"""
        def _save_iteration():
            try:
                if not self.supabase:
                    return False
                
                data = iteration_data.to_dict()
                data.update({
                    'generated_letter': generated_letter,
                    'generation_time_seconds': generation_time,
                    'ai_model_used': 'claude',  # или получать из AIFactory
                    'created_at': datetime.now().isoformat()
                })
                
                self.supabase.table('letter_iterations').insert(data).execute()
                logger.info(f"Letter iteration saved for session {iteration_data.session_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error saving letter iteration: {e}")
                return False
        
        result = await self._execute_async(_save_iteration)
        return result is True
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def format_iteration_counter(self, status: SessionIterationStatus) -> str:
        """Форматировать счетчик итераций для показа пользователю"""
        remaining = status.remaining_iterations
        
        if remaining <= 0:
            return "🏁 <b>Это финальное письмо</b>\nИсчерпаны все возможности улучшения\n\n💡 Создайте новое письмо: /start"
        
        return f"🔄 <b>Осталось правок: {remaining}</b>"
    
    def get_improvement_prompt_text(self, remaining_iterations: int) -> str:
        """Получить текст с инструкциями для улучшения письма"""
        return (
            f"🔄 <b>Улучшаем письмо</b> ({remaining_iterations} правок осталось)\n\n"
            "💬 <b>Опишите, что нужно изменить:</b>\n\n"
            "🎯 <b>Например:</b>\n"
            "• Какой тон письма предпочитаете? (деловой/дружелюбный/уверенный)\n"
            "• Какие навыки стоит подчеркнуть сильнее?\n"
            "• Что добавить или убрать из письма?\n"
            "• Нужно ли изменить структуру или акценты?\n"
            "• Больше конкретных примеров из опыта?\n\n"
            "📝 <i>Напишите ваши пожелания подробно...</i>"
        )

# Глобальный экземпляр
feedback_service = FeedbackService() 