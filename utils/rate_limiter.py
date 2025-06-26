"""
Rate Limiter для защиты от DoS атак
Сопровод v9.2 - Security Protection

Хранение в памяти (без Redis для упрощения)
Sliding window algorithm для точного подсчета
"""
import time
import logging
from typing import Dict, List, Tuple, Optional
from functools import wraps
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    Production-ready rate limiter с хранением в памяти
    
    Лимиты:
    - 5 команд в 60 секунд (общие команды)
    - 3 AI запроса в 300 секунд (генерация писем)
    - 50KB максимальный размер текста
    """
    
    def __init__(self):
        # Sliding window для каждого пользователя и типа действия
        self.user_requests: Dict[str, deque] = defaultdict(deque)
        
        # Конфигурация лимитов
        self.limits = {
            'commands': {'rate': 5, 'window': 60},        # 5 команд/минуту
            'ai_requests': {'rate': 3, 'window': 300},    # 3 AI запроса/5 минут
            'text_size': {'max_size': 50 * 1024}          # 50KB max text
        }
        
        # Админы (обходят лимиты)
        self.admin_ids: List[int] = []
        
        logger.info("🔒 InMemoryRateLimiter initialized")
        logger.info(f"   Commands limit: {self.limits['commands']['rate']}/{self.limits['commands']['window']}s")
        logger.info(f"   AI requests limit: {self.limits['ai_requests']['rate']}/{self.limits['ai_requests']['window']}s")
        logger.info(f"   Text size limit: {self.limits['text_size']['max_size']} bytes")
    
    def set_admin_ids(self, admin_ids: List[int]):
        """Установить список админов (обходят лимиты)"""
        self.admin_ids = admin_ids
        logger.info(f"🔒 Rate limiter admin IDs set: {admin_ids}")
    
    def is_admin(self, user_id: int) -> bool:
        """Проверить является ли пользователь админом"""
        return user_id in self.admin_ids
    
    def check_rate_limit(self, user_id: int, action_type: str) -> Tuple[bool, Dict]:
        """
        Проверить rate limit для пользователя
        
        Returns:
            (allowed: bool, info: dict)
            info содержит: allowed, requests_left, retry_after_seconds, warning
        """
        # Админы обходят лимиты
        if self.is_admin(user_id):
            return True, {
                'allowed': True,
                'requests_left': 999,
                'retry_after_seconds': 0,
                'warning': False,
                'admin_bypass': True
            }
        
        if action_type not in self.limits:
            logger.warning(f"🔒 Unknown action type: {action_type}")
            return True, {'allowed': True, 'requests_left': 999}
        
        limit_config = self.limits[action_type]
        max_requests = limit_config['rate']
        window_seconds = limit_config['window']
        
        # Автоматическая очистка каждые 1000 запросов
        if hasattr(self, '_cleanup_counter'):
            self._cleanup_counter += 1
        else:
            self._cleanup_counter = 1
            
        if self._cleanup_counter % 1000 == 0:
            logger.info(f"🧹 Auto-cleanup triggered at request #{self._cleanup_counter}")
            self.cleanup_old_data()
        
        # Ключ для хранения requests этого пользователя и действия
        key = f"{user_id}:{action_type}"
        current_time = time.time()
        
        # Получаем deque для этого пользователя/действия
        requests_deque = self.user_requests[key]
        
        # Убираем старые запросы (вне sliding window)
        while requests_deque and requests_deque[0] <= current_time - window_seconds:
            requests_deque.popleft()
        
        current_requests = len(requests_deque)
        requests_left = max(0, max_requests - current_requests)
        
        # Предупреждение при 80% лимита
        warning_threshold = int(max_requests * 0.8)
        warning = current_requests >= warning_threshold
        
        if current_requests >= max_requests:
            # Лимит превышен
            # Считаем когда можно будет снова делать запрос
            oldest_request_time = requests_deque[0] if requests_deque else current_time
            retry_after = max(0, int(oldest_request_time + window_seconds - current_time))
            
            logger.warning(f"🔒 RATE_LIMIT exceeded: user_id={user_id}, action={action_type}, "
                         f"requests={current_requests}/{max_requests}, retry_after={retry_after}s")
            
            return False, {
                'allowed': False,
                'requests_left': 0,
                'retry_after_seconds': retry_after,
                'warning': False,
                'current_requests': current_requests,
                'max_requests': max_requests,
                'window_seconds': window_seconds
            }
        
        # Лимит не превышен - добавляем текущий запрос
        requests_deque.append(current_time)
        
        if warning:
            logger.info(f"🔒 RATE_LIMIT warning: user_id={user_id}, action={action_type}, "
                       f"requests={current_requests + 1}/{max_requests} (80% threshold)")
        
        return True, {
            'allowed': True,
            'requests_left': requests_left - 1,  # -1 потому что мы только что добавили запрос
            'retry_after_seconds': 0,
            'warning': warning,
            'current_requests': current_requests + 1,
            'max_requests': max_requests,
            'window_seconds': window_seconds
        }
    
    def check_text_size(self, text: str) -> Tuple[bool, Dict]:
        """
        Проверить размер текста
        
        Returns:
            (allowed: bool, info: dict)
        """
        if not text:
            return True, {'allowed': True, 'size_kb': 0}
        
        text_size = len(text.encode('utf-8'))
        max_size = self.limits['text_size']['max_size']
        size_kb = round(text_size / 1024, 1)
        max_size_kb = round(max_size / 1024, 1)
        
        if text_size > max_size:
            logger.warning(f"🔒 TEXT_SIZE exceeded: size={size_kb}KB, max={max_size_kb}KB")
            return False, {
                'allowed': False,
                'size_kb': size_kb,
                'max_size_kb': max_size_kb,
                'size_bytes': text_size,
                'max_size_bytes': max_size
            }
        
        return True, {
            'allowed': True,
            'size_kb': size_kb,
            'max_size_kb': max_size_kb,
            'size_bytes': text_size,
            'max_size_bytes': max_size
        }
    
    def get_stats(self) -> Dict:
        """Получить статистику rate limiter"""
        total_users = len(set(key.split(':')[0] for key in self.user_requests.keys()))
        total_tracked_actions = len(self.user_requests)
        
        return {
            'total_users_tracked': total_users,
            'total_action_types_tracked': total_tracked_actions,
            'admin_ids': self.admin_ids,
            'limits': self.limits
        }
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """
        Очистка старых данных (вызывать периодически)
        """
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        keys_to_remove = []
        for key, requests_deque in self.user_requests.items():
            # Убираем старые запросы
            while requests_deque and requests_deque[0] <= cutoff_time:
                requests_deque.popleft()
            
            # Если deque пустой, удаляем ключ
            if not requests_deque:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.user_requests[key]
        
        logger.info(f"🔒 Cleanup completed: removed {len(keys_to_remove)} empty entries")


# Глобальный экземпляр rate limiter
rate_limiter = InMemoryRateLimiter()


def rate_limit(action_type: str, check_text_size: bool = False):
    """
    Декоратор для rate limiting
    
    Args:
        action_type: тип действия ('commands', 'ai_requests')
        check_text_size: проверять ли размер текста
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            # Получаем user_id
            user_id = None
            if update.effective_user:
                user_id = update.effective_user.id
            elif update.callback_query and update.callback_query.from_user:
                user_id = update.callback_query.from_user.id
            
            if not user_id:
                logger.warning("🔒 Rate limiter: no user_id found")
                return await func(update, context, *args, **kwargs)
            
            # Проверяем rate limit
            allowed, info = rate_limiter.check_rate_limit(user_id, action_type)
            
            if not allowed:
                # Формируем сообщение об ошибке
                retry_minutes = max(1, int(info['retry_after_seconds'] / 60))
                
                if action_type == 'commands':
                    error_msg = (
                        f"⏱️ <b>Слишком много команд!</b>\n\n"
                        f"📊 Лимит: {info['max_requests']} команд в {info['window_seconds']}с\n"
                        f"⏰ Попробуйте через {retry_minutes} мин\n\n"
                        f"💡 Это защита от спама"
                    )
                elif action_type == 'ai_requests':
                    error_msg = (
                        f"🤖 <b>Лимит AI запросов исчерпан!</b>\n\n"
                        f"📊 Лимит: {info['max_requests']} писем в {info['window_seconds']}с\n"
                        f"⏰ Попробуйте через {retry_minutes} мин\n\n"
                        f"💎 Для увеличения лимитов: /support"
                    )
                else:
                    error_msg = f"⏱️ Лимит действий исчерпан. Попробуйте через {retry_minutes} мин"
                
                # Отправляем сообщение пользователю
                if update.message:
                    await update.message.reply_text(error_msg, parse_mode='HTML')
                elif update.callback_query:
                    await update.callback_query.answer(f"Лимит исчерпан! Попробуйте через {retry_minutes} мин", show_alert=True)
                
                return
            
            # Проверяем размер текста если нужно
            if check_text_size:
                text_to_check = ""
                if update.message and update.message.text:
                    text_to_check = update.message.text
                
                if text_to_check:
                    text_allowed, text_info = rate_limiter.check_text_size(text_to_check)
                    
                    if not text_allowed:
                        error_msg = (
                            f"📄 <b>Текст слишком большой!</b>\n\n"
                            f"📊 Размер: {text_info['size_kb']} КБ\n"
                            f"📋 Максимум: {text_info['max_size_kb']} КБ\n\n"
                            f"💡 Сократите текст и попробуйте снова"
                        )
                        
                        if update.message:
                            await update.message.reply_text(error_msg, parse_mode='HTML')
                        return
            
            # Показываем предупреждение при 80% лимита
            if info.get('warning') and not info.get('admin_bypass'):
                warning_msg = f"⚠️ Внимание: осталось {info['requests_left']} из {info['max_requests']} запросов"
                if update.message:
                    await update.message.reply_text(warning_msg, parse_mode='HTML')
            
            # Вызываем оригинальную функцию
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator 