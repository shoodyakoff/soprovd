"""
Сервис для работы с каналами привлечения пользователей v7.3
Отслеживание UTM-параметров, реферальных ссылок и источников трафика
"""
import logging
import re
from typing import Optional, Dict, Any
from datetime import datetime
from utils.database import SupabaseClient

logger = logging.getLogger(__name__)

class AcquisitionService:
    def __init__(self):
        self.supabase = SupabaseClient.get_client()
        self.enabled = bool(self.supabase)
        
    async def track_user_acquisition(self, user_id: int, start_param: Optional[str] = None, 
                                   referrer_url: Optional[str] = None) -> bool:
        """
        Отслеживает источник привлечения пользователя
        
        Args:
            user_id: ID пользователя
            start_param: параметр из /start команды
            referrer_url: URL реферера (если есть)
        """
        if not self.enabled or not self.supabase:
            return False
            
        try:
            # Парсим UTM параметры из start_param
            utm_data = self._parse_start_param(start_param)
            
            # Определяем реферального пользователя
            referral_user_id = self._extract_referral_user(start_param)
            
            acquisition_data = {
                'user_id': user_id,
                'utm_source': utm_data.get('source'),
                'utm_medium': utm_data.get('medium'),
                'utm_campaign': utm_data.get('campaign'),
                'utm_content': utm_data.get('content'),
                'utm_term': utm_data.get('term'),
                'referrer_url': referrer_url,
                'telegram_start_param': start_param,
                'referral_user_id': referral_user_id,
                'device_type': 'mobile',  # Telegram всегда mobile
                'session_count': 1,
                'first_session_at': datetime.now().isoformat(),
                'last_session_at': datetime.now().isoformat()
            }
            
            # Удаляем None значения
            acquisition_data = {k: v for k, v in acquisition_data.items() if v is not None}
            
            # Сохраняем в БД
            response = self.supabase.table('acquisition_channels').insert(acquisition_data).execute()
            
            logger.info(f"✅ Tracked acquisition for user {user_id}: {utm_data}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error tracking acquisition for user {user_id}: {e}")
            return False
    
    def _parse_start_param(self, start_param: Optional[str]) -> Dict[str, str]:
        """
        Парсит UTM параметры из start параметра Telegram
        
        Поддерживаемые форматы:
        - /start utm_source_google_utm_medium_cpc_utm_campaign_winter
        - /start ref_12345 (реферальная ссылка)
        - /start promo_developers (промо-кампания)
        """
        if not start_param:
            return {}
            
        utm_data = {}
        
        # Убираем /start если есть
        param = start_param.replace('/start ', '').strip()
        
        # Парсим UTM параметры
        if 'utm_' in param:
            # Формат: utm_source_google_utm_medium_cpc_utm_campaign_winter
            parts = param.split('_')
            current_key = None
            current_value = []
            
            for part in parts:
                if part.startswith('utm'):
                    if current_key and current_value:
                        utm_data[current_key] = '_'.join(current_value)
                    current_key = part.replace('utm_', '')
                    current_value = []
                else:
                    current_value.append(part)
            
            # Добавляем последний параметр
            if current_key and current_value:
                utm_data[current_key] = '_'.join(current_value)
                
        # Парсим специальные форматы
        elif param.startswith('ref_'):
            utm_data = {
                'source': 'referral',
                'medium': 'social',
                'campaign': 'referral_program'
            }
        elif param.startswith('promo_'):
            promo_name = param.replace('promo_', '')
            utm_data = {
                'source': 'telegram',
                'medium': 'promo',
                'campaign': promo_name
            }
        elif param.startswith('ad_'):
            ad_name = param.replace('ad_', '')
            utm_data = {
                'source': 'telegram_ads',
                'medium': 'cpc',
                'campaign': ad_name
            }
        else:
            # Неизвестный формат - сохраняем как есть
            utm_data = {
                'source': 'telegram',
                'medium': 'organic',
                'content': param
            }
            
        return utm_data
    
    def _extract_referral_user(self, start_param: Optional[str]) -> Optional[int]:
        """Извлекает ID реферального пользователя"""
        if not start_param:
            return None
            
        # Ищем паттерн ref_12345
        match = re.search(r'ref_(\d+)', start_param)
        if match:
            return int(match.group(1))
            
        return None
    
    async def update_session_count(self, user_id: int) -> bool:
        """Обновляет счетчик сессий для пользователя"""
        if not self.enabled or not self.supabase:
            return False
            
        try:
            # Обновляем счетчик и последнюю активность
            response = self.supabase.table('acquisition_channels').update({
                'session_count': self.supabase.table('acquisition_channels').select('session_count').eq('user_id', user_id).execute().data[0]['session_count'] + 1,
                'last_session_at': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating session count for user {user_id}: {e}")
            return False
    
    async def get_user_acquisition_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает данные о привлечении пользователя"""
        if not self.enabled or not self.supabase:
            return None
            
        try:
            response = self.supabase.table('acquisition_channels').select('*').eq('user_id', user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting acquisition data for user {user_id}: {e}")
            return None
    
    async def get_acquisition_stats(self, days: int = 30) -> Dict[str, Any]:
        """Получает статистику по каналам привлечения"""
        if not self.enabled or not self.supabase:
            return {}
            
        try:
            # Получаем статистику через VIEW
            response = self.supabase.table('acquisition_stats').select('*').execute()
            
            return {
                'channels': response.data,
                'total_users': sum(item['users'] for item in response.data),
                'avg_conversion_rate': sum(item['conversion_rate'] for item in response.data) / len(response.data) if response.data else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting acquisition stats: {e}")
            return {}

# Глобальный экземпляр
acquisition_service = AcquisitionService()

# =====================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# =====================================================

"""
# В start_conversation добавить:
start_param = context.args[0] if context.args else None
await acquisition_service.track_user_acquisition(
    user_id=user_id, 
    start_param=start_param
)

# Примеры ссылок для маркетинга:
https://t.me/your_bot?start=utm_source_google_utm_medium_cpc_utm_campaign_winter2024
https://t.me/your_bot?start=utm_source_habr_utm_medium_article_utm_campaign_developers
https://t.me/your_bot?start=ref_12345  # реферальная от пользователя 12345
https://t.me/your_bot?start=promo_newyear  # промо-кампания
https://t.me/your_bot?start=ad_banner1  # реклама
""" 