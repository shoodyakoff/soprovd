"""
Сервис управления подписками v7.0
Простая проверка лимитов без платежей
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from utils.database import SupabaseClient
from config import SUBSCRIPTIONS_ENABLED, FREE_LETTERS_LIMIT, PREMIUM_LETTERS_LIMIT
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self):
        self.supabase = SupabaseClient.get_client()
        self.enabled = SUBSCRIPTIONS_ENABLED and SupabaseClient.is_available()
    
    def _parse_period_end_safely(self, period_end) -> date:
        """Безопасно парсит дату окончания периода (исправлено для v9.10)"""
        try:
            # Обрабатываем случай None (новые подписки без установленного period_end)
            if period_end is None:
                logger.info("period_end is None, returning yesterday to trigger reset")
                return date.today() - timedelta(days=1)
            
            if isinstance(period_end, str):
                # Убираем различные timezone маркеры
                clean_date = period_end.replace('Z', '').replace('+00:00', '').replace('T', ' ')
                # Пробуем разные форматы
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        return datetime.strptime(clean_date, fmt).date()
                    except ValueError:
                        continue
                # Fallback на fromisoformat
                return datetime.fromisoformat(clean_date.split('.')[0]).date()
            else:
                return period_end.date() if hasattr(period_end, 'date') else period_end
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing period_end date: {period_end}, error: {e}")
            # Возвращаем вчерашнюю дату чтобы сбросить лимиты
            return date.today() - timedelta(days=1)
        
    async def check_user_limits(self, user_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Проверить лимиты пользователя:
        - FREE: 3 письма в месяц
        - PREMIUM: 20 писем в день
        
        Args:
            user_id: ID пользователя
            force_refresh: Принудительно перечитать данные из БД
            
        Возвращает: {
            'can_generate': bool,
            'letters_used': int,
            'letters_limit': int,
            'plan_type': str,
            'remaining': int,
            'period_type': str,
            'is_active': bool,
            'period_end': Optional[str]
        }
        """
        if not self.enabled or not self.supabase:
            logger.warning("Subscription service is disabled or Supabase client is not available.")
            return self._free_access_fallback()
        
        if force_refresh:
            logger.info(f"🔄 Force refreshing limits for user {user_id}")
        
        try:
            response = self.supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()
            
            if not response.data:
                logger.info(f"No subscription found for user {user_id}, attempting to create one.")
                from services.analytics_service import analytics
                if hasattr(analytics, 'supabase') and analytics.supabase:
                    subscription = await analytics.get_or_create_subscription(user_id)
                    if not subscription:
                        logger.error(f"Failed to create subscription for user {user_id}")
                        return self._free_access_fallback()
                    
                    response = self.supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()
                    if not response.data:
                        logger.error(f"Analytics created subscription but not found in DB for user {user_id}")
                        return self._free_access_fallback()
                else:
                    logger.error(f"Analytics service or its Supabase client is not available.")
                    return self._free_access_fallback()
            
            subscription = response.data[0]
            
            letters_used = subscription.get('letters_used', 0)
            letters_limit = subscription.get('letters_limit', FREE_LETTERS_LIMIT)
            plan_type = subscription.get('plan_type', 'free')
            status = subscription.get('status', 'inactive')
            period_end = subscription.get('period_end')
            
            is_active = status == 'active'
            
            # Проверяем, не истек ли период
            today = date.today()
            period_end_date = self._parse_period_end_safely(period_end)
            
            if today > period_end_date:
                await self._reset_limits(user_id, plan_type)
                letters_used = 0
                is_active = plan_type == 'free' # Premium становится неактивным
            
            remaining = max(0, letters_limit - letters_used)
            can_generate = remaining > 0 and is_active
            
            return {
                'can_generate': can_generate,
                'letters_used': letters_used,
                'letters_limit': letters_limit,
                'plan_type': plan_type,
                'remaining': remaining,
                'period_type': 'monthly' if plan_type == 'free' else 'daily',
                'is_active': is_active,
                'period_end': period_end
            }
            
        except Exception as e:
            logger.error(f"Error checking user limits: {e}")
            return self._free_access_fallback()
    

    
    def _free_access_fallback(self) -> Dict[str, Any]:
        """Free доступ (fallback для новых пользователей)"""
        return {
            'can_generate': True,
            'letters_used': 0,
            'letters_limit': 3,
            'plan_type': 'free',
            'remaining': 3,
            'period_type': 'monthly'
        }
    

    
    async def _check_and_reset_period(self, user_id: int) -> bool:
        """Проверить и сбросить период если нужно (для исправления проблемы лимитов)"""
        try:
            if not self.supabase:
                return False
            
            # Получаем подписку
            response = self.supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()
            if not response.data:
                return False
            
            subscription = response.data[0]
            plan_type = subscription['plan_type']
            period_end = subscription['period_end']
            
            # Проверяем, не истек ли период
            today = date.today()
            period_end_date = self._parse_period_end_safely(period_end)
            
            if today > period_end_date:
                logger.info(f"🔄 Period expired for user {user_id}, resetting limits")
                await self._reset_limits(user_id, plan_type)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking period for user {user_id}: {e}")
            return False

    async def _reset_limits(self, user_id: int, plan_type: str) -> bool:
        """Сбросить лимиты пользователя в зависимости от плана"""
        try:
            if not self.supabase:
                return False
            
            today = date.today()
            
            if plan_type == 'premium':
                # Premium: дневные лимиты
                tomorrow = today + timedelta(days=1)
                period_end = tomorrow.isoformat()
                period_type = "дневные"
            else:
                # Free: месячные лимиты
                import calendar
                # Следующий месяц
                if today.month == 12:
                    next_month = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    next_month = today.replace(month=today.month + 1, day=1)
                period_end = next_month.isoformat()
                period_type = "месячные"
            
            self.supabase.table('subscriptions').update({
                'letters_used': 0,
                'period_start': today.isoformat(),
                'period_end': period_end
            }).eq('user_id', user_id).execute()
            
            logger.info(f"{period_type} limits reset for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting limits: {e}")
            return False
    
    async def increment_usage(self, user_id: int) -> bool:
        """
        Увеличить счетчик использованных писем АТОМАРНО
        ТОЛЬКО для новых сессий, НЕ для итераций!
        """
        if not self.enabled:
            return True
            
        try:
            if not self.supabase:
                return True
            
            logger.info(f"🔄 Attempting atomic increment for user {user_id}")
            
            # Используем атомарную SQL функцию
            response = self.supabase.rpc('increment_user_letters', {
                'user_id_param': user_id
            }).execute()
            
            if response.data and len(response.data) > 0:
                result = response.data[0]
                new_count = result['new_count']
                can_generate = result['can_generate']
                plan_type = result['plan_type']
                
                logger.info(f"✅ Letter usage incremented atomically for user {user_id}: count={new_count}, can_generate={can_generate}, plan={plan_type}")
                return True
            else:
                logger.error(f"❌ No response from increment_user_letters for user {user_id}")
                return False
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error in atomic increment_usage for user {user_id}: {error_msg}")
            
            # Проверяем тип ошибки для лучшей диагностики
            if "column reference \"plan_type\" is ambiguous" in error_msg:
                logger.warning(f"⚠️ SQL function has ambiguous column reference - using fallback for user {user_id}")
            elif "42702" in error_msg:
                logger.warning(f"⚠️ PostgreSQL error 42702 (ambiguous column) - using fallback for user {user_id}")
            else:
                logger.warning(f"⚠️ Unknown error type - using fallback for user {user_id}")
            
            # Fallback на старую логику только в крайнем случае
            try:
                logger.info(f"🔄 Falling back to manual increment logic for user {user_id}")
                
                # Получаем текущую подписку
                from services.analytics_service import analytics
                subscription = await analytics.get_or_create_subscription(user_id)
                
                if subscription:
                    # Ручное увеличение счетчика
                    current_used = subscription.get('letters_used', 0)
                    new_used = current_used + 1
                    
                    # Обновляем в БД
                    self.supabase.table('subscriptions').update({
                        'letters_used': new_used,
                        'updated_at': 'now()'
                    }).eq('user_id', user_id).execute()
                    
                    logger.info(f"✅ Manual increment successful for user {user_id}: {current_used} -> {new_used}")
                    return True
                else:
                    logger.error(f"❌ No subscription found for manual increment - user {user_id}")
                    return False
                    
            except Exception as fallback_e:
                logger.error(f"❌ Fallback increment also failed for user {user_id}: {fallback_e}")
                return False
    
    def format_limit_message(self, limits: Dict[str, Any]) -> str:
        """Форматировать сообщение о лимитах"""
        if not limits['can_generate']:
            if limits.get('error'):
                return f"❌ {limits['error']}"
            
            period_text = "сегодня" if limits['period_type'] == 'daily' else "в этом месяце"
            reset_text = "завтра" if limits['period_type'] == 'daily' else "в следующем месяце"
            
            return (
                f"<b>Лимит исчерпан!</b>\n\n"
                f"Использовано: {limits['letters_used']}/{limits['letters_limit']} писем {period_text}\n"
                f"План: {limits['plan_type'].title()}\n"
                f"Лимит обновится {reset_text}\n\n"
                f"<b>Premium:</b> 20 писем в день за 199₽/месяц\n"
                f"Написать @shoodyakoff"
            )
        
        # Показываем остаток при малом количестве
        remaining = limits.get('remaining', 0)
        if remaining <= 5:
            period_text = "сегодня" if limits['period_type'] == 'daily' else "в этом месяце"
            return (
                f"<b>Остаток писем {period_text}: {remaining}</b>\n"
                f"Правки письма не засчитываются в лимит"
            )
        
        return ""  # Не показываем сообщение при большом остатке

    def format_subscription_info(self, limits: Dict[str, Any]) -> str:
        """Форматировать информацию о подписке для стартового сообщения"""
        # Определяем название плана
        plan_name = {
            'free': 'Бесплатная',
            'premium': 'Премиум'
        }.get(limits['plan_type'], limits['plan_type'].title())
        
        # Определяем период
        period_text = "сегодня" if limits['period_type'] == 'daily' else "в этом месяце"
        
        # Определяем цвет эмодзи в зависимости от остатка
        if limits['remaining'] == 0:
            emoji = "🔴"
        elif limits['remaining'] <= 3:
            emoji = "🟡"
        else:
            emoji = "🟢"
        
        return (
            f"<b>Подписка:</b> {plan_name}\n"
            f"{emoji} <b>Писем осталось {period_text}:</b> {limits['remaining']}/{limits['letters_limit']}\n"
        )

    async def activate_premium_subscription(self, user_id: int, payment_id: str = None) -> bool:
        """
        Активирует Premium подписку для пользователя после успешного платежа
        
        Args:
            user_id: ID пользователя в БД
            payment_id: ID платежа от ЮKassa (опционально, пока не применим миграцию)
            
        Returns:
            True если активация успешна
        """
        try:
            if not self.supabase:
                logger.error(f"❌ Supabase not available for Premium activation for user {user_id}")
                return False
            
            # Получаем текущую подписку
            response = self.supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()
            
            today = date.today()
            
            if response.data:
                # Есть существующая подписка - ПРОДЛЕВАЕМ
                current_subscription = response.data[0]
                current_period_end = current_subscription.get('period_end')
                
                # Определяем новую дату окончания
                if current_period_end:
                    try:
                        # Парсим текущую дату окончания
                        if isinstance(current_period_end, str):
                            current_end = datetime.fromisoformat(current_period_end.replace('Z', '+00:00')).date()
                        else:
                            current_end = current_period_end
                        
                        # Если подписка еще активна - продлеваем от текущей даты окончания
                        if current_end > today:
                            new_period_end = current_end + timedelta(days=30)
                            logger.info(f"🔄 Extending active Premium subscription for user {user_id}: {current_end} → {new_period_end}")
                        else:
                            # Подписка истекла - начинаем с сегодня
                            new_period_end = today + timedelta(days=30)
                            logger.info(f"🔄 Renewing expired Premium subscription for user {user_id}: {today} → {new_period_end}")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing current period_end, starting fresh: {e}")
                        new_period_end = today + timedelta(days=30)
                else:
                    # Нет даты окончания - начинаем с сегодня
                    new_period_end = today + timedelta(days=30)
                    logger.info(f"🔄 Starting new Premium subscription for user {user_id}: {today} → {new_period_end}")
            else:
                # Нет подписки - создаем новую
                new_period_end = today + timedelta(days=30)
                logger.info(f"🆕 Creating new Premium subscription for user {user_id}: {today} → {new_period_end}")
            
            subscription_data = {
                'user_id': user_id,
                'plan_type': 'premium',
                'status': 'active',
                'letters_used': 0,  # Сбрасываем счетчик при продлении
                'letters_limit': PREMIUM_LETTERS_LIMIT,
                'period_start': today.isoformat(),
                'period_end': new_period_end.isoformat(),
                'upgraded_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Добавляем payment_id только если он не None
            if payment_id is not None:
                subscription_data['payment_id'] = payment_id
            
            if response.data:
                # Обновляем существующую подписку
                self.supabase.table('subscriptions').update(subscription_data).eq('user_id', user_id).execute()
                logger.info(f"✅ Premium subscription extended for user {user_id} until {new_period_end}")
            else:
                # Создаем новую подписку
                subscription_data['created_at'] = datetime.now().isoformat()
                self.supabase.table('subscriptions').insert(subscription_data).execute()
                logger.info(f"✅ Premium subscription created for user {user_id} until {new_period_end}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error activating Premium subscription for user {user_id}: {e}")
            return False

# Глобальный экземпляр
subscription_service = SubscriptionService() 