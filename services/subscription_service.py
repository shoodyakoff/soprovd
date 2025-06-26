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
        
    async def check_user_limits(self, user_id: int) -> Dict[str, Any]:
        """
        Проверить лимиты пользователя:
        - FREE: 3 письма в месяц
        - PREMIUM: 20 писем в день
        Возвращает: {
            'can_generate': bool,
            'letters_used': int,
            'letters_limit': int,
            'plan_type': str,
            'remaining': int,
            'period_type': str
        }
        """
        if not self.enabled:
            # Если подписки выключены - даем Free план вместо unlimited
            return self._free_access_fallback()
        
        try:
            if not self.supabase:
                logger.warning("Supabase not available, giving Free access")
                return self._free_access_fallback()
            
            # Получаем подписку пользователя
            response = self.supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()
            
            if not response.data:
                logger.info(f"No subscription found for user {user_id}, using existing analytics method")
                # Используем существующий метод из analytics_service
                from services.analytics_service import analytics
                subscription = await analytics.get_or_create_subscription(user_id)
                if not subscription:
                    logger.error(f"Failed to create subscription for user {user_id}")
                    return self._free_access_fallback()
                # Получаем созданную подписку
                response = self.supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()
                if not response.data:
                    logger.error(f"Analytics created subscription but not found in DB for user {user_id}")
                    return self._free_access_fallback()
            
            subscription = response.data[0]
            
            letters_used = subscription['letters_used']
            letters_limit = subscription['letters_limit']
            plan_type = subscription['plan_type']
            status = subscription['status']
            period_end = subscription['period_end']
            
            # Проверяем статус подписки
            if status != 'active':
                return {
                    'can_generate': False,
                    'letters_used': letters_used,
                    'letters_limit': letters_limit,
                    'plan_type': plan_type,
                    'remaining': 0,
                    'period_type': 'monthly' if plan_type == 'free' else 'daily',
                    'error': 'Подписка неактивна'
                }
            
            # Проверяем, не истек ли период (дневной для premium, месячный для free)
            today = date.today()
            period_end_date = datetime.fromisoformat(period_end.replace('Z', '+00:00')).date()
            
            if today > period_end_date:
                # Период истек - сбрасываем счетчик
                await self._reset_limits(user_id, plan_type)
                letters_used = 0
            
            remaining = max(0, letters_limit - letters_used)
            can_generate = remaining > 0
            
            return {
                'can_generate': can_generate,
                'letters_used': letters_used,
                'letters_limit': letters_limit,
                'plan_type': plan_type,
                'remaining': remaining,
                'period_type': 'monthly' if plan_type == 'free' else 'daily'
            }
            
        except Exception as e:
            logger.error(f"Error checking user limits: {e}")
            # В случае ошибки даем Free доступ, а не unlimited
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
        Увеличить счетчик использованных писем
        ТОЛЬКО для новых сессий, НЕ для итераций!
        """
        if not self.enabled:
            return True
            
        try:
            if not self.supabase:
                return True
            
            # Получаем текущее значение
            response = self.supabase.table('subscriptions').select('letters_used').eq('user_id', user_id).execute()
            if not response.data:
                logger.info(f"No subscription found for user {user_id} during increment, using analytics method")
                from services.analytics_service import analytics
                subscription = await analytics.get_or_create_subscription(user_id)
                if not subscription:
                    logger.error(f"Failed to create subscription for increment for user {user_id}")
                    return False
                response = self.supabase.table('subscriptions').select('letters_used').eq('user_id', user_id).execute()
                if not response.data:
                    logger.error(f"Analytics subscription not found in increment for user {user_id}")
                    return False
            
            current_used = response.data[0]['letters_used']
            new_used = current_used + 1
            
            # Увеличиваем счетчик
            self.supabase.table('subscriptions').update({
                'letters_used': new_used
            }).eq('user_id', user_id).execute()
            
            logger.info(f"Letter usage incremented for user {user_id}: {current_used} -> {new_used}")
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")
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

# Глобальный экземпляр
subscription_service = SubscriptionService() 