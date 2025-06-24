from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime
import json

@dataclass
class UserData:
    telegram_user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass  
class LetterSessionData:
    """Сессия генерации сопроводительного письма"""
    user_id: int
    status: str = 'started'  # started, completed, abandoned
    mode: Optional[str] = None  # simple, advanced, etc.
    job_description: Optional[str] = None
    job_description_length: Optional[int] = None
    resume_text: Optional[str] = None
    resume_length: Optional[int] = None
    selected_style: Optional[str] = None  # professional, casual, bold
    detected_profession: Optional[str] = None
    detected_level: Optional[str] = None
    confidence_score: Optional[float] = None
    suggested_style: Optional[str] = None
    generated_letter: Optional[str] = None
    generated_letter_length: Optional[int] = None
    generation_time_seconds: Optional[int] = None
    openai_model_used: Optional[str] = None
    openai_tokens_used: Optional[int] = None
    user_regenerated: bool = False
    user_rating: Optional[int] = None
    regeneration_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Убираем None значения для необязательных полей
        return {k: v for k, v in data.items() if v is not None}

@dataclass
class EventData:
    user_id: int
    event_type: str  # 'start', 'vacancy_sent', 'resume_sent', 'letter_generated', 'restart'
    session_id: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data['event_data'] is None:
            del data['event_data']
        return data

@dataclass
class ErrorData:
    error_type: str
    error_message: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    stack_trace: Optional[str] = None
    handler_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}

@dataclass
class OpenAIRequestData:
    model: str
    request_type: str  # 'letter_generation', 'analysis', 'validation'
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time_ms: int
    success: bool = True
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None} 