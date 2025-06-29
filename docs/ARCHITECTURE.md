# 🏗️ Техническая архитектура

> **Системная архитектура AI Telegram бота для генерации сопроводительных писем**

## 🔧 ТЕХНИЧЕСКИЙ СТЕК

### **Core Technologies**
- **Python 3.11+** - основной язык разработки
- **python-telegram-bot** - Telegram Bot API framework
- **Supabase** - PostgreSQL база данных + realtime
- **Railway** - deployment platform
- **Redis** - кеширование и rate limiting (optional)

### **AI Providers**
- **OpenAI GPT-4o** - основной AI провайдер
- **Anthropic Claude-3.5** - fallback AI провайдер
- **Dual Provider Architecture** - автоматическое переключение при сбоях

## 📁 АРХИТЕКТУРА КОДА

```
tg_soprovod/
├── 🎯 main.py              # Entry point
├── ⚙️ config.py           # Configuration
├── 🗂️ handlers/           # Telegram handlers
│   └── simple_conversation_v6.py
├── 🛠️ services/           # Business logic
│   ├── ai_service.py       # AI orchestration
│   ├── subscription_service.py
│   ├── analytics_service.py
│   └── feedback_service.py
├── 📊 models/             # Data models
├── 🔧 utils/              # Utilities
│   ├── validators.py
│   ├── rate_limiter.py
│   └── keyboards.py
└── 🗄️ migrations/         # Database migrations
```

## 🔄 ПРОЦЕСС ГЕНЕРАЦИИ

```mermaid
graph TD
    A[Вакансия] --> B[Резюме]
    B --> C[AI Service]
    C --> D{Выбор провайдера}
    D -->|Primary| E[OpenAI GPT-4o]
    D -->|Fallback| F[Claude-3.5]
    E --> G[Письмо]
    F --> G
    G --> H[Валидация]
    H --> I[Пользователь]
```

## 🗄️ БАЗА ДАННЫХ

### **Основные таблицы:**
- `users` - пользователи бота
- `subscriptions` - подписки и лимиты
- `letter_sessions` - сессии генерации писем
- `user_feedback` - обратная связь
- `analytics_events` - события аналитики

### **Views:**
- `user_cohorts_basic` - аналитика когорт пользователей
- `user_feedback_stats` - статистика обратной связи

## 🔒 БЕЗОПАСНОСТЬ

- **Rate Limiting:** 5 команд/мин, 3 AI запроса/5мин
- **PII Санитизация:** Удаление персональных данных из логов
- **Input Validation:** Максимум 50KB текста
- **GDPR Compliance:** Согласие на обработку ПД

## 📊 АНАЛИТИКА

- **User Journey Tracking** - отслеживание пути пользователя
- **Conversion Metrics** - метрики конверсии в Premium
- **AI Performance** - качество и скорость генерации
- **Error Monitoring** - мониторинг ошибок

## 🚀 DEPLOYMENT

- **Platform:** Railway
- **Environment:** Production
- **Auto-deploy:** Git push → Railway deploy
- **Database:** Supabase PostgreSQL

---

**Принципы:** Simple, Scalable, Secure, Sustainable 