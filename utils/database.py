import os
from supabase import create_client, Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Optional[Client]:
        """Получить клиент Supabase (синглтон)"""
        if cls._instance is None:
            try:
                # Импортируем переменные из config.py, где они правильно загружаются
                from config import SUPABASE_URL, SUPABASE_KEY
                
                if not SUPABASE_URL or not SUPABASE_KEY:
                    logger.warning("Supabase credentials not found in config")
                    return None
                
                cls._instance = create_client(SUPABASE_URL, SUPABASE_KEY)
                logger.info("✅ Supabase client initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
                return None
                
        return cls._instance
    
    @classmethod
    def is_available(cls) -> bool:
        """Проверить доступность Supabase"""
        try:
            from config import ANALYTICS_ENABLED
            return cls.get_client() is not None and ANALYTICS_ENABLED
        except:
            return False 