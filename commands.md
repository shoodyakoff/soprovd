# Команды для управления ботом

## Обнуление подписки пользователя

### SQL команда для обнуления подписки пользователя с ID = 5:

```sql
-- Обнуляем подписку пользователя с ID = 5
UPDATE subscriptions 
SET 
    plan_type = 'free',
    status = 'active',
    letters_used = 0,
    letters_limit = 3,
    period_start = CURRENT_DATE,
    period_end = (CURRENT_DATE + INTERVAL '1 month')::date,
    updated_at = NOW()
WHERE user_id = 5;

-- Проверяем результат
SELECT * FROM subscriptions WHERE user_id = 5;
```

### Python скрипт для обнуления подписки:

```python
# reset_subscription.py
import asyncio
from datetime import date, timedelta
from utils.database import SupabaseClient

async def reset_user_subscription(user_id: int = 5):
    """Обнуляет подписку пользователя до free плана"""
    try:
        supabase = SupabaseClient.get_client()
        if not supabase:
            print("❌ Supabase не доступен")
            return False
        
        today = date.today()
        next_month = today + timedelta(days=30)
        
        # Обновляем подписку
        response = supabase.table('subscriptions').update({
            'plan_type': 'free',
            'status': 'active',
            'letters_used': 0,
            'letters_limit': 3,
            'period_start': today.isoformat(),
            'period_end': next_month.isoformat(),
            'updated_at': 'now()'
        }).eq('user_id', user_id).execute()
        
        if response.data:
            print(f"✅ Подписка пользователя {user_id} обнулена до Free плана")
            print(f"📅 Новый период: {today} - {next_month}")
            return True
        else:
            print(f"❌ Пользователь {user_id} не найден или подписка не обновлена")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обнуления подписки: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(reset_user_subscription(5))
```

### Запуск скрипта:

```bash
python reset_subscription.py
```

---

## Ответы на вопросы:

### 1. Нужен ли webhook_handler.py в проде?

**ДА, обязательно нужен!** 

В продакшене webhook_handler.py будет работать как отдельный FastAPI сервер, который:
- Принимает уведомления от ЮKassa о платежах
- Автоматически активирует Premium подписки
- Отправляет уведомления пользователям

Без него платежи не будут обрабатываться автоматически.

### 2. Автоматизация webhook

**ДА, теперь всё автоматизировано!**

После оплаты по ссылке:
1. ЮKassa автоматически отправляет webhook на ваш сервер
2. webhook_handler.py обрабатывает уведомление
3. Автоматически активируется Premium подписка
4. Пользователь получает сообщение "✅ Оплата прошла, подписка активирована!" + новое сообщение с кнопками

**Больше не нужно вручную дергать webhook** - всё происходит автоматически после реальной оплаты через ЮKassa.

Единственное что нужно в продакшене:
- Настроить публичный URL webhook'а в личном кабинете ЮKassa
- Убедиться что сервер доступен из интернета по HTTPS
