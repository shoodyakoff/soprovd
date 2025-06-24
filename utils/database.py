import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Заглушка для Supabase клиента - временно отключен"""
    _instance: Optional[object] = None
    _failed_init = True  # Принудительно отключаем
    
    @classmethod
    def get_client(cls) -> Optional[object]:
        """Получить клиент Supabase (отключен)"""
        logger.info("⚠️ Supabase отключен - бот работает без аналитики")
        return None
    
    @classmethod
    def is_available(cls) -> bool:
        """Проверить доступность Supabase (всегда False)"""
        return False 