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
    
    @classmethod
    def get_client(cls) -> Optional[object]:
        """Получить клиент Supabase (синглтон)"""
        if cls._instance is None:
            try:
                if not SUPABASE_AVAILABLE or create_client is None:
                    logger.warning("Supabase library not available")
                    return None
                
                # Импортируем переменные из config.py
                from config import SUPABASE_URL, SUPABASE_KEY
                
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