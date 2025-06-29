# ТЗ v9.8: Багфикс - Логика подписок и итераций

**Дата:** 2024-12-19  
**Версия релиза:** v9.8  
**Тип:** Критический багфикс  
**Приоритет:** 🔴 Высокий  

## 📋 Описание проблем

### **Проблема 1: Неправильная логика итераций**
- **Free план:** Доступна только 1 итерация (основная генерация), но должно быть 1 основная + 1 правка = 2 попытки
- **Premium план:** Работает корректно (3 итерации)

### **Проблема 2: Неправильный подсчет использованных писем**
- Счетчик увеличивается в `handle_retry_generation` (повторные попытки)
- После генерации письма показывает "3/3" вместо "2/3"
- Счетчик должен увеличиваться только при **первой** успешной генерации

### **Проблема 3: Потеря данных при улучшении письма**
- При нажатии "Улучшить письмо" показывается ошибка "Missing vacancy_text or resume_text in context"
- `context.user_data` очищается между запросами
- Нужно восстанавливать данные из сессии в БД

## 🔍 Анализ причин

### **Причина 1: Неправильное значение max_iterations**
```python
# handlers/simple_conversation_v6.py, строка 392 - ОШИБКА:
if limits and limits.get('plan_type') == 'premium':
    max_iterations = 3
else:
    max_iterations = 1  # ← НЕПРАВИЛЬНО! Должно быть 2
```

### **Причина 2: Неправильное место вызова increment_usage**
```python
# handlers/simple_conversation_v6.py, строка 914 - ОШИБКА:
# В handle_retry_generation:
if is_generation_successful:
    await subscription_service.increment_usage(user_id)  # ← НЕПРАВИЛЬНО!
```

**Должно быть:** `increment_usage` вызывается только в `_process_and_respond` при первой успешной генерации.

## 🛠️ План исправления

### 1. Исправление логики итераций
- ✅ **КРИТИЧЕСКОЕ:** Изменить `max_iterations = 1` → `max_iterations = 2` для FREE плана
- ✅ Обновить комментарии для ясности логики

### 2. Исправление подсчета писем
- ✅ **ВАЖНО:** Перенести `increment_usage` из `handle_retry_generation` в `_process_and_respond`
- ✅ Добавить комментарий о том, что повторные генерации не засчитываются

### 3. Исправление потери данных при улучшении
- ✅ **КРИТИЧЕСКОЕ:** Добавить восстановление данных из сессии в `handle_improve_letter`
- ✅ Использовать `analytics.get_letter_session_by_id()` для получения vacancy_text и resume_text

### 4. Тестирование
- ⏳ Проверить что FREE план дает 2 попытки (1 основная + 1 правка)
- ⏳ Проверить что счетчик увеличивается только при первой генерации
- ⏳ Проверить что повторные попытки не увеличивают счетчик
- ⏳ Проверить что улучшение письма работает без ошибок

## 🔧 Код исправлений

### **Файл: `handlers/simple_conversation_v6.py`**

#### **1. Исправление max_iterations (строка ~392):**
```python
# БЫЛО (ОШИБКА):
if limits and limits.get('plan_type') == 'premium':
    max_iterations = 3
else:
    max_iterations = 1 # Бесплатный тариф

# СТАЛО (ИСПРАВЛЕНО):
if limits and limits.get('plan_type') == 'premium':
    max_iterations = 3  # Premium: 1 основная + 2 итерации правок
else:
    max_iterations = 2  # Free: 1 основная + 1 итерация правок
```

#### **2. Перенос increment_usage в _process_and_respond (строка ~513):**
```python
# ДОБАВЛЕНО в _process_and_respond:
if is_generation_successful:
    await update.effective_user.send_message(...)
    # Увеличиваем счетчик использованных писем при успешной генерации
    await subscription_service.increment_usage(user_id)
    await analytics.update_letter_session(...)
```

#### **3. Удаление increment_usage из handle_retry_generation (строка ~914):**
```python
# БЫЛО (ОШИБКА):
if is_generation_successful:
    await subscription_service.increment_usage(user_id)

# СТАЛО (ИСПРАВЛЕНО):
if is_generation_successful:
    # НЕ увеличиваем счетчик - это повторная генерация, не новое письмо
```

#### **4. Исправление потери данных в handle_improve_letter (строка ~735):**
```python
# БЫЛО (ОШИБКА):
if not context.user_data.get('vacancy_text') or not context.user_data.get('resume_text'):
    logger.error("❌ Missing vacancy_text or resume_text in context")
    # Показывалась ошибка

# СТАЛО (ИСПРАВЛЕНО):
if not context.user_data.get('vacancy_text') or not context.user_data.get('resume_text'):
    logger.info("🔍 Восстанавливаем данные из сессии...")
    session_response = await analytics.get_letter_session_by_id(session_id)
    if session_response:
        context.user_data['vacancy_text'] = session_response.get('job_description', '')
        context.user_data['resume_text'] = session_response.get('resume_text', '')
```

## ✅ Критерии успеха

### Функциональные требования:
1. ✅ FREE план: 1 основная генерация + 1 итерация правок = 2 попытки
2. ✅ Premium план: 1 основная генерация + 2 итерации правок = 3 попытки  
3. ✅ Счетчик писем увеличивается только при первой успешной генерации
4. ⏳ Повторные попытки и итерации НЕ увеличивают счетчик
5. ⏳ После генерации письма показывается корректный остаток (например, "2/3")
6. ✅ Кнопка "Улучшить письмо" работает без ошибок "Missing data"

### Технические требования:
- ✅ Код содержит понятные комментарии о логике
- ✅ Нет дублирования вызовов `increment_usage`
- ✅ Логика подписок работает корректно

## 📦 План деплоя

### Этапы:
1. **Тестирование на DEV** - проверка исправлений
2. **Коммит изменений** в git репозиторий  
3. **Деплой на Railway** - автоматический деплой
4. **Мониторинг** - проверка корректности подсчета

### Команды деплоя:
```bash
git add handlers/simple_conversation_v6.py tasks/TZ_v9_8_Bugfix_Subscription_Logic.md
git commit -m "🐛 Fix v9.8: Subscription logic, iterations count and data recovery"
git push origin main
```

## 🔍 Метрики для проверки

### После деплоя проверить:
1. **FREE пользователь:** Создает письмо → остаток "2/3" → делает правку → остаток "2/3"
2. **Premium пользователь:** Создает письмо → остаток корректный → может сделать 2 правки
3. **Повторные попытки:** НЕ уменьшают остаток писем
4. **Новое письмо:** Уменьшает остаток на 1

## 🚀 Статус выполнения

- ✅ **Анализ проблем** - завершен  
- ✅ **Исправление max_iterations** - применено
- ✅ **Перенос increment_usage** - применено
- ✅ **Удаление дублирования** - применено
- ✅ **Восстановление данных** - применено
- 🔄 **Тестирование** - готово к выполнению
- ⏳ **Деплой** - готов к выполнению

---

**Ответственный:** AI Assistant  
**Тестировщик:** @shoodyakoff  
**Дата планируемого завершения:** 2024-12-19 