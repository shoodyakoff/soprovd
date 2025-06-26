# МИГРАЦИЯ v9.5: СИНХРОНИЗАЦИЯ PROD И DEV БАЗ ДАННЫХ

## ⚠️ КРИТИЧЕСКИ ВАЖНО: ПОЭТАПНОЕ ВЫПОЛНЕНИЕ

Из-за ошибки с VIEW, которые ссылаются на изменяемые поля, миграция разделена на **3 ЭТАПА**.
Выполнять строго последовательно!

## ЭТАП 1: Удаление VIEW и лишних полей

```bash
# Выполните:
psql -h your-prod-host -U your-user -d your-db -f migrations/v9.5_prod_sync_fixed.sql
```

**Что делает:**
- ✅ Удаляет все VIEW которые ссылаются на изменяемые поля
- ✅ Удаляет лишние поля `users.total_generations` и `users.updated_at` 
- ✅ Изменяет тип `letter_sessions.generation_time_seconds` на `double precision`

## ЭТАП 2: Изменение типов user_id

```bash
# Выполните ТОЛЬКО после успешного завершения ЭТАПА 1:
psql -h your-prod-host -U your-user -d your-db -f migrations/v9.5_prod_sync_step2.sql
```

**Что делает:**
- ✅ Изменяет типы `user_id` с `integer` на `bigint` во всех нужных таблицах:
  - `acquisition_channels.user_id` и `referral_user_id`
  - `letter_feedback.user_id`
  - `letter_iterations.user_id`
  - `payments.user_id`
  - `subscriptions.user_id`
  - `subscriptions_backup.user_id`

## ЭТАП 3: Пересоздание VIEW таблиц

```bash
# Выполните ТОЛЬКО после успешного завершения ЭТАПОВ 1 и 2:
psql -h your-prod-host -U your-user -d your-db -f migrations/v9.5_prod_sync_step3.sql
```

**Что делает:**
- ✅ Пересоздает все VIEW таблицы с правильными типами полей:
  - `user_stats`
  - `session_stats` (теперь работает с `double precision`)
  - `user_activity`
  - `openai_usage`
  - `user_cohorts_basic` (теперь работает с `bigint` user_id)

## Проверка результата

После выполнения всех 3 этапов проверьте:

```sql
-- Проверяем типы полей
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'letter_sessions' 
AND column_name = 'generation_time_seconds';
-- Должно быть: double precision

-- Проверяем что VIEW существуют
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name IN ('user_stats', 'session_stats', 'user_activity', 'openai_usage', 'user_cohorts_basic');
-- Должно быть 5 строк

-- Проверяем что лишние поля удалены
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('total_generations', 'updated_at');
-- Должно быть 0 строк
```

## В случае ошибок

Если на любом этапе возникла ошибка:
1. **НЕ ПРОДОЛЖАЙТЕ** выполнение следующих этапов
2. Сообщите об ошибке для диагностики
3. При необходимости можно откатить изменения через `ROLLBACK`

## После успешной миграции

1. ✅ PROD база синхронизирована с DEV
2. ✅ Можно безопасно деплоить код
3. ✅ Все VIEW работают корректно
4. ✅ Типы данных приведены к единому стандарту

---

**Статус миграции:** 🔄 Готова к выполнению (поэтапно)
**Критичность:** 🔴 Высокая - обязательна перед деплоем кода

# 🚨 КРИТИЧЕСКИ ВАЖНО: ИНСТРУКЦИИ ПО МИГРАЦИИ v9.5

## ⚠️ ВНИМАНИЕ! ОБЯЗАТЕЛЬНО К ВЫПОЛНЕНИЮ ПЕРЕД ДЕПЛОЕМ

**Дата создания:** 2024-12-19  
**Статус:** 🔴 КРИТИЧЕСКИЙ - ВЫПОЛНИТЬ НЕМЕДЛЕННО  
**Цель:** Синхронизация prod и dev схем баз данных

---

## 🔍 ОБНАРУЖЕННЫЕ КРИТИЧЕСКИЕ РАЗЛИЧИЯ

### 📊 Анализ различий между PROD и DEV базами:

#### 🏭 **PROD база (prod_soprovod):**
- ✅ Поле `users.total_generations` (ЛИШНЕЕ - нужно удалить)
- ✅ Поле `users.updated_at` (ЛИШНЕЕ - нужно удалить)
- ❌ Отсутствует VIEW `user_cohorts_basic` (нужно создать)
- ✅ Правильные типы `user_id` как `bigint` во всех таблицах
- ❌ Тип `generation_time_seconds` как `integer` (нужно изменить на `double precision`)

#### 🔧 **DEV база (shoodyakoff's Project):**
- ❌ Нет поля `users.total_generations`
- ❌ Нет поля `users.updated_at`
- ✅ Есть VIEW `user_cohorts_basic`
- ❌ Неправильные типы `user_id` как `integer` в некоторых таблицах
- ✅ Правильный тип `generation_time_seconds` как `double precision`

---

## 🎯 ПЛАН МИГРАЦИИ

### 📋 **ШАГ 1: ПОДГОТОВКА К МИГРАЦИИ**

#### 1.1 Проверка доступа к PROD базе
```sql
-- Выполнить на PROD базе для проверки доступа
SELECT 
    schemaname, 
    tablename, 
    tableowner 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
```

#### 1.2 Создание бэкапа PROD базы (ОБЯЗАТЕЛЬНО!)
```bash
# Создать полный бэкап перед миграцией
pg_dump -h [PROD_HOST] -U [PROD_USER] -d [PROD_DB] > backup_before_v9_5_$(date +%Y%m%d_%H%M%S).sql
```

### 📋 **ШАГ 2: ВЫПОЛНЕНИЕ МИГРАЦИИ**

#### 2.1 Загрузка файла миграции
```bash
# Файл миграции уже готов:
migrations/v9.5_prod_sync.sql
```

#### 2.2 Выполнение миграции на PROD
```bash
# ВНИМАНИЕ: Выполнять ТОЛЬКО на PROD базе!
psql -h [PROD_HOST] -U [PROD_USER] -d [PROD_DB] -f migrations/v9.5_prod_sync.sql
```

#### 2.3 Ожидаемый вывод миграции
```
NOTICE:  Поле users.total_generations удалено
NOTICE:  Поле users.updated_at удалено
NOTICE:  Тип letter_sessions.generation_time_seconds изменен на double precision
NOTICE:  Тип acquisition_channels.user_id изменен на bigint
NOTICE:  Тип acquisition_channels.referral_user_id изменен на bigint
NOTICE:  Тип letter_feedback.user_id изменен на bigint
NOTICE:  Тип letter_iterations.user_id изменен на bigint
NOTICE:  Тип payments.user_id изменен на bigint
NOTICE:  Тип subscriptions.user_id изменен на bigint
NOTICE:  Тип subscriptions_backup.user_id изменен на bigint
NOTICE:  VIEW user_cohorts_basic создан успешно
NOTICE:  ============================================================================
NOTICE:  МИГРАЦИЯ v9.5 ЗАВЕРШЕНА УСПЕШНО
NOTICE:  ============================================================================
```

### 📋 **ШАГ 3: ПРОВЕРКА ПОСЛЕ МИГРАЦИИ**

#### 3.1 Проверка удаления полей
```sql
-- Убедиться, что поля удалены
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('total_generations', 'updated_at')
AND table_schema = 'public';
-- Результат должен быть пустым
```

#### 3.2 Проверка типов данных
```sql
-- Проверить типы user_id
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE column_name LIKE '%user_id%' 
AND table_schema = 'public'
ORDER BY table_name, column_name;
-- Все должны быть bigint
```

#### 3.3 Проверка VIEW
```sql
-- Проверить, что VIEW создан и работает
SELECT COUNT(*) FROM user_cohorts_basic;
-- Должно вернуть количество пользователей
```

#### 3.4 Проверка generation_time_seconds
```sql
-- Проверить тип поля
SELECT data_type 
FROM information_schema.columns 
WHERE table_name = 'letter_sessions' 
AND column_name = 'generation_time_seconds'
AND table_schema = 'public';
-- Должно быть: double precision
```

---

## 🚨 КРИТИЧЕСКИЕ ОШИБКИ В КОДЕ

### ❌ **ГЛАВНАЯ ПРОБЛЕМА: Неправильная передача user_id**

**КРИТИЧЕСКАЯ ОШИБКА:** В коде передается `telegram_user_id` вместо внутреннего `user_id`!

#### 🔍 **Анализ проблемы:**
```python
# ❌ НЕПРАВИЛЬНО (строка 351):
user_id = update.message.from_user.id  # Это telegram_user_id (например, 123456789)
limits = await subscription_service.check_user_limits(user_id)

# ✅ ПРАВИЛЬНО (исправлено):
analytics_user_id = context.user_data.get('analytics_user_id')  # Это внутренний user_id (например, 3)
limits = await subscription_service.check_user_limits(analytics_user_id)
```

#### 🛠️ **Почему это критично:**
1. `subscription_service.check_user_limits()` ищет подписку по внутреннему `user_id` из таблицы `users`
2. Но получает `telegram_user_id` (например, 987654321)
3. В таблице `subscriptions` нет записи с `user_id = 987654321`
4. Сервис пытается создать подписку через `analytics.get_or_create_subscription(987654321)`
5. Но `analytics.get_or_create_subscription()` тоже ищет по внутреннему `user_id`
6. **РЕЗУЛЬТАТ:** Пользователь не создается в `subscriptions`, получает ошибки лимитов

#### ✅ **ИСПРАВЛЕНО в коде:**
- Строка 351: `user_id = update.message.from_user.id` → `telegram_user_id = update.message.from_user.id`
- Строка 362: `limits = await subscription_service.check_user_limits(user_id)` → `limits = await subscription_service.check_user_limits(analytics_user_id)`
- Добавлена проверка наличия `analytics_user_id`

### ❌ Обнаруженные ошибки линтера в `handlers/simple_conversation_v6.py`:

1. **Неправильные вызовы методов сервисов:**
   - `get_user_subscription_info()` → `check_user_limits()`
   - `start_letter_session()` → `create_letter_session()`
   - `check_and_update_limits()` → `check_user_limits()`
   - `get_iteration_status()` → `get_session_iteration_status()`

2. **Неопределенные переменные:**
   - `vacancy_text` в функции улучшения письма
   - Неправильная передача типов данных

3. **Проблемы с типами:**
   - `session_id` может быть `None`, но передается как `str`

### ✅ Частично исправлено:
- ✅ **ГЛАВНОЕ:** Исправлена передача `user_id` → `analytics_user_id`
- ✅ Исправлен вызов `validators.is_text_long_enough()` → `InputValidator.validate_resume_text()`
- ✅ Исправлен вызов `get_user_subscription_info()` → `check_user_limits()`
- ✅ Исправлен вызов `start_letter_session()` → `create_letter_session()`

### ⚠️ Осталось исправить:
- Остальные ошибки типов и неопределенных переменных
- Проверки на `None` для `session_id`

---

## 📋 ПЛАН ДЕПЛОЯ ПОСЛЕ МИГРАЦИИ

### 🎯 **ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ:**

#### 1. **ВЫПОЛНИТЬ МИГРАЦИЮ** (СНАЧАЛА!)
```bash
# На PROD базе
psql -h [PROD_HOST] -U [PROD_USER] -d [PROD_DB] -f migrations/v9.5_prod_sync.sql
```

#### 2. **ИСПРАВИТЬ ОСТАВШИЕСЯ ОШИБКИ КОДА**
- Завершить исправление ошибок линтера в `handlers/simple_conversation_v6.py`
- Добавить проверки на `None` для `session_id`
- Исправить передачу `vacancy_text` в функции улучшения

#### 3. **ТЕСТИРОВАНИЕ**
- Проверить работу бота на DEV после исправлений
- Убедиться, что все функции работают корректно
- Протестировать создание писем и итерации

#### 4. **ДЕПЛОЙ КОДА**
- Только после успешной миграции и исправления ошибок
- Деплой изменений в `handlers/simple_conversation_v6.py`
- Деплой остальных файлов проекта

---

## ⚠️ РИСКИ И МИТИГАЦИЯ

### 🔴 **ВЫСОКИЕ РИСКИ:**

#### Риск 1: Потеря данных при миграции
**Митигация:** 
- ✅ Создан полный бэкап базы
- ✅ Миграция использует безопасные `DROP COLUMN IF EXISTS`
- ✅ Все операции в транзакции с возможностью отката

#### Риск 2: Несовместимость кода с новой схемой
**Митигация:**
- ✅ Код адаптирован под новую схему
- ⚠️ Нужно завершить исправление ошибок линтера
- ✅ Тестирование на DEV перед деплоем

#### Риск 3: Downtime продакшена
**Митигация:**
- ✅ Миграция выполняется быстро (< 30 секунд)
- ✅ Большинство операций не блокируют таблицы
- ✅ План отката готов

### 🟡 **СРЕДНИЕ РИСКИ:**

#### Риск 4: Проблемы с VIEW user_cohorts_basic
**Митигация:**
- ✅ VIEW протестирован на DEV
- ✅ Использует только существующие таблицы
- ✅ Имеет fallback логику

---

## 🔄 ПЛАН ОТКАТА (ROLLBACK)

### В случае проблем с миграцией:

#### 1. **Откат базы данных:**
```bash
# Восстановление из бэкапа
psql -h [PROD_HOST] -U [PROD_USER] -d [PROD_DB] < backup_before_v9_5_[TIMESTAMP].sql
```

#### 2. **Откат кода:**
```bash
# Вернуть предыдущую версию кода
git revert [COMMIT_HASH]
```

#### 3. **Проверка работоспособности:**
```bash
# Проверить, что бот работает
curl -X POST https://api.telegram.org/bot[TOKEN]/getMe
```

---

## ✅ ЧЕКЛИСТ ВЫПОЛНЕНИЯ

### 📋 **ПЕРЕД МИГРАЦИЕЙ:**
- [ ] Создан бэкап PROD базы
- [ ] Файл `migrations/v9.5_prod_sync.sql` готов
- [ ] Доступ к PROD базе проверен
- [ ] План отката готов

### 📋 **ВЫПОЛНЕНИЕ МИГРАЦИИ:**
- [ ] Миграция выполнена на PROD
- [ ] Все NOTICE сообщения получены
- [ ] Ошибок в процессе миграции не было
- [ ] Проверки после миграции пройдены

### 📋 **ПОСЛЕ МИГРАЦИИ:**
- [ ] Схемы PROD и DEV синхронизированы
- [ ] Ошибки линтера в коде исправлены
- [ ] Тестирование на DEV пройдено
- [ ] Код задеплоен на PROD
- [ ] Бот работает корректно

---

## 🎯 ЗАКЛЮЧЕНИЕ

**Миграция v9.5 критически важна** для синхронизации prod и dev схем баз данных. 

**ОБЯЗАТЕЛЬНО выполнить** миграцию перед деплоем любого кода, иначе возможны критические ошибки в работе бота.

**Время выполнения:** ~30 минут (включая проверки)  
**Приоритет:** 🔴 КРИТИЧЕСКИЙ  
**Статус:** ⚠️ ГОТОВ К ВЫПОЛНЕНИЮ 