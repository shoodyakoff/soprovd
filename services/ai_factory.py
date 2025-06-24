"""
Фабрика для создания AI-сервисов
"""
import os
from typing import Optional
from .ai_service import AIService
from .openai_service import OpenAIService
from .claude_service import ClaudeService


class AIFactory:
    """Фабрика для создания AI-сервисов"""
    
    _instance: Optional[AIService] = None
    
    @classmethod
    def get_service(cls) -> AIService:
        """
        Получить экземпляр AI-сервиса в зависимости от конфигурации
        
        Returns:
            Экземпляр AI-сервиса (OpenAI или Claude)
        """
        if cls._instance is None:
            # Читаем провайдера динамически из переменных окружения
            ai_provider = os.getenv('AI_PROVIDER', 'openai')
            if ai_provider.lower() == 'claude':
                cls._instance = ClaudeService()
            else:
                cls._instance = OpenAIService()
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Сбросить singleton для тестирования"""
        cls._instance = None
    
    @classmethod
    def get_provider_name(cls) -> str:
        """Получить название текущего провайдера"""
        ai_provider = os.getenv('AI_PROVIDER', 'openai')
        return ai_provider.upper()


# Глобальная функция для получения сервиса
def get_ai_service() -> AIService:
    """Получить AI-сервис для работы"""
    return AIFactory.get_service() 