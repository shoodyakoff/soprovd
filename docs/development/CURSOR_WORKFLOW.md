# 🤖 CURSOR WORKFLOW ДЛЯ AI TELEGRAM БОТА

## 🎯 Принципы работы с Cursor для tg_soprovod

### ⚠️ КРИТИЧЕСКИ ВАЖНО
- **AI Промпты = код** - версионируются и не меняются без тестов
- **База данных = продакшн** - любые изменения через миграции  
- **Безопасность = приоритет** - PII не логируется
- **Производительность = масштабируемость** - каждый запрос должен выдержать 1000+ пользователей

---

## 📋 Структура задач

### Шаблон задачи для AI бота:
```markdown
# 🎯 [v7.3] Оптимизация database queries

## Контекст  
**Проблема:** Analytics делает 15-20 запросов на письмо  
**Цель:** Сократить до 3-5 запросов через batching  
**Приоритет:** CRITICAL (блокирует масштабирование)

## Затронутые компоненты
- [ ] `services/analytics_service.py` - batch events
- [ ] `models/analytics_models.py` - добавить batch methods  
- [ ] `utils/database.py` - connection pooling

## Ограничения
- НЕ ломать существующую аналитику
- НЕ менять структуру таблиц user_events
- Сохранить все event_types
- Backward compatibility

## AI Services
- НЕ трогать AI промпты
- НЕ менять fallback логику OpenAI ↔ Claude
- НЕ убирать error handling

## Definition of Done
- [ ] Load test: 1000 concurrent users без connection errors
- [ ] Metrics: database requests сократились на 80%
- [ ] Tests: все существующие аналитические тесты проходят
- [ ] Monitoring: новые метрики для batch performance
```

---

## 🚀 Промпты для Cursor

### 🔍 Анализ производительности
```
Проанализируй services/analytics_service.py на предмет:
1. Дублирующихся запросов к базе данных
2. N+1 query problems
3. Возможности для batching операций
4. Connection pooling issues

Покажи конкретные строки кода с проблемами и предложи оптимизацию.
НЕ меняй функциональность, только производительность.
```

### 🛠 Рефакторинг с безопасностью
```
Отрефактори handlers/simple_conversation_v6.py чтобы:
1. Добавить rate limiting на user_id (5 запросов/минуту)
2. Убрать PII из всех logger.info() вызовов
3. Добавить input validation для текстов
4. Сохранить всю существующую логику ConversationHandler

Покаж diff и объясни каждое изменение.
```

### 🤖 AI Services optimization
```
Оптимизируй services/ai_factory.py для:
1. Connection pooling к OpenAI и Claude APIs
2. Retry logic с exponential backoff
3. Caching одинаковых промптов на 1 час
4. Circuit breaker pattern

НЕ ТРОГАЙ промпты в ai_service.py - только инфраструктурный код.
Сохрани все fallback механизмы.
```

### 📊 Database optimization
```
Проанализируй models/analytics_models.py и предложи:
1. Batch insert методы для user_events
2. Оптимизацию индексов для частых queries
3. Connection pooling configuration
4. Prepared statements для повторяющихся запросов

Покаж конкретные SQL запросы ДО и ПОСЛЕ оптимизации.
```

---

## ⚡ Workflow по этапам

### 1️⃣ АНАЛИЗ (перед началом)
```bash
# Всегда начинай с анализа
"Прочитай файл [filename] и дай краткое резюме:
- Что делает
- Какие зависимости  
- Потенциальные проблемы
- Связи с другими компонентами"
```

### 2️⃣ ПЛАНИРОВАНИЕ
```bash
# Планируй изменения
"На основе задачи создай план изменений:
1. Какие файлы менять и почему
2. Какие риски и как их минимизировать  
3. Как тестировать изменения
4. Какие метрики отследить"
```

### 3️⃣ РЕАЛИЗАЦИЯ  
```bash
# Пошаговая реализация
"Внеси изменения в [filename]:
- Сначала покажи diff
- Объясни каждое изменение
- Укажи на потенциальные проблемы
- Предложи как протестировать"
```

### 4️⃣ РЕВЬЮ
```bash
# Финальная проверка
"Проревьюй изменения в [filename]:
- Соответствуют ли требованиям?
- Есть ли проблемы безопасности?
- Не сломается ли при нагрузке?
- Какие тесты добавить?"
```

---

## 🚨 Красные флаги - СТОП сигналы

### ❌ НЕ позволяй Cursor делать:
- Менять `UNIFIED_ANALYSIS_PROMPT` без explicit approval
- Удалять error handling в AI services
- Изменять supabase_schema.sql напрямую
- Логировать resume_text или vacancy_text
- Убирать rate limiting или validation
- Менять database connection без тестов

### ✅ Проверяй ВСЕГДА:
- Async/await используется правильно
- Error handling не потерян
- Logging не содержит PII
- Tests покрывают новую функциональность
- Backward compatibility сохранена

---

## 📝 Коммиты для AI проекта

### Шаблоны коммитов:
```bash
# Производительность
perf: optimize analytics batching - reduce DB queries by 80%

# AI улучшения  
ai: add response caching for duplicate prompts - save $200/month

# Безопасность
security: add rate limiting and PII sanitization in logs

# Фичи
feat: implement user subscription limits with Redis cache

# Исправления
fix: handle Claude API timeout with proper fallback to GPT-4
```

---

## 🔧 Настройка environment

### Локальная разработка:
```bash
# Всегда используй dev environment
cp .env.example .env.dev
python run_dev.py

# НЕ тестируй на production данных
# НЕ коммить .env файлы
# НЕ использовать production API keys
```

### Тестирование AI изменений:
```bash
# Создай test промпты
"Создай тестовые данные для проверки AI генерации:
- 5 примеров вакансий разной сложности
- 3 примера резюме
- Expected outputs для regression testing"
```

---

## 📊 Мониторинг изменений

### После каждого изменения проверяй:
```python
# Performance metrics
"Замерь до и после:
- Database query count
- Response time
- Memory usage  
- AI API calls count"

# Error monitoring
"Проверь логи на новые ошибки:
- Exception traces
- Warning messages
- Failed AI requests
- Database connection issues"
```

### Перед production deploy:
```bash
# Load testing
"Протестируй под нагрузкой:
- 100 concurrent users
- 500 requests per minute
- Memory usage под нагрузкой
- Database connection pool"
```

---

## 🎯 Специальные инструкции для компонентов

### AI Services:
- Всегда preserve fallback OpenAI ↔ Claude
- Log token usage для cost monitoring  
- Timeout handling обязателен
- Cache similar prompts

### Database:
- Batch аналитические события
- Connection pooling настроен
- RLS политики проверены
- **ОБЯЗАТЕЛЬНО:** Миграции для ВСЕХ schema changes
- **ОБЯЗАТЕЛЬНО:** Rollback план для каждой миграции
- **ОБЯЗАТЕЛЬНО:** Тестирование на dev копии prod данных
- **ОБЯЗАТЕЛЬНО:** Индексы для новых полей с поиском
- **НИКОГДА:** НЕ менять supabase_schema.sql напрямую

### Telegram Bot:
- ConversationHandler state persistent
- Error messages user-friendly  
- Rate limiting на user actions
- Input validation строгий

### Security:
- PII не логируется НИКОГДА
- Rate limiting обязателен
- Input sanitization всегда
- Environment variables через config

---

## 🚀 Готово к продакшену чек-лист

Перед каждым релизом:
- [ ] Все тесты проходят
- [ ] Load test под 1000+ users
- [ ] Security audit пройден
- [ ] AI prompts протестированы
- [ ] Database migrations применены
- [ ] Monitoring настроен
- [ ] Rollback plan готов
- [ ] Documentation обновлена

**Помни:** Этот бот обрабатывает персональные данные пользователей и генерирует контент за деньги. Каждая ошибка = потеря доверия и возможные штрафы. 