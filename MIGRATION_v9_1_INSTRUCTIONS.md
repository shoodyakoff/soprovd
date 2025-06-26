# 🔄 ИНСТРУКЦИЯ ПО МИГРАЦИИ v9.1 + v9.4

## 📋 ЧТО ДЕЛАЕТ МИГРАЦИЯ

### v9.1 - Legal Documents
- ✅ Добавляет поля согласия в таблицу `users`
- ✅ **Проставляет согласие = TRUE всем существующим пользователям** (implied consent)
- ✅ Создает индексы для быстрого поиска по согласию
- ✅ Добавляет юридические документы и команды `/privacy`, `/terms`

### v9.4 - Bugfix Subscription Unlimited  
- ✅ **Исправляет критический баг:** новые пользователи получали Unlimited вместо Free
- ✅ Удаляет метод `_unlimited_access()` 
- ✅ Все новые пользователи получают Free подписку с 3 письмами

---

## 🚀 КАК ЗАПУСТИТЬ МИГРАЦИЮ

### Вариант 1: Автоматический скрипт (рекомендуется)
```bash
# Убедитесь что настроены переменные окружения
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"

# Запускаем скрипт миграции
python run_migration_v9_1.py
```

### Вариант 2: Ручное выполнение SQL
```bash
# Загружаем SQL файл в Supabase Dashboard → SQL Editor
# Выполняем migrate_v9_1_add_consent_fields.sql
```

### Вариант 3: Через Python код
```python
from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Выполняем команды из migrate_v9_1_add_consent_fields.sql
with open('migrate_v9_1_add_consent_fields.sql', 'r') as f:
    sql_commands = f.read()
    
# Выполняем через Supabase
```

---

## ⚠️ ВАЖНЫЕ МОМЕНТЫ

### Для существующих пользователей
- 🎯 **Автоматически проставляется согласие = TRUE**
- 📅 **Логика:** если пользователь уже генерировал письма, значит он фактически согласился
- 🔒 **Версия согласия:** v1.0 (для отслеживания изменений политики)
- 📧 **Маркетинговое согласие:** FALSE (отдельно от основного согласия)

### Новые поля в users
```sql
consent_given BOOLEAN DEFAULT NULL     -- TRUE/FALSE/NULL
consent_timestamp TIMESTAMP           -- когда дано согласие  
consent_version VARCHAR(10)           -- версия политики
marketing_consent BOOLEAN DEFAULT FALSE -- согласие на рекламу
```

### Безопасность
- ✅ **Откатываемо:** есть команды для отката изменений
- ✅ **Без потери данных:** все добавления, никаких удалений
- ✅ **С проверкой:** `IF NOT EXISTS` для безопасности

---

## 🧪 ПРОВЕРКА ПОСЛЕ МИГРАЦИИ

### 1. Проверить поля в БД
```sql
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN ('consent_given', 'consent_timestamp', 'consent_version', 'marketing_consent');
```

### 2. Проверить количество пользователей с согласием
```sql
SELECT 
  consent_given,
  consent_version,
  COUNT(*) as user_count
FROM users 
WHERE id IS NOT NULL
GROUP BY consent_given, consent_version;
```

### 3. Проверить новых пользователей в боте
- Создать нового пользователя → должен получить подписку "Бесплатная 3/3"
- НЕ должно быть "Unlimited 999999/999999"

### 4. Проверить команды
- `/support` → должно показать @shoodyakoff
- `/privacy` → должно показать политику конфиденциальности
- `/terms` → должно показать пользовательское соглашение

---

## 🔧 ОТКАТ (если нужен)

### Быстрый откат изменений
```sql
-- Удаляем добавленные поля (ОСТОРОЖНО!)
DROP INDEX IF EXISTS idx_users_consent_version;
DROP INDEX IF EXISTS idx_users_consent;
ALTER TABLE users DROP COLUMN IF EXISTS marketing_consent;
ALTER TABLE users DROP COLUMN IF EXISTS consent_version;
ALTER TABLE users DROP COLUMN IF EXISTS consent_timestamp;
ALTER TABLE users DROP COLUMN IF EXISTS consent_given;
```

### Откат кода
```bash
# Откатить до предыдущего коммита
git revert HEAD

# Или жесткий откат (ОСТОРОЖНО!)
git reset --hard HEAD~1
```

---

## 📈 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### ДО миграции
```
❌ Новый пользователь:
   Подписка: Unlimited  
   🟢 Писем осталось: 999999/999999

❌ /support → старый текст с багами
❌ НЕТ юридических документов
```

### ПОСЛЕ миграции
```
✅ Новый пользователь:
   Подписка: Бесплатная
   🟢 Писем осталось: 3/3

✅ /support → @shoodyakoff
✅ /privacy → политика конфиденциальности
✅ /terms → пользовательское соглашение
✅ Существующие пользователи: согласие = TRUE
```

---

## 🎯 ГОТОВНОСТЬ К ПРОДАКШЕНУ

- ✅ **v9.1 Legal Documents** - ПОЛНОСТЬЮ ГОТОВО
- ✅ **v9.4 Bugfix Subscriptions** - ПОЛНОСТЬЮ ГОТОВО  
- ✅ **Миграция БД** - ГОТОВА К ЗАПУСКУ
- ✅ **Инструкции** - ГОТОВЫ
- ✅ **Откат** - ГОТОВ

**🚀 МОЖНО ДЕПЛОИТЬ НА ПРОДАКШЕН!** 

# 🔧 ИНСТРУКЦИЯ: Миграция v9.1 - Поля согласия

## ⚠️ КРИТИЧЕСКИ ВАЖНО
**Без этой миграции бот не будет работать!** 
Ошибка: `column users.consent_given does not exist`

## 📋 **Шаги выполнения:**

### 1. **Откройте Supabase Dashboard**
- Перейдите в проект: https://supabase.com/dashboard
- Выберите ваш проект

### 2. **Откройте SQL Editor**
- В левом меню выберите "SQL Editor"
- Нажмите "New query"

### 3. **Скопируйте и выполните миграцию**
```sql
-- МИГРАЦИЯ v9.1: Добавление полей согласия для ФЗ-152
-- Выполнить в Supabase SQL Editor

-- 1. Добавляем поля согласия
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_given BOOLEAN DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_timestamp TIMESTAMP DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_version VARCHAR(10) DEFAULT 'v1.0';
ALTER TABLE users ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN DEFAULT FALSE;

-- 2. Проставляем согласие существующим пользователям (implied consent)
UPDATE users 
SET consent_given = TRUE, 
    consent_timestamp = NOW(), 
    consent_version = 'v1.0',
    marketing_consent = FALSE
WHERE id IS NOT NULL 
  AND consent_given IS NULL;

-- 3. Создаем индексы
CREATE INDEX IF NOT EXISTS idx_users_consent ON users(consent_given, consent_timestamp);

-- 4. Проверка результата
SELECT 
  consent_given,
  consent_version,
  COUNT(*) as user_count
FROM users 
WHERE id IS NOT NULL
GROUP BY consent_given, consent_version;
```

### 4. **Нажмите "Run"**
- Выполните миграцию
- Проверьте что нет ошибок

### 5. **Проверьте результат**
Должны увидеть что-то вроде:
```
consent_given | consent_version | user_count
true          | v1.0           | 5
```

## ✅ **После выполнения миграции:**
- Бот снова заработает корректно
- Новые пользователи будут видеть текст согласия
- Существующие пользователи получат статус согласия автоматически

## 🚨 **Если что-то пошло не так:**
```sql
-- Откат миграции (только в крайнем случае!)
DROP INDEX IF EXISTS idx_users_consent;
ALTER TABLE users DROP COLUMN IF EXISTS marketing_consent;
ALTER TABLE users DROP COLUMN IF EXISTS consent_version;
ALTER TABLE users DROP COLUMN IF EXISTS consent_timestamp;
ALTER TABLE users DROP COLUMN IF EXISTS consent_given;
``` 