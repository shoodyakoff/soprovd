# 🧪 Инструкция по запуску рассылки в DEV режиме

## 🚀 БЫСТРЫЙ СТАРТ (5 минут)

### 1. Подготовка окружения
```bash
cd /Users/stas/tg_soprovod
source venv/bin/activate
export ENVIRONMENT=development
```

### 2. Проверь конфигурацию
```bash
# Убедись что в .env.dev есть dev токен бота
grep TELEGRAM_BOT_TOKEN .env.dev
```

### 3. Запуск TEST MODE (безопасно)
```bash
python broadcast_update_dev.py
# Выбери: 1 (TEST MODE)
# Telegram ID: [твой ID или Enter]
# Подтверди: yes
```

### 4. Мониторинг
```bash
# В другом терминале смотри логи:
tail -f broadcast_dev.log
```

**✅ Готово!** TEST MODE только эмулирует отправку, никому ничего не придет.

---

## Безопасное тестирование скрипта рассылки локально

### 📋 Подготовка

1. **Убедись что используешь dev окружение:**
   ```bash
   # Проверь что в .env.dev правильные настройки
   cat .env.dev | grep TELEGRAM_BOT_TOKEN
   cat .env.dev | grep ENVIRONMENT
   ```

2. **Установи переменную окружения:**
   ```bash
   export ENVIRONMENT=development
   ```

3. **Активируй виртуальное окружение:**
   ```bash
   source venv/bin/activate
   ```

### 🚀 Запуск в TEST MODE (рекомендуется)

**TEST MODE** - полностью безопасен, только эмуляция отправки:

```bash
python broadcast_update_dev.py
```

При запуске:
1. Выбери режим `1` (TEST MODE)
2. Введи свой Telegram ID для тестирования (опционально)
3. Подтверди запуск

**Что происходит в TEST MODE:**
- ✅ Подключается к боту
- ✅ Читает пользователей из БД
- ✅ Показывает статистику
- ❌ НЕ отправляет реальные сообщения
- ✅ Логирует все действия в `broadcast_dev.log`

### ⚠️ Запуск в REAL MODE (осторожно!)

**REAL MODE** - отправляет реальные сообщения, но ограниченно:

```bash
python broadcast_update_dev.py
```

При запуске:
1. Выбери режим `2` (REAL MODE)
2. Подтверди что понимаешь риски
3. Подтверди запуск

**Что происходит в REAL MODE:**
- ✅ Ограничивается до 5 пользователей максимум
- ✅ Отправляет реальные сообщения
- ✅ Сообщения помечены как `[DEV TEST]`
- ✅ Логирует все в `broadcast_dev.log`

### 🔍 Мониторинг

**Логи в реальном времени:**
```bash
tail -f broadcast_dev.log
```

**Проверка статистики:**
```bash
grep "СТАТИСТИКА" broadcast_dev.log
```

### 🛡️ Безопасность

**Защитные механизмы в dev версии:**
- 🔒 Максимум 5 пользователей в REAL MODE
- 🔒 Пометка `[DEV TEST]` в сообщениях
- 🔒 Отдельный лог файл `broadcast_dev.log`
- 🔒 Интерактивное подтверждение на каждом шаге
- 🔒 TEST MODE по умолчанию

### 📊 Узнать свой Telegram ID

Для тестирования нужен твой Telegram ID:

1. **Через бота @userinfobot:**
   - Отправь `/start` боту @userinfobot
   - Получишь свой ID

2. **Через dev бота:**
   ```bash
   python -c "
   import asyncio
   from config import TELEGRAM_BOT_TOKEN
   from telegram import Bot
   
   async def get_me():
       bot = Bot(TELEGRAM_BOT_TOKEN)
       async with bot:
           updates = await bot.get_updates()
           if updates:
               print(f'Последний пользователь: {updates[-1].effective_user.id}')
           else:
               print('Нет обновлений, отправь сообщение боту')
   
   asyncio.run(get_me())
   "
   ```

### 🔧 Отладка

**Проблемы с подключением к боту:**
```bash
python -c "
import asyncio
from config import TELEGRAM_BOT_TOKEN
from telegram import Bot

async def test_bot():
    bot = Bot(TELEGRAM_BOT_TOKEN)
    async with bot:
        me = await bot.get_me()
        print(f'Бот: @{me.username}')

asyncio.run(test_bot())
"
```

**Проблемы с БД:**
```bash
python -c "
from utils.database import SupabaseClient
client = SupabaseClient.get_client()
if client:
    result = client.table('users').select('count').execute()
    print(f'Пользователей в БД: {len(result.data) if result.data else 0}')
else:
    print('Нет подключения к Supabase')
"
```

### 📝 Примеры использования

**Быстрый тест (только эмуляция):**
```bash
python broadcast_update_dev.py
# Выбрать 1 (TEST MODE)
# Enter (пропустить admin ID)
# yes (подтвердить)
```

**Тест с отправкой себе:**
```bash
python broadcast_update_dev.py
# Выбрать 1 (TEST MODE)
# Ввести свой Telegram ID
# yes (подтвердить)
```

**Реальная отправка 5 пользователям:**
```bash
python broadcast_update_dev.py
# Выбрать 2 (REAL MODE)
# yes (подтвердить риски)
# yes (подтвердить запуск)
```

### ✅ Чек-лист перед запуском

- [ ] Активировано dev окружение (`ENVIRONMENT=development`)
- [ ] Активировано виртуальное окружение
- [ ] Проверен токен бота в `.env.dev`
- [ ] Выбран правильный режим (TEST для безопасности)
- [ ] Готов мониторить логи
- [ ] Знаешь свой Telegram ID (для тестирования)

### 🚨 Что НЕ делать

- ❌ Не запускай REAL MODE без понимания последствий
- ❌ Не используй продакшн токен в dev
- ❌ Не отключай защитные механизмы
- ❌ Не запускай без мониторинга логов