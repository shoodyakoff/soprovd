import os
from typing import Optional
import logging

# Безопасный импорт Supabase
try:
    from supabase import create_client, Client
    print("✅ Supabase imported successfully")
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Supabase import failed: {e}")
    create_client = None
    Client = None
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance: Optional[object] = None
    _failed_init = False  # Флаг для избежания повторных попыток
    
    @classmethod
    def get_client(cls) -> Optional[object]:
        """Получить клиент Supabase (синглтон)"""
        if cls._instance is None and not cls._failed_init:
            try:
                if not SUPABASE_AVAILABLE or create_client is None:
                    logger.warning("Supabase library not available")
                    cls._failed_init = True
                    return None
                
                # Импортируем переменные из config.py
                from config import SUPABASE_URL, SUPABASE_KEY
                
                print(f"🔍 DATABASE DEBUG: FINAL SUPABASE_URL = {SUPABASE_URL}")
                print(f"🔍 DATABASE DEBUG: FINAL SUPABASE_KEY = {SUPABASE_KEY[:20] if SUPABASE_KEY else 'NONE'}...")
                
                if not SUPABASE_URL or not SUPABASE_KEY:
                    logger.warning("Supabase credentials not found in config")
                    cls._failed_init = True
                    return None
                
                # Создаем клиент с минимальными параметрами, избегая проблем с версиями
                cls._instance = create_client(
                    supabase_url=SUPABASE_URL,
                    supabase_key=SUPABASE_KEY
                )
                logger.info("✅ Supabase client initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
                # Добавляем более детальную информацию об ошибке
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                cls._failed_init = True
                print("⚠️  Бот будет работать без аналитики Supabase")
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