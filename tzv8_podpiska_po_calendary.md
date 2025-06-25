# 🗓️ Техническое задание: Переход на календарную систему подписок v8.0

## 🚨 ПРОБЛЕМА (КРИТИЧЕСКАЯ)

### Текущие баги в системе лимитов:
1. **Лимиты не сбрасываются автоматически** - сброс происходит только при следующем обращении пользователя
2. **Неправильная логика календарных дней** - PREMIUM период создается как `+1 день` от момента подключения
3. **Нет синхронизации с московским временем** - может работать некорректно в разных часовых поясах  
4. **Отсутствует фоновый сброс лимитов** - пользователи могут не получить доступ до первого запроса

## 🎯 ЦЕЛЬ

Создать надежную календарную систему подписок где:
- **FREE**: лимиты сбрасываются 1 числа каждого месяца в 00:00 МСК
- **PREMIUM**: лимиты сбрасываются каждый день в 00:00 МСК
- **Автоматический сброс** работает независимо от активности пользователей
- **Точная синхронизация** с календарными периодами

---

## 📋 ЗАДАЧИ

### ✅ ЭТАП 1: ДИАГНОСТИКА И ИСПРАВЛЕНИЕ ТЕКУЩИХ БАГОВ

#### 1.1 Исследование текущей проблемы
- [ ] Проверить данные подписки пользователя `Stanislav` в БД
- [ ] Выяснить почему лимит показывает 9 вместо 20
- [ ] Найти где теряется логика сброса

#### 1.2 Быстрое исправление (HOTFIX)
- [ ] Добавить функцию принудительного сброса лимитов
- [ ] Создать SQL скрипт для ручного исправления подписок
- [ ] Исправить подписку `Stanislav` до полноценного релиза

### ✅ ЭТАП 2: НОВАЯ КАЛЕНДАРНАЯ ЛОГИКА

#### 2.1 Обновление логики сброса периодов
```python
# СТАРАЯ логика (НЕПРАВИЛЬНАЯ):
if today > period_end_date:
    await self._reset_limits(user_id, plan_type)

# НОВАЯ логика (ПРАВИЛЬНАЯ):
if self._should_reset_calendar_limits(subscription, today):
    await self._reset_calendar_limits(user_id, plan_type, today)
```

#### 2.2 Функции календарного сброса
- [ ] `_should_reset_calendar_limits()` - определить нужен ли сброс
- [ ] `_reset_calendar_limits()` - сбросить лимиты по календарю
- [ ] `_get_next_reset_date()` - вычислить следующую дату сброса
- [ ] `_get_moscow_time()` - работа с московским временем

#### 2.3 Календарные периоды
```python
def _get_next_reset_date(self, plan_type: str, current_date: date) -> date:
    """Получить дату следующего сброса лимитов"""
    if plan_type == 'premium':
        # PREMIUM: следующий день в 00:00 МСК
        return current_date + timedelta(days=1)
    else:
        # FREE: первое число следующего месяца в 00:00 МСК
        if current_date.month == 12:
            return date(current_date.year + 1, 1, 1)
        else:
            return date(current_date.year, current_date.month + 1, 1)
```

### ✅ ЭТАП 3: ФОНОВЫЙ СБРОС ЛИМИТОВ

#### 3.1 Периодическая задача для сброса
- [ ] Создать async задачу `periodic_limits_reset()`
- [ ] Запуск каждые 5 минут с проверкой времени
- [ ] Сброс лимитов всех пользователей в 00:05 МСК

#### 3.2 Надежность и отказоустойчивость
- [ ] Логирование всех операций сброса
- [ ] Повторные попытки при ошибках БД
- [ ] Уведомления администратора при сбоях

### ✅ ЭТАП 4: ОБНОВЛЕНИЕ БД И СХЕМЫ

#### 4.1 Новые поля в таблице subscriptions
```sql
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS 
    last_reset_date DATE DEFAULT CURRENT_DATE;
    
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS 
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow';
```

#### 4.2 Миграция существующих данных
- [ ] Скрипт для пересчета всех `period_end` по календарным правилам
- [ ] Установка `last_reset_date` для всех подписок
- [ ] Исправление неправильных лимитов

### ✅ ЭТАП 5: УЛУЧШЕНИЕ UX

#### 5.1 Информативные сообщения
```python
# PREMIUM
"📊 Остаток писем сегодня: 15/20\n🕐 Лимит обновится завтра в 00:00"

# FREE  
"📊 Остаток писем в этом месяце: 1/3\n🕐 Лимит обновится 1 декабря в 00:00"
```

#### 5.2 Команды для пользователей
- [ ] `/limits` - показать текущие лимиты и время сброса
- [ ] `/subscription` - информация о подписке
- [ ] Автоматические уведомления о сбросе лимитов

---

## 🔧 ТЕХНИЧЕСКАЯ РЕАЛИЗАЦИЯ

### Новый класс CalendarSubscriptionService

```python
import pytz
from datetime import datetime, date, timedelta

class CalendarSubscriptionService(SubscriptionService):
    """Календарная система подписок v8.0"""
    
    def __init__(self):
        super().__init__()
        self.moscow_tz = pytz.timezone('Europe/Moscow')
    
    def _get_moscow_date(self) -> date:
        """Получить текущую дату в Москве"""
        return datetime.now(self.moscow_tz).date()
    
    def _should_reset_calendar_limits(self, subscription: dict, moscow_date: date) -> bool:
        """Определить нужен ли календарный сброс лимитов"""
        last_reset = subscription.get('last_reset_date')
        if not last_reset:
            return True
            
        last_reset_date = datetime.fromisoformat(last_reset).date()
        plan_type = subscription['plan_type']
        
        if plan_type == 'premium':
            # PREMIUM: сброс каждый день
            return moscow_date > last_reset_date
        else:
            # FREE: сброс первого числа месяца
            return (moscow_date.year > last_reset_date.year or 
                   moscow_date.month > last_reset_date.month)
    
    async def _reset_calendar_limits(self, user_id: int, plan_type: str, moscow_date: date):
        """Календарный сброс лимитов"""
        next_reset = self._get_next_reset_date(plan_type, moscow_date)
        
        await self.supabase.table('subscriptions').update({
            'letters_used': 0,
            'last_reset_date': moscow_date.isoformat(),
            'period_start': moscow_date.isoformat(), 
            'period_end': next_reset.isoformat(),
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).execute()
        
        logger.info(f"📅 Calendar reset for user {user_id}: {plan_type} -> next reset {next_reset}")
```

### Фоновая задача сброса

```python
async def periodic_limits_reset():
    """Фоновая задача для сброса лимитов по расписанию"""
    while True:
        try:
            moscow_time = datetime.now(pytz.timezone('Europe/Moscow'))
            
            # Проверяем каждые 5 минут в районе полуночи
            if moscow_time.hour == 0 and moscow_time.minute < 10:
                await reset_all_calendar_limits()
                
            await asyncio.sleep(300)  # 5 минут
        except Exception as e:
            logger.error(f"Error in periodic reset: {e}")
            await asyncio.sleep(300)

async def reset_all_calendar_limits():
    """Сбросить лимиты всех пользователей по календарю"""
    service = CalendarSubscriptionService()
    moscow_date = service._get_moscow_date()
    
    # Получить всех пользователей для сброса
    subscriptions = await service.get_subscriptions_for_reset(moscow_date)
    
    for sub in subscriptions:
        await service._reset_calendar_limits(sub['user_id'], sub['plan_type'], moscow_date)
```

---

## 🚀 ПЛАН РЕЛИЗА

### Приоритет 1: HOTFIX (СЕГОДНЯ)
1. ✅ Исправить подписку `Stanislav` через SQL
2. ✅ Добавить временную функцию принудительного сброса
3. ✅ Протестировать на одном пользователе

### Приоритет 2: ОСНОВНОЙ РЕЛИЗ (2-3 дня)
1. ✅ Реализовать календарную логику
2. ✅ Добавить фоновую задачу
3. ✅ Мигрировать все подписки
4. ✅ Протестировать автоматический сброс

### Приоритет 3: УЛУЧШЕНИЯ UX (1 неделя)
1. ✅ Добавить команды `/limits` и `/subscription`
2. ✅ Улучшить сообщения о лимитах
3. ✅ Добавить уведомления о сбросе

---

## ✅ КРИТЕРИИ ГОТОВНОСТИ

### Функциональные требования:
- [ ] PREMIUM лимиты сбрасываются каждый день в 00:00 МСК
- [ ] FREE лимиты сбрасываются 1 числа месяца в 00:00 МСК  
- [ ] Фоновый сброс работает независимо от активности пользователей
- [ ] Пользователи видят точное время следующего сброса
- [ ] Система работает в московском часовом поясе

### Технические требования:
- [ ] Покрытие unit-тестами 90%+
- [ ] Логирование всех операций с лимитами
- [ ] Graceful degradation при ошибках БД
- [ ] Мониторинг успешности фоновых задач

### Безопасность:
- [ ] Невозможно обойти лимиты сменой часового пояса
- [ ] Защита от race conditions при сбросе
- [ ] Валидация всех временных данных

---

## 🔍 ТЕСТИРОВАНИЕ

### Модульные тесты:
```python
async def test_premium_daily_reset():
    """Тест сброса PREMIUM лимитов каждый день"""
    service = CalendarSubscriptionService()
    
    # Создать подписку вчера
    yesterday = service._get_moscow_date() - timedelta(days=1)
    subscription = create_test_subscription('premium', yesterday)
    
    # Проверить что сброс нужен
    should_reset = service._should_reset_calendar_limits(subscription, service._get_moscow_date())
    assert should_reset == True

async def test_free_monthly_reset():
    """Тест сброса FREE лимитов раз в месяц"""
    # Аналогично для месячного сброса
    pass
```

### Интеграционные тесты:
- [ ] Тест полного цикла: создание подписки → использование лимитов → автосброс
- [ ] Тест работы в разных часовых поясах
- [ ] Тест нагрузки фоновой задачи сброса

---

## 📊 МОНИТОРИНГ

### Метрики для отслеживания:
- Количество успешных сбросов лимитов в день
- Время выполнения операций сброса
- Количество ошибок при сбросе
- Распределение использования лимитов по дням

### Алерты:
- Фоновая задача сброса не выполнилась
- Более 5% ошибок при сбросе лимитов
- Аномальное использование лимитов

---

## 🎉 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После внедрения календарной системы:

1. **Пользователи получают предсказуемые лимиты** - всегда знают когда обновится доступ
2. **Справедливое распределение** - все PREMIUM пользователи получают лимиты одновременно в полночь
3. **Надежность системы** - сброс происходит автоматически даже без активности пользователей
4. **Простота администрирования** - календарная логика интуитивно понятна для поддержки

---

## 🚨 РИСКИ И МИТИГАЦИЯ

### Риск: Сбой фоновой задачи сброса
**Митигация**: Резервный сброс при первом обращении пользователя + мониторинг

### Риск: Проблемы с часовыми поясами
**Митигация**: Использование только московского времени + тесты в разных ТЗ

### Риск: Race conditions при массовом сбросе
**Митигация**: Транзакции БД + блокировки + очередь задач

---

## 📞 КОНТАКТЫ

**Ответственный за релиз**: Разработчик  
**Тестирование**: Разработчик  
**DevOps**: Разработчик  

**Дата начала**: Сегодня  
**Планируемый релиз**: 3 дня  
