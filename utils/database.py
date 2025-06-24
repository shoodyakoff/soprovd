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
                    print("❌ Supabase library not available")
                    cls._failed_init = True
                    return None
                
                # Импортируем переменные из config.py
                from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, ANALYTICS_ENABLED
                
                print("🔍 RAILWAY DEBUG: Supabase configuration check")
                print(f"   ANALYTICS_ENABLED: {ANALYTICS_ENABLED}")
                print(f"   SUPABASE_URL: {SUPABASE_URL[:50] if SUPABASE_URL else 'None'}...")
                print(f"   SUPABASE_KEY: {SUPABASE_KEY[:30] if SUPABASE_KEY else 'None'}...")
                print(f"   SUPABASE_SERVICE_KEY: {SUPABASE_SERVICE_KEY[:30] if SUPABASE_SERVICE_KEY else 'None'}...")
                
                if not ANALYTICS_ENABLED:
                    logger.info("Analytics disabled by configuration")
                    print("⚠️ Analytics disabled by ANALYTICS_ENABLED=false")
                    cls._failed_init = True
                    return None
                
                if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
                    logger.warning("Supabase credentials not found in config")
                    print("❌ Supabase credentials missing!")
                    print(f"   SUPABASE_URL exists: {bool(SUPABASE_URL)}")
                    print(f"   SUPABASE_SERVICE_KEY exists: {bool(SUPABASE_SERVICE_KEY)}")
                    cls._failed_init = True
                    return None
                
                print(f"🔄 Trying to initialize Supabase client with SERVICE KEY...")
                
                # 🔑 ИСПОЛЬЗУЕМ SERVICE KEY для записи в аналитику!
                cls._instance = create_client(
                    supabase_url=SUPABASE_URL,
                    supabase_key=SUPABASE_SERVICE_KEY
                )
                logger.info("✅ Supabase client initialized successfully")
                print("✅ Supabase client initialized successfully")
                
                # Тестируем подключение
                try:
                    test_result = cls._instance.table('users').select('id').limit(1).execute()
                    print("✅ Supabase connection test passed")
                    logger.info("✅ Supabase connection test passed")
                except Exception as test_e:
                    print(f"❌ Supabase connection test failed: {test_e}")
                    logger.error(f"❌ Supabase connection test failed: {test_e}")
                    # Не фейлим инициализацию, может быть проблема с правами
                
            except TypeError as e:
                if "proxy" in str(e):
                    logger.error(f"❌ Supabase version incompatibility (proxy argument): {e}")
                    print(f"❌ Supabase version incompatibility - need different version")
                else:
                    logger.error(f"❌ Supabase TypeError: {e}")
                    print(f"❌ Supabase TypeError: {e}")
                cls._failed_init = True
                print("⚠️ Бот будет работать без аналитики Supabase")
                return None
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
                print(f"❌ Failed to initialize Supabase client: {e}")
                cls._failed_init = True
                print("⚠️ Бот будет работать без аналитики Supabase")
                return None
                
        return cls._instance
    
    @classmethod
    def is_available(cls) -> bool:
        """Проверить доступность Supabase"""
        try:
            from config import ANALYTICS_ENABLED
            client_available = cls.get_client() is not None
            result = client_available and ANALYTICS_ENABLED
            print(f"🔍 Supabase availability check: client={client_available}, enabled={ANALYTICS_ENABLED}, result={result}")
            return result
        except Exception as e:
            print(f"❌ Error checking Supabase availability: {e}")
            return False 