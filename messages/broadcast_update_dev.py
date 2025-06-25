#!/usr/bin/env python3
"""
DEV версия скрипта массовой рассылки апдейта v7.x
Безопасное тестирование локально с TEST MODE и REAL MODE
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from telegram import Bot
from telegram.error import TelegramError, Forbidden, BadRequest

# Настройка логирования для dev
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('broadcast_dev.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Импорты проекта
from config import TELEGRAM_BOT_TOKEN
from utils.database import SupabaseClient


class DevUpdateBroadcaster:
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в конфигурации!")
        
        self.token: str = TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.token)
        self.supabase = SupabaseClient.get_client()
        self.stats = {
            'total_users': 0,
            'sent_success': 0,
            'sent_failed': 0,
            'blocked_bot': 0,
            'other_errors': 0
        }
        
        # Dev настройки
        self.test_mode = True
        self.max_users_real = 5  # Максимум пользователей в REAL MODE
        self.admin_telegram_id: Optional[int] = None
    
    async def get_all_users(self, limit_for_test: bool = False) -> List[Dict[str, Any]]:
        """Получить пользователей из БД с ограничениями для тестирования"""
        try:
            if not self.supabase:
                logger.error("Supabase not available!")
                return []
            
            query = self.supabase.table('users').select(
                'id, telegram_user_id, username, first_name, created_at'
            )
            
            # Если указан admin ID, получить только его
            if self.admin_telegram_id:
                query = query.eq('telegram_user_id', self.admin_telegram_id)
                logger.info(f"🎯 Фильтр по admin ID: {self.admin_telegram_id}")
            
            # Ограничение для REAL MODE
            elif limit_for_test:
                query = query.limit(self.max_users_real)
                logger.info(f"🛡️ Ограничение для REAL MODE: максимум {self.max_users_real} пользователей")
            
            response = query.execute()
            users = response.data or []
            logger.info(f"Получено {len(users)} пользователей из БД")
            return users
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return []
    
    def get_dev_update_message(self) -> str:
        """Текст сообщения об апдейте v7.x с пометкой DEV"""
        return """🧪 <b>[DEV TEST] Крутое обновление в Сопровод!</b>

Привет! Мы запустили МЕГА-апдейт бота с кучей новых фишек:

<b>🆕 Что нового:</b>
✅ <b>Улучшение писем</b> - теперь можно попросить переписать письмо (до 3 раз!)
✅ <b>Лайки и оценки</b> - оцени письмо и помоги нам стать лучше  
✅ <b>Быстрее и стабильнее</b> - улучшили архитектуру и обработку ошибок

<b>🔥 Главное:</b>
Теперь если письмо не идеально - просто нажми "🔄 Улучшить письмо" и объясни что изменить. Бот переписывает с учетом твоих пожеланий!

<b>💡 Как пользоваться:</b>
1. Отправь вакансию
2. Отправь резюме  
3. Получи письмо
4. Оцени: ❤️ или 👎
5. Если нужно - улучши!

🚀 <b>Попробуй прямо сейчас!</b>

/start - Создать новое письмо

<i>🧪 Это тестовое сообщение из DEV окружения</i>"""
    
    async def send_to_user_test(self, user: Dict[str, Any]) -> bool:
        """Эмулировать отправку сообщения (TEST MODE)"""
        telegram_id = user['telegram_user_id']
        username = user.get('username', 'unknown')
        first_name = user.get('first_name', 'Пользователь')
        
        # Эмулируем отправку
        await asyncio.sleep(0.1)  # Имитируем задержку API
        
        # Эмулируем разные результаты
        import random
        if random.random() < 0.8:  # 80% успешных
            logger.info(f"✅ [TEST] Эмулируем отправку: @{username} ({first_name})")
            self.stats['sent_success'] += 1
            return True
        elif random.random() < 0.6:  # 10% заблокировали
            logger.warning(f"🚫 [TEST] Эмулируем блокировку: @{username}")
            self.stats['blocked_bot'] += 1
            return False
        else:  # 10% другие ошибки
            logger.error(f"❌ [TEST] Эмулируем ошибку: @{username}")
            self.stats['other_errors'] += 1
            return False
    
    async def send_to_user_real(self, user: Dict[str, Any]) -> bool:
        """Реально отправить сообщение (REAL MODE)"""
        telegram_id = user['telegram_user_id']
        username = user.get('username', 'unknown')
        first_name = user.get('first_name', 'Пользователь')
        
        try:
            message = self.get_dev_update_message()
            
            await self.bot.send_message(
                chat_id=int(telegram_id),
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"✅ [REAL] Отправлено: @{username} ({first_name})")
            self.stats['sent_success'] += 1
            return True
            
        except Forbidden:
            logger.warning(f"🚫 [REAL] Пользователь заблокировал бота: @{username}")
            self.stats['blocked_bot'] += 1
            return False
            
        except BadRequest as e:
            if "chat not found" in str(e).lower():
                logger.warning(f"❓ [REAL] Чат не найден: @{username}")
            else:
                logger.error(f"❌ [REAL] BadRequest для @{username}: {e}")
            self.stats['other_errors'] += 1
            return False
            
        except TelegramError as e:
            logger.error(f"❌ [REAL] Telegram ошибка для @{username}: {e}")
            self.stats['sent_failed'] += 1
            return False
            
        except Exception as e:
            logger.error(f"❌ [REAL] Неизвестная ошибка для @{username}: {e}")
            self.stats['other_errors'] += 1
            return False
    
    def get_mode_selection(self) -> tuple[bool, bool]:
        """Выбор режима работы"""
        print("\n🧪 DEV BROADCAST РЕЖИМЫ:")
        print("1. TEST MODE - Безопасная эмуляция (рекомендуется)")
        print("2. REAL MODE - Реальная отправка (ОСТОРОЖНО!)")
        
        while True:
            choice = input("\n❓ Выберите режим (1 или 2): ").strip()
            if choice == "1":
                return True, False  # test_mode=True, real_mode=False
            elif choice == "2":
                print("\n⚠️  ВНИМАНИЕ! REAL MODE отправляет реальные сообщения!")
                print(f"🛡️ Максимум {self.max_users_real} пользователей")
                confirm = input("❓ Вы уверены? (yes/no): ").lower().strip()
                if confirm in ['yes', 'y', 'да']:
                    return False, True  # test_mode=False, real_mode=True
            else:
                print("❌ Введите 1 или 2")
    
    def get_admin_id(self) -> Optional[int]:
        """Получить админский Telegram ID для тестирования"""
        admin_input = input("\n❓ Ваш Telegram ID для тестирования (Enter - пропустить): ").strip()
        if admin_input:
            try:
                return int(admin_input)
            except ValueError:
                print("❌ Неверный формат ID, пропускаем")
        return None
    
    async def broadcast_update_dev(self, delay_between_messages: float = 0.3):
        """DEV рассылка с выбором режима"""
        logger.info("🧪 Начинаем DEV рассылку апдейта v7.x")
        
        # Выбор режима
        is_test_mode, is_real_mode = self.get_mode_selection()
        self.test_mode = is_test_mode
        
        # Получить админский ID
        self.admin_telegram_id = self.get_admin_id()
        
        # Получаем пользователей
        users = await self.get_all_users(limit_for_test=is_real_mode)
        if not users:
            logger.error("Нет пользователей для рассылки!")
            return
        
        self.stats['total_users'] = len(users)
        
        # Информация о режиме
        mode_name = "TEST MODE" if is_test_mode else "REAL MODE"
        print(f"\n🎯 Режим: {mode_name}")
        print(f"📊 Пользователей: {len(users)}")
        if self.admin_telegram_id:
            print(f"👤 Админ ID: {self.admin_telegram_id}")
        
        # Подтверждение
        confirm = input(f"\n❓ Запустить {mode_name}? (yes/no): ").lower().strip()
        if confirm not in ['yes', 'y', 'да']:
            logger.info("❌ Рассылка отменена пользователем")
            return
        
        # Начинаем рассылку
        start_time = datetime.now()
        logger.info(f"📤 Начинаем {mode_name}...")
        
        for i, user in enumerate(users, 1):
            try:
                if is_test_mode:
                    await self.send_to_user_test(user)
                else:
                    await self.send_to_user_real(user)
                
                # Прогресс каждые 5 сообщений в dev
                if i % 5 == 0:
                    logger.info(f"📊 Прогресс: {i}/{len(users)} ({i/len(users)*100:.1f}%)")
                
                # Пауза между сообщениями
                if delay_between_messages > 0:
                    await asyncio.sleep(delay_between_messages)
                
            except Exception as e:
                logger.error(f"Критическая ошибка при отправке: {e}")
                continue
        
        # Финальная статистика
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"🎉 {mode_name} ЗАВЕРШЕН!")
        logger.info("📊 СТАТИСТИКА:")
        logger.info(f"   Режим: {mode_name}")
        logger.info(f"   Всего пользователей: {self.stats['total_users']}")
        logger.info(f"   ✅ Успешно отправлено: {self.stats['sent_success']}")
        logger.info(f"   ❌ Ошибки отправки: {self.stats['sent_failed']}")
        logger.info(f"   🚫 Заблокировали бота: {self.stats['blocked_bot']}")
        logger.info(f"   ❓ Другие ошибки: {self.stats['other_errors']}")
        logger.info(f"   ⏱️  Время выполнения: {duration}")
        
        if self.stats['total_users'] > 0:
            success_rate = self.stats['sent_success'] / self.stats['total_users'] * 100
            logger.info(f"   📈 Успешность: {success_rate:.1f}%")
        
        if is_test_mode:
            print(f"\n✅ {mode_name} завершен. Никаких реальных сообщений не отправлено.")
        else:
            print(f"\n⚠️  {mode_name} завершен. Отправлено {self.stats['sent_success']} реальных сообщений!")


async def main():
    """Главная функция DEV"""
    try:
        broadcaster = DevUpdateBroadcaster()
        
        # Тест подключения
        async with broadcaster.bot:
            bot_info = await broadcaster.bot.get_me()
            logger.info(f"🤖 Подключен к боту: @{bot_info.username}")
            
            # Проверка БД
            if not broadcaster.supabase:
                logger.error("❌ Нет подключения к Supabase!")
                return
            
            # Запуск dev рассылки
            await broadcaster.broadcast_update_dev(delay_between_messages=0.3)
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return


if __name__ == "__main__":
    print("🧪 DEV МАССОВАЯ РАССЫЛКА АПДЕЙТА v7.x")
    print("=" * 50)
    print("🛡️ Безопасное тестирование с TEST MODE и REAL MODE")
    asyncio.run(main())