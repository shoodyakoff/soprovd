import os
from typing import Optional, Any
import logging

# Безопасный импорт Supabase
try:
    from supabase import create_client, Client
    print("✅ Supabase imported successfully")
    SUPABASE_AVAILABLE = True
    SupabaseClientType = Client
except ImportError as e:
    print(f"❌ Supabase import failed: {e}")
    create_client = None
    Client = None
    SUPABASE_AVAILABLE = False
    SupabaseClientType = Any

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase клиент с улучшенной обработкой ошибок"""
    _instance: Optional[Any] = None
    _failed_init = False
    
    @classmethod
    def get_client(cls) -> Optional[Any]:
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
                
                logger.info("🔍 RAILWAY DEBUG: Supabase configuration check")
                logger.info(f"   ANALYTICS_ENABLED: {ANALYTICS_ENABLED}")
                logger.info(f"   SUPABASE_URL: {SUPABASE_URL[:50] if SUPABASE_URL else 'None'}...")
                logger.info(f"   SUPABASE_KEY: {SUPABASE_KEY[:30] if SUPABASE_KEY else 'None'}...")
                logger.info(f"   SUPABASE_SERVICE_KEY: {SUPABASE_SERVICE_KEY[:30] if SUPABASE_SERVICE_KEY else 'None'}...")
                
                if not ANALYTICS_ENABLED:
                    logger.info("Analytics disabled by configuration")
                    logger.warning("⚠️ Analytics disabled by ANALYTICS_ENABLED=false")
                    cls._failed_init = True
                    return None
                
                if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
                    logger.warning("Supabase credentials not found in config")
                    logger.error("❌ Supabase credentials missing!")
                    logger.error(f"   SUPABASE_URL exists: {bool(SUPABASE_URL)}")
                    logger.error(f"   SUPABASE_SERVICE_KEY exists: {bool(SUPABASE_SERVICE_KEY)}")
                    cls._failed_init = True
                    return None
                
                logger.info(f"🔄 Trying to initialize Supabase client with SERVICE KEY...")
                
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
                    logger.info("✅ Supabase connection test passed")
                    print("✅ Supabase connection test passed")
                except Exception as test_e:
                    logger.error(f"❌ Supabase connection test failed: {test_e}")
                    print(f"❌ Supabase connection test failed: {test_e}")
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


# ========================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С СОГЛАСИЕМ ПОЛЬЗОВАТЕЛЕЙ
# ========================================

async def get_user_consent_status(user_id: int) -> Optional[dict]:
    """
    Получить статус согласия пользователя
    
    Args:
        user_id: ID пользователя в системе аналитики
        
    Returns:
        dict с информацией о согласии или None если пользователь не найден
        {
            'consent_given': bool,
            'consent_timestamp': datetime,
            'consent_version': str,
            'marketing_consent': bool
        }
    """
    try:
        client = SupabaseClient.get_client()
        if not client:
            logger.warning("Supabase client not available for consent check")
            return None
            
        result = client.table('users').select(
            'consent_given, consent_timestamp, consent_version, marketing_consent'
        ).eq('id', user_id).execute()
        
        if result.data:
            consent_data = result.data[0]
            logger.info(f"✅ Consent status retrieved for user {user_id}: {consent_data}")
            return consent_data
        else:
            logger.info(f"⚠️ No consent data found for user {user_id}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error getting consent status for user {user_id}: {e}")
        return None


async def save_user_consent(user_id: int, consent_version: str = 'v1.0', marketing_consent: bool = False) -> bool:
    """
    Сохранить согласие пользователя на обработку персональных данных
    
    Args:
        user_id: ID пользователя в системе аналитики
        consent_version: Версия политики конфиденциальности
        marketing_consent: Согласие на маркетинговые коммуникации
        
    Returns:
        bool: True если согласие сохранено успешно
    """
    try:
        client = SupabaseClient.get_client()
        if not client:
            logger.warning("Supabase client not available for consent saving")
            return False
            
        # Обновляем или создаем запись согласия
        result = client.table('users').update({
            'consent_given': True,
            'consent_timestamp': 'now()',
            'consent_version': consent_version,
            'marketing_consent': marketing_consent
        }).eq('id', user_id).execute()
        
        if result.data:
            logger.info(f"✅ Consent saved for user {user_id}, version {consent_version}")
            return True
        else:
            logger.error(f"❌ Failed to save consent for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error saving consent for user {user_id}: {e}")
        return False


async def revoke_user_consent(user_id: int) -> bool:
    """
    Отозвать согласие пользователя (для обработки через email support)
    
    Args:
        user_id: ID пользователя в системе аналитики
        
    Returns:
        bool: True если согласие отозвано успешно
    """
    try:
        client = SupabaseClient.get_client()
        if not client:
            logger.warning("Supabase client not available for consent revocation")
            return False
            
        # Помечаем согласие как отозванное (НЕ удаляем пользователя полностью)
        result = client.table('users').update({
            'consent_given': False,
            'consent_timestamp': 'now()'  # Время отзыва
        }).eq('id', user_id).execute()
        
        if result.data:
            logger.info(f"✅ Consent revoked for user {user_id}")
            return True
        else:
            logger.error(f"❌ Failed to revoke consent for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error revoking consent for user {user_id}: {e}")
        return False


async def check_user_needs_consent(user_id: int) -> bool:
    """
    Проверить нужно ли запросить согласие у пользователя
    
    Args:
        user_id: ID пользователя в системе аналитики
        
    Returns:
        bool: True если нужно запросить согласие
    """
    try:
        consent_status = await get_user_consent_status(user_id)
        
        if consent_status is None:
            # Новый пользователь - нужно согласие
            logger.info(f"🆕 New user {user_id} - consent required")
            return True
            
        if consent_status.get('consent_given') is None:
            # Существующий пользователь без согласия - нужно запросить
            logger.info(f"⚠️ Existing user {user_id} without consent - consent required")
            return True
            
        if consent_status.get('consent_given') is False:
            # Согласие отозвано - нужно новое согласие
            logger.info(f"❌ User {user_id} revoked consent - new consent required")
            return True
            
        # Согласие есть и активно
        logger.info(f"✅ User {user_id} has valid consent")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error checking consent requirement for user {user_id}: {e}")
        # В случае ошибки лучше запросить согласие для безопасности
        return True


async def migrate_existing_users_consent() -> dict:
    """
    Мягкая миграция существующих пользователей - проставить implied consent
    
    Эта функция должна быть запущена ОДИН РАЗ после применения миграции БД
    
    Returns:
        dict: Статистика миграции
    """
    try:
        client = SupabaseClient.get_client()
        if not client:
            logger.warning("Supabase client not available for migration")
            return {'error': 'Database not available'}
            
        # Находим пользователей без согласия
        users_without_consent = client.table('users').select(
            'id'
        ).is_('consent_given', 'null').execute()
        
        if not users_without_consent.data:
            logger.info("✅ No users found without consent - migration complete")
            return {'migrated': 0, 'already_migrated': 0}
            
        # Проставляем implied consent
        migration_result = client.table('users').update({
            'consent_given': True,
            'consent_timestamp': 'now()',
            'consent_version': 'v1.0',
            'marketing_consent': False
        }).is_('consent_given', 'null').execute()
        
        migrated_count = len(users_without_consent.data)
        logger.info(f"✅ Migration complete: {migrated_count} users migrated to implied consent")
        
        return {
            'migrated': migrated_count,
            'already_migrated': 0,
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"❌ Error during consent migration: {e}")
        return {'error': str(e)} 