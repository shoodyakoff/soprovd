"""
Модели данных для системы оценок и обратной связи v7.2
УПРОЩЕННАЯ ВЕРСИЯ: только лайки/дизлайки БЕЗ комментариев
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class LetterFeedbackData:
    """Данные об оценке письма пользователем - ТОЛЬКО лайки/дизлайки"""
    session_id: str
    user_id: int
    iteration_number: int
    feedback_type: str  # ТОЛЬКО 'like' или 'dislike'
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для Supabase"""
        data = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'iteration_number': self.iteration_number,
            'feedback_type': self.feedback_type
        }
        
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
            
        return data

@dataclass
class LetterIterationImprovement:
    """Данные для улучшения письма на основе обратной связи"""
    session_id: str
    user_id: int
    iteration_number: int
    user_feedback: str  # Комментарий пользователя о том, что нужно изменить
    improvement_request: str  # Запрос на улучшение
    previous_letter: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для letter_iterations"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'iteration_number': self.iteration_number,
            'user_feedback': self.user_feedback,
            'improvement_request': self.improvement_request,
            'iteration_type': 'improvement'
        }

@dataclass
class SessionIterationStatus:
    """Статус итераций для сессии"""
    session_id: str
    current_iteration: int
    max_iterations: int
    has_feedback: bool
    can_iterate: bool
    remaining_iterations: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'current_iteration': self.current_iteration,
            'max_iterations': self.max_iterations,
            'has_feedback': self.has_feedback,
            'can_iterate': self.can_iterate,
            'remaining_iterations': self.remaining_iterations
        } 