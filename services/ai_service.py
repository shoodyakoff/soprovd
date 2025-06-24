"""
Абстрактный интерфейс для AI-сервисов
"""
from abc import ABC, abstractmethod
from typing import Optional


class AIService(ABC):
    """Абстрактный интерфейс для AI-сервисов"""
    
    @abstractmethod
    async def test_api_connection(self) -> bool:
        """Проверяет работу API"""
        pass
        
    @abstractmethod
    async def get_completion(
        self, 
        prompt: str, 
        temperature: float = 0.7, 
        max_tokens: int = 1500,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_type: str = "completion"
    ) -> Optional[str]:
        """Универсальный метод для получения ответа от AI"""
        pass
        
    @abstractmethod
    async def generate_personalized_letter(
        self, 
        prompt: str, 
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """Генерирует письмо по готовому персонализированному промпту"""
        pass
        
    @abstractmethod
    def set_stats_callback(self, callback):
        """Установить callback для сбора статистики"""
        pass 