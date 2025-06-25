"""
Модели для системы подписок и лимитов
Сопровод v7.0
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class SubscriptionData:
    """Данные о подписке пользователя"""
    user_id: int
    plan_type: str = "free"  # free, premium
    letters_limit: int = 3  # 3 письма в месяц для free плана
    letters_used: int = 0  # Использовано писем
    status: str = "active"  # active, cancelled, expired
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    auto_renew: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для Supabase"""
        return {
            'user_id': self.user_id,
            'plan_type': self.plan_type,
            'letters_limit': self.letters_limit,
            'letters_used': self.letters_used,
            'status': self.status,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'auto_renew': self.auto_renew,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def can_generate_letter(self) -> bool:
        """Проверяет, может ли пользователь генерировать письмо"""
        if self.plan_type == "premium":
            return True
        return self.letters_used < self.letters_limit
    
    def get_remaining_letters(self) -> int:
        """Возвращает количество оставшихся писем"""
        return max(0, self.letters_limit - self.letters_used)


@dataclass 
class PaymentData:
    """Данные о платеже"""
    user_id: int
    payment_id: str
    amount: float
    currency: str = "RUB"
    status: str = "pending"  # pending, completed, failed, refunded
    payment_method: str = "yookassa"
    description: Optional[str] = None
    confirmation_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для Supabase"""
        return {
            'user_id': self.user_id,
            'payment_id': self.payment_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'description': self.description,
            'confirmation_url': self.confirmation_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata
        }


@dataclass
class LetterIterationData:
    """Данные об итерации письма (редактирование по комментариям)"""
    session_id: str
    user_id: int
    iteration_number: int  # 1, 2, 3 (максимум 3 итерации)
    user_comment: str
    original_letter: str
    updated_letter: str
    tokens_used: Optional[int] = None
    generation_time_seconds: Optional[int] = None
    ai_provider: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для Supabase"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'iteration_number': self.iteration_number,
            'user_comment': self.user_comment,
            'original_letter': self.original_letter,
            'updated_letter': self.updated_letter,
            'tokens_used': self.tokens_used,
            'generation_time_seconds': self.generation_time_seconds,
            'ai_provider': self.ai_provider,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class SessionState:
    """Состояние сессии для итераций"""
    session_id: str
    user_id: int
    vacancy_text: str
    resume_text: str
    current_letter: str
    iterations_count: int = 0
    max_iterations: int = 3
    created_at: Optional[datetime] = None
    
    def can_iterate(self) -> bool:
        """Проверяет, можно ли еще итерировать"""
        return self.iterations_count < self.max_iterations
    
    def get_remaining_iterations(self) -> int:
        """Возвращает количество оставшихся итераций"""
        return max(0, self.max_iterations - self.iterations_count)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'vacancy_text': self.vacancy_text,
            'resume_text': self.resume_text,
            'current_letter': self.current_letter,
            'iterations_count': self.iterations_count,
            'max_iterations': self.max_iterations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 