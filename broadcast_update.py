#!/usr/bin/env python3
"""
Скрипт массовой рассылки апдейта v7.x всем пользователям бота
ИСПОЛЬЗОВАТЬ ОСТОРОЖНО! Только на продакшене!
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

from telegram import Bot
from telegram.error import TelegramError, Forbidden, BadRequest

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('broadcast.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Импорты проекта
from config import TELEGRAM_BOT_TOKEN
from utils.database import SupabaseClient


class UpdateBroadcaster:
    def __init__(self):
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в конфигурации!")
        
        # Явно указываем тип для линтера
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
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей из БД"""
        try:
            if not self.supabase:
                logger.error("Supabase not available!")
                return []
            
            response = self.supabase.table('users').select(
                'id, telegram_user_id, username, first_name, created_at'
            ).execute()
            
            users = response.data or []
            logger.info(f"Получено {len(users)} пользователей из БД")
            return users
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return []
    
    def get_update_message(self) -> str:
        """Текст сообщения об апдейте v7.x"""
        return """🎉 <b>Крутое обновление в Сопровод!</b>

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

/start - Создать новое письмо"""
    
    async def send_to_user(self, user: Dict[str, Any]) -> bool:
        """Отправить сообщение одному пользователю"""
        telegram_id = user['telegram_user_id']
        username = user.get('username', 'unknown')
        first_name = user.get('first_name', 'Пользователь')
        
        try:
            message = self.get_update_message()
            
            # Используем современный синтаксис
            await self.bot.send_message(
                chat_id=int(telegram_id),
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"✅ Отправлено: @{username} ({first_name})")
            self.stats['sent_success'] += 1
            return True
            
        except Forbidden:
            logger.warning(f"🚫 Пользователь заблокировал бота: @{username}")
            self.stats['blocked_bot'] += 1
            return False
            
        except BadRequest as e:
            if "chat not found" in str(e).lower():
                logger.warning(f"❓ Чат не найден: @{username}")
            else:
                logger.error(f"❌ BadRequest для @{username}: {e}")
            self.stats['other_errors'] += 1
            return False
            
        except TelegramError as e:
            logger.error(f"❌ Telegram ошибка для @{username}: {e}")
            self.stats['sent_failed'] += 1
            return False
            
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка для @{username}: {e}")
            self.stats['other_errors'] += 1
            return False
    
    async def broadcast_update(self, delay_between_messages: float = 0.5):
        """Массовая рассылка с защитой от лимитов"""
        logger.info("🚀 Начинаем массовую рассылку апдейта v7.x")
        
        # Получаем пользователей
        users = await self.get_all_users()
        if not users:
            logger.error("Нет пользователей для рассылки!")
            return
        
        self.stats['total_users'] = len(users)
        logger.info(f"📊 Будет отправлено {len(users)} сообщений")
        
        # Подтверждение
        print(f"\n🎯 ВНИМАНИЕ! Будет отправлено {len(users)} сообщений.")
        print("⚠️  Это массовая рассылка! Убедись что запускаешь на правильном боте.")
        print("🤖 Проверь что TELEGRAM_BOT_TOKEN указывает на ПРОДАКШН бота.")
        
        confirm = input("\n❓ Продолжить рассылку? (yes/no): ").lower().strip()
        if confirm not in ['yes', 'y', 'да']:
            logger.info("❌ Рассылка отменена пользователем")
            return
        
        # Начинаем рассылку
        start_time = datetime.now()
        logger.info("📤 Начинаем отправку...")
        
        for i, user in enumerate(users, 1):
            try:
                await self.send_to_user(user)
                
                # Прогресс каждые 10 сообщений
                if i % 10 == 0:
                    logger.info(f"📊 Прогресс: {i}/{len(users)} ({i/len(users)*100:.1f}%)")
                
                # Пауза между сообщениями (защита от лимитов)
                if delay_between_messages > 0:
                    await asyncio.sleep(delay_between_messages)
                
            except Exception as e:
                logger.error(f"Критическая ошибка при отправке: {e}")
                continue
        
        # Финальная статистика
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🎉 РАССЫЛКА ЗАВЕРШЕНА!")
        logger.info("📊 СТАТИСТИКА:")
        logger.info(f"   Всего пользователей: {self.stats['total_users']}")
        logger.info(f"   ✅ Успешно отправлено: {self.stats['sent_success']}")
        logger.info(f"   ❌ Ошибки отправки: {self.stats['sent_failed']}")
        logger.info(f"   🚫 Заблокировали бота: {self.stats['blocked_bot']}")
        logger.info(f"   ❓ Другие ошибки: {self.stats['other_errors']}")
        logger.info(f"   ⏱️  Время выполнения: {duration}")
        
        # Защита от деления на ноль
        if self.stats['total_users'] > 0:
            success_rate = self.stats['sent_success'] / self.stats['total_users'] * 100
            logger.info(f"   📈 Успешность: {success_rate:.1f}%")


async def main():
    """Главная функция"""
    try:
        broadcaster = UpdateBroadcaster()
        
        # Тест подключения
        async with broadcaster.bot:
            bot_info = await broadcaster.bot.get_me()
            logger.info(f"🤖 Подключен к боту: @{bot_info.username}")
            
            # Проверка БД
            if not broadcaster.supabase:
                logger.error("❌ Нет подключения к Supabase!")
                return
            
            # Запуск рассылки
            await broadcaster.broadcast_update(delay_between_messages=0.5)
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return


if __name__ == "__main__":
    print("🚀 МАССОВАЯ РАССЫЛКА АПДЕЙТА v7.x")
    print("=" * 50)
    asyncio.run(main())