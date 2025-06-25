 # 🚀 ИНСТРУКЦИЯ ПО РЕЛИЗУ СОПРОВОД V7.0

## 📋 ЧТО РЕЛИЗИТСЯ:
- ✅ Система подписок с лимитами (FREE: 3 письма/месяц, PREMIUM: 20 писем/день)
- ✅ Система оценок и итераций (лайк/дизлайк/комментарий)
- ✅ Улучшение писем до 3 раз на письмо
- ✅ Детальная аналитика и статистика
- ✅ SQL инструменты для администрирования

---

## 🗂️ ФАЙЛЫ ДЛЯ КОММИТА:

### ✅ Обязательные файлы:
```
config.py                    # Добавлены настройки подписок
handlers/simple_conversation_v6.py  # Новые обработчики оценок
services/subscription_service.py    # Сервис проверки лимитов  
services/feedback_service.py        # Сервис оценок и итераций
models/subscription_models.py       # Модели подписок
models/feedback_models.py           # Модели оценок
utils/keyboards.py                  # Кнопки для оценок
services/analytics_service.py       # Расширенная аналитика
```

### 📊 SQL скрипты:
```
update_schema_v7.sql        # Основное обновление БД
add_feedback_system.sql     # Система оценок
manage_subscriptions.sql    # Управление подписками
supabase_schema.sql         # Обновленная полная схема
```

### 📝 Документация:
```
tzv7.md                     # Обновленный план
RELEASE_INSTRUCTIONS.md     # Эта инструкция
```

---

## 🔧 ПОШАГОВАЯ ИНСТРУКЦИЯ:

### ШАГ 1: ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ

#### 1.1 Войти в Supabase Dashboard
- Перейти в SQL Editor
- Открыть проект Сопровод

#### 1.2 Выполнить SQL скрипты (В СТРОГОМ ПОРЯДКЕ!)

**Первый скрипт - Основное обновление:**
```sql
-- Скопировать и выполнить содержимое update_schema_v7.sql
-- Этот скрипт создаст таблицы subscriptions, payments, letter_iterations
```

**Второй скрипт - Система оценок:**
```sql  
-- Скопировать и выполнить содержимое add_feedback_system.sql
-- Этот скрипт добавит таблицу letter_feedback и обновит существующие
```

#### 1.3 Проверить создание таблиц
В Table Editor должны появиться:
- ✅ `subscriptions` (подписки пользователей)
- ✅ `payments` (платежи)  
- ✅ `letter_iterations` (итерации писем)
- ✅ `letter_feedback` (оценки писем)

---

### ШАГ 2: ОБНОВЛЕНИЕ ПЕРЕМЕННЫХ RAILWAY

#### 2.1 Войти в Railway Dashboard
- Перейти в проект Сопровод
- Открыть раздел Variables

#### 2.2 Добавить новые переменные:
```bash
SUBSCRIPTIONS_ENABLED=true
FREE_LETTERS_LIMIT=3
PREMIUM_LETTERS_LIMIT=20
```

#### 2.3 Проверить существующие переменные:
```bash
ANALYTICS_ENABLED=true          # Должно быть true
SUPABASE_URL=https://...        # Должен быть заполнен
SUPABASE_KEY=eyJ...             # Должен быть заполнен
TELEGRAM_BOT_TOKEN=7647818988:...  # Должен быть заполнен
AI_PROVIDER=claude              # claude или openai
ANTHROPIC_API_KEY=sk-ant-...    # Если используете Claude
```

---

### ШАГ 3: КОММИТ И ДЕПЛОЙ КОДА

#### 3.1 Добавить файлы в git:
```bash
# Переходим в папку проекта
cd /Users/stas/tg_soprovod

# Добавляем все измененные файлы
git add config.py
git add handlers/simple_conversation_v6.py
git add services/subscription_service.py
git add services/feedback_service.py
git add services/analytics_service.py
git add models/subscription_models.py
git add models/feedback_models.py
git add utils/keyboards.py
git add update_schema_v7.sql
git add add_feedback_system.sql
git add manage_subscriptions.sql
git add supabase_schema.sql
git add tzv7.md
git add RELEASE_INSTRUCTIONS.md
```

#### 3.2 Создать коммит:
```bash
git commit -m "🚀 Release v7.0: Subscription system + Feedback system

✅ Features:
- Daily limits: 20 letters per day for free users
- Feedback system: like/dislike/comment buttons  
- Letter iterations: up to 3 improvements per letter
- Analytics: detailed usage statistics
- Admin tools: SQL scripts for subscription management

✅ New services:
- SubscriptionService: limit checking
- FeedbackService: ratings and iterations

✅ Database:
- subscriptions table with daily limits
- letter_feedback table for ratings
- letter_iterations table for improvements
- payments table for future monetization

✅ Config:
- SUBSCRIPTIONS_ENABLED setting
- FREE_LETTERS_LIMIT=20 (daily)
- PREMIUM_LETTERS_LIMIT=999999

🔧 Technical:
- Unified plan_type field across all tables
- Safe fallback if DB fails
- Type safety improvements
- RLS policies for security"
```

#### 3.3 Отправить в репозиторий:
```bash
git push origin main
```

#### 3.4 Дождаться автодеплоя Railway
- Railway автоматически подхватит изменения
- Следить за логами деплоя в Railway Dashboard
- Ждать статус "Deployed"

---

### ШАГ 4: ПРОВЕРКА РАБОТОСПОСОБНОСТИ

#### 4.1 Проверить запуск бота:
- Открыть логи в Railway
- Искать сообщения:
  ```
  ✅ Analytics configured
  ✅ Subscription service initialized  
  🚀 Бот Сопровод v6.0 запущен
  ```

#### 4.2 Протестировать основной функционал:
```
1. /start - должен работать как обычно
2. Отправить вакансию - должна приниматься
3. Отправить резюме - должно генерироваться письмо
4. После письма - должны появиться кнопки ❤️👎💬
5. Нажать кнопку - должен работать сбор обратной связи
```

#### 4.3 Проверить лимиты:
- Создать тестового пользователя
- Сгенерировать 3 письма (для FREE плана)
- На 4-м письме должно появиться сообщение о лимите

#### 4.4 Проверить аналитику:
- В Supabase Table Editor открыть таблицы
- Должны появляться записи в:
  - `users` (пользователи)
  - `letter_sessions` (сессии)
  - `subscriptions` (подписки)
  - `letter_feedback` (при оценках)

---

### ШАГ 5: АДМИНИСТРИРОВАНИЕ

#### 5.1 Ручное управление подписками:
Использовать файл `manage_subscriptions.sql` для:
- Просмотра всех подписок
- Выдачи премиум доступа
- Сброса лимитов
- Блокировки пользователей

#### 5.2 Мониторинг:
```sql
-- Статистика подписок
SELECT * FROM subscription_stats;

-- Статистика оценок  
SELECT * FROM feedback_stats;

-- Активность пользователей
SELECT * FROM user_activity;
```

---

## ⚠️ КРИТИЧЕСКИЕ МОМЕНТЫ:

### 🚨 ОБЯЗАТЕЛЬНО ПРОВЕРИТЬ:
1. **SQL скрипты выполнены БЕЗ ошибок**
2. **Переменная SUBSCRIPTIONS_ENABLED=true установлена**
3. **Бот запустился без ошибок в логах**
4. **Кнопки оценок появляются после генерации письма**
5. **Лимиты работают корректно**

### 🔧 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ:

#### Проблема: SQL ошибки
```sql
-- Проверить существование таблиц
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('subscriptions', 'letter_feedback', 'letter_iterations');
```

#### Проблема: Бот не запускается
- Проверить логи Railway на ошибки Python
- Убедиться что все переменные окружения установлены
- Проверить что Supabase доступен

#### Проблема: Лимиты не работают
- Установить `SUBSCRIPTIONS_ENABLED=false` для отключения
- Проверить подключение к Supabase
- Посмотреть логи сервиса подписок

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:

### ✅ После успешного релиза:
- Пользователи видят лимит "Осталось писем: X"
- После письма появляются кнопки оценки
- Можно улучшать письма до 3 раз
- Админ может управлять подписками через SQL
- Собирается детальная аналитика

### 📈 Метрики для отслеживания:
- Количество генераций в день
- Процент пользователей, достигших лимита
- Распределение оценок (лайки/дизлайки)
- Частота использования итераций
- Время генерации писем

---

## 🎉 ПОЗДРАВЛЯЕМ!

**Сопровод v7.0 успешно релизнут!** 🚀

Система подписок и оценок работает, пользователи могут улучшать письма, а вы получаете детальную аналитику для дальнейшего развития продукта.