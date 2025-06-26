# 📋 ТЗ v9.5 - Bugfix: User Cohorts Analytics (Исправление багов в аналитике когорт пользователей)

## ⚠️ КРИТИЧЕСКИ ВАЖНО - ПРАВИЛА РАБОТЫ С ТЗ
- ✅ **Следовать строго по ТЗ** при любых изменениях кода
- ✅ **Менять ТЗ и связанные пункты** при обнаружении несоответствий
- ✅ **Поэтапные изменения файлов** (до 50-100 строк за раз)

---

## 🐛 **ОПИСАНИЕ ПРОБЛЕМЫ**

### Исходная ситуация
В продакшене обнаружены критические ошибки в VIEW `user_cohorts_basic`:
- **Проблема 1:** Дата из будущего `2025-06-01` (должна быть текущий месяц)
- **Проблема 2:** Нереальные цифры: 54 пользователя, 49 premium (на dev контуре)
- **Проблема 3:** Неправильная логика вычисления когорт и активированных пользователей
- **Проблема 4:** VIEW используется для продакшен аналитики, но работает некорректно

### Техническая причина
VIEW `user_cohorts_basic` создан с **неправильной логикой**:
1. **Неправильные timezone вычисления** - берет будущие даты
2. **Некорректная логика активации** - считает всех пользователей активированными
3. **Неправильный подсчет premium** - использует тестовые данные
4. **Отсутствие фильтрации** по реальным данным

---

## 🎯 **ЦЕЛЬ ЗАДАЧИ**
Исправить VIEW `user_cohorts_basic` для корректной аналитики когорт пользователей на продакшене

## 📊 **СТАТУС ВЫПОЛНЕНИЯ**
- ⏳ **5.1** Анализ текущей структуры VIEW - В ПРОЦЕССЕ
- ⏳ **5.2** Исправление логики дат и timezone - НЕ НАЧАТО
- ⏳ **5.3** Исправление логики активированных пользователей - НЕ НАЧАТО
- ⏳ **5.4** Исправление подсчета premium пользователей - НЕ НАЧАТО
- ⏳ **5.5** Добавление фильтрации по периодам - НЕ НАЧАТО
- ⏳ **5.6** Тестирование на реальных данных - НЕ НАЧАТО

---

## 🛠 **ДЕТАЛЬНЫЙ ПЛАН РЕАЛИЗАЦИИ**

### **5.1 Анализ текущей структуры VIEW** ⏳
**Текущие поля:**
- `cohort_month` - месяц когорты (НЕПРАВИЛЬНО: показывает 2025-06-01)
- `acquisition_channel` - канал привлечения (NULL для всех)
- `cohort_size` - размер когорты (НЕПРАВИЛЬНО: 54 на dev)
- `activated_users` - активированные пользователи (НЕПРАВИЛЬНО: 51)
- `premium_users` - premium пользователи (НЕПРАВИЛЬНО: 49)
- `avg_days_to_first_generation` - среднее время до первого письма

### **5.2 Исправление логики дат и timezone** ⏳
**Проблема:**
```sql
-- Текущая неправильная логика (показывает будущие даты)
DATE_TRUNC('month', some_wrong_field) 
```

**Исправление:**
```sql
-- Правильная логика с учетом timezone
DATE_TRUNC('month', u.created_at AT TIME ZONE 'UTC')::date as cohort_month
WHERE u.created_at >= CURRENT_DATE - INTERVAL '12 months'
  AND u.created_at < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
```

### **5.3 Исправление логики активированных пользователей** ⏳
**Проблема:** Считает всех пользователей активированными

**Правильная логика:**
```sql
-- Активированный = создал хотя бы одно письмо
COUNT(DISTINCT CASE 
  WHEN ls.id IS NOT NULL AND ls.status = 'completed' 
  THEN u.id 
END) as activated_users
```

### **5.4 Исправление подсчета premium пользователей** ⏳
**Проблема:** Неправильно считает premium подписки

**Правильная логика:**
```sql
-- Premium = активная premium подписка
COUNT(DISTINCT CASE 
  WHEN s.plan_type = 'premium' AND s.status = 'active' 
  THEN u.id 
END) as premium_users
```

### **5.5 Добавление фильтрации по периодам** ⏳
**Добавить фильтры:**
- Только последние 12 месяцев
- Исключить тестовых пользователей (если есть)
- Группировка по месяцам корректно

### **5.6 Создание правильного VIEW** ⏳
**Полная корректная версия:**
```sql
DROP VIEW IF EXISTS user_cohorts_basic;

CREATE VIEW user_cohorts_basic AS
SELECT 
    DATE_TRUNC('month', u.created_at AT TIME ZONE 'UTC')::date as cohort_month,
    COALESCE(ac.utm_source, 'direct') as acquisition_channel,
    COUNT(DISTINCT u.id) as cohort_size,
    COUNT(DISTINCT CASE 
        WHEN ls.id IS NOT NULL AND ls.status = 'completed' 
        THEN u.id 
    END) as activated_users,
    COUNT(DISTINCT CASE 
        WHEN s.plan_type = 'premium' AND s.status = 'active' 
        THEN u.id 
    END) as premium_users,
    ROUND(
        AVG(
            CASE 
                WHEN ls.created_at IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (ls.created_at - u.created_at))/86400 
            END
        ), 2
    ) as avg_days_to_first_generation
FROM users u
LEFT JOIN acquisition_channels ac ON u.id = ac.user_id  
LEFT JOIN letter_sessions ls ON u.id = ls.user_id 
    AND ls.status = 'completed'
    AND ls.created_at = (
        SELECT MIN(ls2.created_at) 
        FROM letter_sessions ls2 
        WHERE ls2.user_id = u.id AND ls2.status = 'completed'
    )
LEFT JOIN subscriptions s ON u.id = s.user_id 
    AND s.status = 'active'
WHERE u.created_at >= CURRENT_DATE - INTERVAL '12 months'
    AND u.created_at < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
    -- Исключаем тестовых пользователей (если нужно)
    AND u.telegram_user_id NOT IN (SELECT telegram_user_id FROM users WHERE username LIKE '%test%')
GROUP BY 
    DATE_TRUNC('month', u.created_at AT TIME ZONE 'UTC')::date,
    COALESCE(ac.utm_source, 'direct')
HAVING COUNT(DISTINCT u.id) > 0
ORDER BY cohort_month DESC, acquisition_channel;
```

---

## ✅ **КРИТЕРИИ ГОТОВНОСТИ (Definition of Done)**

### Функциональные требования
- ✅ **Корректные даты** - показывает реальные месяцы, НЕ будущие
- ✅ **Правильный подсчет когорт** - количество пользователей по месяцам регистрации
- ✅ **Корректная активация** - только пользователи создавшие письма
- ✅ **Правильный premium** - только активные premium подписки
- ✅ **Реальные каналы привлечения** - НЕ только NULL
- ✅ **Фильтрация периода** - только последние 12 месяцев

### Технические требования
- ✅ **Производительность** - VIEW выполняется быстро (< 5 сек)
- ✅ **Timezone корректность** - правильная работа с UTC
- ✅ **Исключение тестовых данных** - НЕ влияют на продакшен аналитику
- ✅ **Совместимость** с существующими дашбордами

---

## 🧪 **ПЛАН ТЕСТИРОВАНИЯ**

### Критические сценарии
```sql
-- Тест 1: Проверка корректности дат
SELECT cohort_month FROM user_cohorts_basic 
WHERE cohort_month > CURRENT_DATE;
-- Результат: ПУСТОЙ (не должно быть будущих дат)

-- Тест 2: Проверка логики активации
SELECT cohort_month, cohort_size, activated_users 
FROM user_cohorts_basic 
WHERE activated_users > cohort_size;
-- Результат: ПУСТОЙ (активированных не может быть больше когорты)

-- Тест 3: Проверка premium логики
SELECT cohort_month, cohort_size, premium_users 
FROM user_cohorts_basic 
WHERE premium_users > cohort_size;
-- Результат: ПУСТОЙ (premium не может быть больше когорты)

-- Тест 4: Проверка каналов привлечения
SELECT DISTINCT acquisition_channel FROM user_cohorts_basic;
-- Результат: НЕ только NULL, есть 'direct' и другие каналы
```

### Ручное тестирование
- [ ] **Даты реальные:** Все cohort_month <= текущий месяц
- [ ] **Цифры адекватные:** Количества соответствуют реальности
- [ ] **Логика активации:** Только пользователи с письмами
- [ ] **Premium корректно:** Только активные подписки

---

## 📈 **ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ**

### До исправления
```
❌ user_cohorts_basic:
   cohort_month: 2025-06-01 (БУДУЩЕЕ!)
   cohort_size: 54 (нереально для dev)
   activated_users: 51 (неправильная логика)
   premium_users: 49 (тестовые данные)
```

### После исправления  
```
✅ user_cohorts_basic:
   cohort_month: 2024-12-01 (реальная дата)
   cohort_size: 3 (реальное количество)
   activated_users: 2 (только создавшие письма)
   premium_users: 0 (корректно для dev)
```

---

## 🚨 **РИСКИ И ОГРАНИЧЕНИЯ**

### МИНИМАЛЬНЫЕ риски
- ✅ **Только изменение VIEW** - НЕ трогаем основные таблицы
- ✅ **Откат за 1 минуту** - можем быстро восстановить старую версию
- ✅ **НЕ влияет на пользователей** - только внутренняя аналитика

### Средние риски
- ⚠️ **Дашборды могут сломаться** - если зависят от старой структуры
- ⚠️ **Изменение данных** - цифры в аналитике изменятся

### Откат (если нужен)
```sql
-- Быстрый откат к старой версии
DROP VIEW IF EXISTS user_cohorts_basic;
-- Восстановить старую версию из бэкапа
```
- Время отката: **1 минута**

---

## 💡 **ДОПОЛНИТЕЛЬНЫЕ СООБРАЖЕНИЯ**

### Почему это критично для продакшена
- **Неправильная аналитика:** Принятие решений на основе ложных данных
- **Будущие даты:** Нарушают логику отчетности
- **Репутационные риски:** Неточные метрики для стейкхолдеров

### Техническая элегантность
- ✅ **Правильные SQL практики** - корректная работа с датами и timezone
- ✅ **Производительность** - оптимизированные JOIN и фильтры
- ✅ **Читаемость** - понятная логика для будущих разработчиков

---

## 📝 **СВЯЗАННЫЕ ЗАДАЧИ**

- **ТЗ v9.4** - Bugfix Subscription Unlimited (исправлено)
- **ТЗ v9.1** - Legal Documents (выполнено)
- **ТЗ v9.2** - Security Protection (НЕ начато)
- **ТЗ v9.3** - Monetization Touchpoints (НЕ начато)

---

**Время выполнения:** 2 часа  
**Приоритет:** 🟠 ВЫСОКИЙ (Критично для продакшен аналитики)  
**Тип задачи:** Bugfix (Исправление аналитики) 