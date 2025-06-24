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
                # DEBUG: Прямо здесь проверим переменные
                print(f"🔍 DATABASE DEBUG: os.getenv('SUPABASE_URL') = {os.getenv('SUPABASE_URL', 'NOT_FOUND')}")
                print(f"🔍 DATABASE DEBUG: os.getenv('SUPABASE_KEY') = {os.getenv('SUPABASE_KEY', 'NOT_FOUND')[:20]}...")
                
                # В production на Railway используем прямое чтение
                if os.getenv('ENVIRONMENT') == 'production':
                    SUPABASE_URL = os.getenv('SUPABASE_URL')
                    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
                    print("🔧 Using direct os.getenv() for production")
                else:
                    # Импортируем переменные из config.py для локальной разработки
                    from config import SUPABASE_URL, SUPABASE_KEY
                    print("🔧 Using config.py imports for development")
                
                print(f"🔍 DATABASE DEBUG: FINAL SUPABASE_URL = {SUPABASE_URL}")
                print(f"🔍 DATABASE DEBUG: FINAL SUPABASE_KEY = {SUPABASE_KEY[:20] if SUPABASE_KEY else 'NONE'}...")
                
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