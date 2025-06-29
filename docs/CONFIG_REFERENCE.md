# ⚙️ Справочник конфигурации

> **Полный справочник всех настроек и переменных окружения**

## 🔧 Переменные окружения

### 🔑 **Обязательные настройки**

```env
# Telegram Bot API
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOPqrstuVWXyz

# AI провайдеры (требуется минимум один)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# База данных Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

### 💳 **Платежная система ЮKassa**

```env
# ЮKassa настройки
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=test_abcd1234...
YOOKASSA_ENABLED=true

# Webhook сервер
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8000
WEBHOOK_PATH=/webhook/yookassa
```

### 📊 **Аналитика и база данных**

```env
# Включение аналитики
ANALYTICS_ENABLED=true

# Подключение к базе данных
DATABASE_POOL_SIZE=10
DATABASE_TIMEOUT=30
```

### 💰 **Система подписок**

```env
# Включение подписок
SUBSCRIPTIONS_ENABLED=true

# Лимиты бесплатной версии
FREE_LETTERS_LIMIT=3
FREE_LETTERS_PERIOD_DAYS=30

# Лимиты Premium
PREMIUM_LETTERS_LIMIT=20
PREMIUM_LETTERS_PERIOD_DAYS=1
```

### 🔒 **Безопасность и ограничения**

```env
# Rate limiting
RATE_LIMITING_ENABLED=true
RATE_LIMIT_COMMANDS_PER_MINUTE=5
RATE_LIMIT_AI_PER_5MIN=3

# Лимиты контента
MAX_TEXT_SIZE_KB=50
MAX_VACANCY_LENGTH=10000
MAX_RESUME_LENGTH=20000

# Админы (через запятую)
ADMIN_TELEGRAM_IDS=123456789,987654321
```

### 🤖 **Настройки AI**

```env
# Основной провайдер (openai или claude)
AI_PROVIDER=openai

# Единый анализ (рекомендуется)
USE_UNIFIED_ANALYSIS=true

# Параметры генерации
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000
AI_TIMEOUT_SECONDS=60
```

### 🌍 **Окружение**

```env
# Окружение (development, staging, production)
ENVIRONMENT=production

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=structured

# Часовой пояс
TIMEZONE=UTC
```

## 📁 Файлы конфигурации

### **config.py**
Главный файл конфигурации, который читает переменные окружения и устанавливает defaults.

### **.env files**
- `.env` - основной файл (НЕ коммитить!)
- `env.example` - шаблон с примерами
- `.env.dev` - для разработки
- `.env.staging` - для staging окружения

## 🔧 Настройки по умолчанию

```python
# Из config.py
DEFAULT_SETTINGS = {
    'FREE_LETTERS_LIMIT': 3,
    'PREMIUM_LETTERS_LIMIT': 20,
    'RATE_LIMIT_COMMANDS_PER_MINUTE': 5,
    'RATE_LIMIT_AI_PER_5MIN': 3,
    'MAX_TEXT_SIZE_KB': 50,
    'AI_TEMPERATURE': 0.7,
    'AI_MAX_TOKENS': 2000,
    'DATABASE_POOL_SIZE': 10,
    'YOOKASSA_ENABLED': False,
    'WEBHOOK_HOST': '0.0.0.0',
    'WEBHOOK_PORT': 8000,
    'WEBHOOK_PATH': '/webhook/yookassa'
}
```

## 🚀 Настройка окружений

### **Development**
```bash
cp env.example .env.dev
# Отредактировать .env.dev
export ENVIRONMENT=development
python run_dev.py
```

### **Production (Railway)**
Настраивается через Railway Dashboard:
- Environment Variables
- Auto-deploy from GitHub
- Custom domains
- Webhook URL: `https://your-app.railway.app/webhook/yookassa`

### **Staging**
```bash
cp env.example .env.staging
# Настроить staging параметры
export ENVIRONMENT=staging
```

## 💳 Настройка ЮKassa

### **Тестовая среда**
```env
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=test_abcd1234...
YOOKASSA_ENABLED=true
```

### **Продакшн среда**
```env
YOOKASSA_SHOP_ID=live_shop_id
YOOKASSA_SECRET_KEY=live_secret_key
YOOKASSA_ENABLED=true
```

### **Webhook настройки**
- URL: `https://your-app.railway.app/webhook/yookassa`
- События: `payment.succeeded`, `payment.canceled`, `refund.succeeded`
- Проверка подписи: включена (HMAC-SHA256)

## ⚠️ Важные замечания

### **Безопасность:**
- Никогда не коммитить `.env` файлы
- Ротация API ключей каждые 90 дней
- Минимальные права для service accounts
- Проверка подписи webhook'ов ЮKassa

### **Production:**
- Всегда использовать HTTPS
- Настроить мониторинг логов
- Регулярный backup базы данных
- Мониторинг webhook доставки

### **Development:**
- Использовать отдельные API ключи
- Тестовая база данных
- Отключить rate limiting для тестов
- Использовать `ngrok` для локальной отладки webhook'ов

### **Платежи:**
- Тестировать на тестовых картах ЮKassa
- Мониторить успешность webhook'ов
- Fallback на ручную обработку при сбоях
- Логирование всех платежных операций

---

**Этот справочник автоматически обновляется при изменении config.py** 