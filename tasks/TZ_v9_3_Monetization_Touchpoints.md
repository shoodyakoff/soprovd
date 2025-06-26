# 💰 ТЗ v9.3 - Monetization Touchpoints (Точки монетизации)

## ⚠️ КРИТИЧЕСКИ ВАЖНО - ПРАВИЛА РАБОТЫ С ТЗ
- ✅ **Следовать строго по ТЗ** при любых изменениях кода
- ✅ **Менять ТЗ и связанные пункты** при обнаружении несоответствий
- ✅ **Поэтапные изменения файлов** (до 50-100 строк за раз)

---

## 🎯 **ЦЕЛЬ ЗАДАЧИ**
Добавить 4+ touchpoints для конверсии в premium подписку без ухудшения UX

## 📊 **СТАТУС ВЫПОЛНЕНИЯ**
- ✅ **3.1** Premium кнопки созданы (4 типа клавиатур)
- ✅ **3.2** 4 touchpoints интегрированы в бот (limit_reached, post_generation, iteration)
- ✅ **3.3** Analytics tracking настроен (4 новых события)
- ✅ **3.4** Команда `/premium` реализована (+ 5 callback handlers)

---

## 🛠 **ДЕТАЛЬНЫЙ ПЛАН РЕАЛИЗАЦИИ**

### **3.1 Premium кнопки** ⏳
**Файлы для изменения:**
- `utils/keyboards.py` (добавить новые кнопки)

**Cursor промпт 3.1:**
```
Добавь premium кнопки в utils/keyboards.py (строка ~50):

1. **Новые inline кнопки:**
   - "💎 Получить Premium" → callback: premium_inquiry
   - "📞 Связаться с нами" → callback: contact_support  
   - "⭐ Узнать больше" → callback: premium_info
   - "🔓 Разблокировать лимиты" → callback: unlock_limits

2. **Красивое оформление:**
   - Эмодзи для визуальной привлекательности
   - Понятные тексты кнопок
   - НЕ агрессивные формулировки

3. **НЕ ломать существующие keyboards:**
   - Добавить новые функции, не менять старые
   - Совместимость с текущими callback handlers

4. **Keyboard layouts:**
   - limit_reached_keyboard() → показ при исчерпании лимита
   - post_generation_keyboard() → после успешной генерации
   - premium_info_keyboard() → детальная информация
```

### **3.2 Touchpoints Integration** ⏳
**Файлы для изменения:**
- `handlers/simple_conversation_v6.py` (4 точки монетизации)

**Cursor промпт 3.2:**
```
Добавь 4 touchpoints в handlers/simple_conversation_v6.py:

1. **ГЛАВНЫЙ touchpoint (строка ~45) - При исчерпании лимита:**
   - Сообщение: "🚫 Лимит бесплатных писем исчерпан (3/3)"
   - "💎 Premium дает 20 писем в день + лучшее качество"
   - Кнопки: "💎 Получить Premium" / "📞 Связаться"

2. **SOFT SELL touchpoint (строка ~120) - После генерации:**
   - Сообщение: "✅ Письмо готово! Понравилось качество?"
   - "⭐ Premium использует GPT-4 + Claude для еще лучших результатов"
   - Кнопки: "⭐ Узнать больше" / "Продолжить бесплатно"

3. **UPSELL touchpoint (строка ~200) - При повторных запросах:**
   - Сообщение: "🔄 Хотите улучшить письмо еще раз?"
   - "💎 Premium позволяет 20 писем в день + приоритет"
   - Кнопки: "🔓 Разблокировать" / "Оставить как есть"

4. **НОВЫЙ handler - команда /premium:**
   - Полная информация о premium
   - Сравнение Free vs Premium
   - "Стоимость: 400 рублей/месяц, оплата через @shoodyakoff"

5. **НЕ ломать ConversationHandler flow**
```

### **3.3 Analytics Tracking** ⏳
**Файлы для изменения:**
- `services/analytics_service.py` (tracking touchpoints)

**Cursor промпт 3.3:**
```
Добавь monetization tracking в services/analytics_service.py:

1. **Новые события для отслеживания:**
   - premium_offer_shown → когда показан touchpoint
   - premium_button_clicked → клик на premium кнопку
   - contact_initiated → клик на "Связаться"
   - premium_info_viewed → просмотр /premium команды

2. **Метаданные событий:**
   - touchpoint_location: 'limit_reached', 'post_generation', 'iteration', 'command'
   - user_generation_count: сколько писем уже сгенерировал
   - session_duration: сколько времени в боте

3. **НЕ ломать существующую аналитику:**
   - Добавить новые методы, не менять старые
   - Совместимость с текущими событиями

4. **GDPR compliance:**
   - НЕ логировать PII в events
   - Только user_id (хешированный) + метрики
   - Batch отправка для производительности

5. **A/B testing готовность:**
   - Поле ab_test_group: 'control', 'touchpoints_enabled'
   - Возможность включать/выключать touchpoints
```

### **3.4 Premium Command** ⏳
**Файлы для изменения:**
- `handlers/simple_conversation_v6.py` (новая команда /premium)

**Cursor промпт 3.4:**
```
Добавь команду /premium в handlers/simple_conversation_v6.py:

1. **Информационная страница:**
   - Сравнительная таблица Free vs Premium
   - Преимущества: 20 писем в день, GPT-4 + Claude, приоритет
   - Цена: "400 рублей/месяц"

2. **Красивое форматирование:**
   - Эмодзи для визуального разделения
   - Четкая структура информации
   - Призыв к действию в конце

3. **Интеграция с analytics:**
   - Трекинг просмотра premium_info_viewed
   - Кнопки для связи: "📞 Связаться" → contact_initiated

4. **НЕ влияет на ConversationHandler:**
   - Команда работает в любой момент
   - После просмотра → возврат к текущему состоянию
```

---

## ✅ **КРИТЕРИИ ГОТОВНОСТИ (Definition of Done)**

### Monetization Features
- ✅ 4+ touchpoints интегрированы в бот
- ✅ Красивое оформление premium предложений
- ✅ Analytics tracking всех touchpoints
- ✅ Команда `/premium` работает корректно
- ✅ Кнопки ведут на связь с @shoodyakoff
- ✅ A/B testing готовность (включить/выключить)

---

## 🧪 **ПЛАН ТЕСТИРОВАНИЯ**

### A/B Testing Framework
```python
def test_premium_conversion():
    """Тест конверсии в premium"""
    # A: С touchpoints vs B: Без touchpoints
    # Метрики: CTR, conversion rate, user satisfaction
    # Статистическая значимость результатов

def test_touchpoint_effectiveness():
    """Тест эффективности touchpoints"""
    # Какой touchpoint конвертирует лучше
    # Время показа: сразу vs после генерации
    # Текст предложения: агрессивный vs мягкий
```

### UX Testing
```python
def test_user_experience():
    """Тест пользовательского опыта"""
    # Предложения не раздражают пользователей
    # Кнопки работают корректно
    # Telegram @username корректный
```

### Ручное тестирование
- [ ] Лимит исчерпан → показ главного touchpoint
- [ ] После генерации → soft sell предложение
- [ ] Повторные запросы → upsell touchpoint
- [ ] `/premium` → полная информация о подписке
- [ ] Кнопки ведут на @shoodyakoff в Telegram
- [ ] Красивое оформление на всех устройствах
- [ ] Analytics события отправляются корректно

---

## 📈 **МЕТРИКИ УСПЕХА**
- **Premium conversion rate:** +25% от baseline
- **Touchpoint CTR:** 10% пользователей кликают на premium кнопки
- **Contact conversion:** 5% реально обращаются в @shoodyakoff
- **User satisfaction:** НЕ хуже текущего (>=4.5/5)

---

## 🚨 **РИСКИ И ОГРАНИЧЕНИЯ**
- **НЕ раздражать** пользователей агрессивными предложениями
- **НЕ ломать** основной flow генерации писем
- **НЕ замедлять** работу бота
- **Временное решение:** оплата через @shoodyakoff (не автоматизировано)

---

## 💡 **БУДУЩИЕ УЛУЧШЕНИЯ (НЕ в этом ТЗ)**
- Автоматизированная оплата через Telegram Payments
- Персонализированные предложения на основе поведения
- Реферальная программа
- Пробный период Premium (7 дней)

---

**Время выполнения:** 6 часов  
**Приоритет:** ВАЖНЫЙ (Business growth) 