# 🚀 БЫСТРЫЕ ПРОМПТЫ ДЛЯ CURSOR

## 📋 Для копирования в чаты

### 🔍 **Анализ кода (Database Performance)**
```
Проанализируй [файл] на предмет:
1. N+1 query problems
2. Дублирующиеся запросы к базе данных
3. Возможности для batching операций
4. Неоптимальные async/await

Покажи конкретные строки с проблемами.
НЕ меняй функциональность, только производительность.
НЕ трогай AI промпты и error handling.
```

### 📊 **Database Analysis & Migration**
```
Проанализируй [файл] на предмет изменений БД:
1. Какие таблицы будут затронуты
2. Нужны ли новые поля/индексы
3. Совместимость с существующими данными
4. План миграции и отката

ОБЯЗАТЕЛЬНО создай migrate_[название].sql файл с:
- ALTER TABLE командами
- CREATE INDEX для новых полей
- DEFAULT значениями
- Rollback командами в комментариях

НЕ меняй supabase_schema.sql напрямую!
```

### 🛡️ **Security Audit**
```
Проверь [файл] на безопасность:
1. PII в логах (ФИО, телефоны, email из resume_text)
2. Отсутствие input validation
3. SQL injection возможности
4. Rate limiting gaps

Покажи проблемы и предложи исправления.
Сохрани всю существующую функциональность.
```

### 🤖 **AI Services Review**
```
Отревьюй [файл] для AI сервисов:
1. Fallback механизмы OpenAI ↔ Claude сохранены?
2. Error handling не потерян?
3. Timeout настройки корректны?
4. Token usage логируется?

КРИТИЧНО: НЕ меняй UNIFIED_ANALYSIS_PROMPT без approval.
Объясни каждое предлагаемое изменение.
```

### ⚡ **Performance Optimization**
```
Оптимизируй [файл] для производительности:
1. Убери дублирующиеся database queries
2. Добавь batching для analytics events
3. Проверь connection pooling
4. Оптимизируй memory usage

Цель: выдержать 1000+ concurrent users.
НЕ ломай существующую функциональность.
```

### 📱 **Telegram Bot Issues**
```
Исправь [проблема] в [файл]:
1. ConversationHandler state management
2. Callback query error handling
3. Keyboard markup issues
4. Message template problems

Сохрани всю логику бота.
Используй utils/keyboards.py для клавиатур.
```

---

## 🎯 Промпты для специфических задач

### Database Migration
```
Создай миграцию для [изменение]:
1. Новый файл migrate_[описание].sql в корне проекта
2. Сохрани все RLS политики
3. НЕ ломай существующие данные
4. **ОБЯЗАТЕЛЬНО:** Rollback команды в комментариях
5. **ОБЯЗАТЕЛЬНО:** Индексы для новых полей
6. **ОБЯЗАТЕЛЬНО:** DEFAULT значения для новых полей
7. **ОБЯЗАТЕЛЬНО:** Тестирование на dev копии
8. **ОБЯЗАТЕЛЬНО:** План отката каждого ALTER TABLE

НЕ меняй supabase_schema.sql напрямую!
Пример структуры миграции:
-- FORWARD MIGRATION
ALTER TABLE user_sessions ADD COLUMN new_field VARCHAR(50) DEFAULT 'default_value';
CREATE INDEX idx_user_sessions_new_field ON user_sessions(new_field);

-- ROLLBACK COMMANDS (в комментариях)
-- DROP INDEX idx_user_sessions_new_field;
-- ALTER TABLE user_sessions DROP COLUMN new_field;
```

### AI Prompt Testing
```
Создай A/B тест для промпта:
1. Версия A: текущий промпт
2. Версия B: предложенные изменения
3. Метрики для сравнения
4. Test framework

НЕ меняй production промпт без тестирования!
```

### Load Testing
```
Создай load test для [компонент]:
1. Сценарий для 100+ concurrent users
2. Тест memory usage
3. Database connection pooling test
4. Metrics collection

Цель: подготовка к 1000+ пользователей.
```

---

## 💡 Как использовать:

1. **Скопируй нужный промпт** из этого файла
2. **Замени [переменные]** на конкретные значения  
3. **Вставь в Cursor чат** - правила из .cursor/rules.json подключатся автоматически
4. **Проверь результат** на соответствие ограничениям

---

## ⚠️ Помни всегда:

- `.cursor/rules.json` подключается автоматически
- Эти промпты - дополнительные уточнения
- Всегда проверяй что Cursor не нарушил критичные правила
- При сомнениях - лучше спроси дополнительно

**Цель:** Сделать работу с Cursor максимально эффективной и безопасной для AI Telegram бота. 