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
    """Supabase клиент с улучшенной обработкой ошибок"""
    _instance: Optional[object] = None
    _failed_init = False
    
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
                
                if not SUPABASE_URL or not SUPABASE_KEY:
                    logger.warning("Supabase credentials not found in config")
                    cls._failed_init = True
                    return None
                
                print(f"🔄 Trying to initialize Supabase client...")
                
                # Создаем клиент с минимальными параметрами
                cls._instance = create_client(
                    supabase_url=SUPABASE_URL,
                    supabase_key=SUPABASE_KEY
                )
                logger.info("✅ Supabase client initialized successfully")
                print("✅ Supabase client initialized successfully")
                
            except TypeError as e:
                if "proxy" in str(e):
                    logger.error(f"❌ Supabase version incompatibility (proxy argument): {e}")
                    print(f"❌ Supabase version incompatibility - need different version")
                else:
                    logger.error(f"❌ Supabase TypeError: {e}")
                cls._failed_init = True
                print("⚠️ Бот будет работать без аналитики Supabase")
                return None
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
                cls._failed_init = True
                print("⚠️ Бот будет работать без аналитики Supabase")
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