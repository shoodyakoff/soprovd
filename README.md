# 🤖 Сопровод v9.10 - AI-powered Cover Letter Generator

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-Latest-blue.svg)](https://core.telegram.org/bots/api)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green.svg)](https://platform.openai.com/)
[![Claude](https://img.shields.io/badge/Anthropic-Claude--3.5-purple.svg)](https://www.anthropic.com/)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-blueviolet.svg)](https://railway.app/)
[![Security](https://img.shields.io/badge/Security-Rate%20Limited-red.svg)](#security)

> **Production-ready AI Telegram bot with monetization, security, and GDPR compliance**

Сопровод помогает соискателям создавать персонализированные сопроводительные письма, анализируя вакансию и резюме с помощью современных AI моделей. Включает полную систему подписок Free/Premium и защиту от злоупотреблений.

## 🎯 Основные возможности

### ✨ **AI-анализ**
- **Умный анализ вакансий** - извлечение ключевых требований и болевых точек компании
- **Персонализация под резюме** - поиск точных совпадений навыков и опыта
- **Система итераций** - до 3 улучшений письма по комментариям пользователя
- **Стилистическая адаптация** - профессиональный тон с человечными нотками

### 🚀 **Производительность**
- **30-45 секунд** - время генерации письма
- **Dual AI support** - OpenAI GPT-4o + Anthropic Claude 3.5 Sonnet
- **Асинхронная обработка** - не блокирует других пользователей
- **Smart fallbacks** - переключение между моделями при ошибках

### 💰 **Монетизация**
- **Free план** - 3 письма в месяц
- **Premium план** - 20 писем в день
- **Система подписок** - автоматическое управление лимитами
- **Гибкие тарифы** - возможность расширения функций

### 🔒 **Безопасность**
- **Rate Limiting** - 5 команд/минуту, 3 AI запроса/5 минут
- **Input Validation** - проверка размера текста до 50KB
- **DoS защита** - sliding window algorithm
- **Admin панель** - управление через Telegram

### 📊 **Аналитика & Compliance**
- **Real-time метрики** через Supabase
- **User journey tracking** - от start до готового письма
- **GDPR compliance** - согласие на обработку ПД
- **Детальное логирование** - все действия пользователей

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram      │────│   Python Bot     │────│   AI Services   │
│   Users         │    │   (Async)        │    │   GPT-4/Claude  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────┴──────┐
                       │  Analytics  │
                       │  (Supabase) │
                       └─────────────┘
```

### 🛠️ **Tech Stack**
- **Backend**: Python 3.9+, python-telegram-bot (async)
- **AI Models**: OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet
- **Database**: Supabase (PostgreSQL) с RLS
- **Security**: InMemory Rate Limiter + Input Validation
- **Deployment**: Railway (Docker)
- **Monitoring**: Supabase analytics + custom logging
- **Monetization**: Subscription system с автоматическим управлением лимитами

## 🚀 Быстрый старт

### Локальная разработка

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/your-repo/tg_soprovod.git
cd tg_soprovod
```

2. **Создайте виртуальное окружение**
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. **Установите зависимости**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения**
```bash
cp env.example .env.dev
# Отредактируйте .env.dev файл
```

5. **Запустите бота**
```bash
python run_dev.py
```

### 🔧 Переменные окружения

#### Обязательные:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_claude_key
```

#### Аналитика и База данных:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
ANALYTICS_ENABLED=true
```

#### Система подписок:
```env
SUBSCRIPTIONS_ENABLED=true
FREE_LETTERS_LIMIT=3
PREMIUM_LETTERS_LIMIT=20
```

#### Безопасность:
```env
RATE_LIMITING_ENABLED=true
RATE_LIMIT_COMMANDS_PER_MINUTE=5
RATE_LIMIT_AI_PER_5MIN=3
MAX_TEXT_SIZE_KB=50
ADMIN_TELEGRAM_IDS=your_admin_id1,your_admin_id2
```

#### Настройки AI:
```env
AI_PROVIDER=openai  # openai или claude
USE_UNIFIED_ANALYSIS=true
```

## 📈 Использование

### Для пользователей:

1. **Найдите бота** в Telegram: `@your_bot_name`
2. **Отправьте** `/start`
3. **Скопируйте** текст вакансии
4. **Вставьте** ваше резюме
5. **Получите** готовое письмо за 30-45 секунд!

### Команды:
- `/start` - Создать новое письмо
- `/help` - Справка по использованию  
- `/about` - О боте и возможностях
- `/premium` - Информация о Premium планах
- `/support` - Связаться с поддержкой
- `/privacy` - Политика конфиденциальности
- `/terms` - Пользовательское соглашение
- `/cancel` - Отменить текущий процесс

### Интерактивные функции:
- **Система оценок** - 👍 Нравится / 👎 Улучшить
- **Итерации писем** - до 3 улучшений по комментариям
- **Навигация** - удобные кнопки для перехода между разделами
- **Обратная связь** - оценка качества сгенерированных писем

## 🔬 AI Prompt Engineering

Бот использует специально разработанный промпт для максимальной персонализации:

```python
# Основной промпт v6.0 - 200+ строк тщательно протестированной логики
UNIFIED_ANALYSIS_PROMPT = """
Ты - эксперт по созданию сопроводительных писем, которые заставляют 
HR-менеджеров остановиться и подумать: "Черт, этот кандидат ТОЧНО 
понимает, что нам нужно"...
"""
```

**Особенности промпта:**
- 📝 **Структурированный анализ** - явные и скрытые потребности вакансии
- 🎯 **Конкретные совпадения** - поиск точных пересечений навыков
- 💡 **Эмоциональные триггеры** - адаптация под культуру компании
- 📊 **Цифры и результаты** - количественные достижения из резюме

## 📊 Аналитика и метрики

### Основные KPI:
- **Conversion Rate**: Start → Generated Letter
- **Generation Time**: Медианное время создания письма  
- **User Retention**: Возврат пользователей
- **AI Cost per Generation**: Стоимость токенов
- **Error Rate**: Процент неудачных генераций

### Схема базы данных:
```sql
users              -- Пользователи Telegram (с GDPR полями)
letter_sessions     -- Сессии генерации писем (с UUID)
letter_iterations   -- Итерации улучшения писем
subscriptions       -- Подписки пользователей (Free/Premium)
payments           -- История платежей и транзакций
user_events        -- События пользователей (детальная аналитика)
letter_feedback    -- Оценки писем (лайки/дизлайки)
openai_requests    -- Логи AI запросов (с метриками)
error_logs         -- Системные ошибки (с stack traces)
acquisition_channels -- UTM трекинг и реферралы
```

### Функции базы данных:
- **RLS (Row Level Security)** - защита данных на уровне PostgreSQL
- **Автоматические триггеры** - обновление updated_at полей
- **Аналитические представления** - готовые метрики и статистика
- **Атомарные операции** - безопасное обновление лимитов подписок

## 🚢 Production Deployment

Проект настроен для **Railway** deployment:

1. **Подключите** GitHub репозиторий к Railway
2. **Настройте** environment variables в Railway dashboard
3. **Deploy** происходит автоматически при push в main

### Railway Environment Variables:
```
# Основные
ENVIRONMENT=production
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...

# База данных и аналитика
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
ANALYTICS_ENABLED=true

# Система подписок
SUBSCRIPTIONS_ENABLED=true
FREE_LETTERS_LIMIT=3
PREMIUM_LETTERS_LIMIT=20

# Безопасность
RATE_LIMITING_ENABLED=true
RATE_LIMIT_COMMANDS_PER_MINUTE=5
RATE_LIMIT_AI_PER_5MIN=3
MAX_TEXT_SIZE_KB=50
ADMIN_TELEGRAM_IDS=123456789,987654321

# AI настройки
AI_PROVIDER=openai
USE_UNIFIED_ANALYSIS=true
```

## 🛠️ Разработка

### Структура проекта:
```
tg_soprovod/
├── handlers/           # Telegram bot handlers
│   └── simple_conversation_v6.py
├── services/          # AI services & analytics  
│   ├── ai_factory.py
│   ├── openai_service.py
│   ├── claude_service.py
│   ├── subscription_service.py
│   └── analytics_service.py
├── models/            # Data models
│   ├── subscription_models.py
│   ├── analytics_models.py
│   └── feedback_models.py
├── utils/             # Database & utilities
│   ├── database.py
│   ├── rate_limiter.py
│   ├── validators.py
│   └── keyboards.py
├── docs/              # Documentation
│   ├── architecture/
│   ├── legal/
│   └── releases/
├── migrations/        # Database migrations
├── tasks/            # Task specifications
├── config.py         # Configuration
├── main.py          # Bot entry point
├── Dockerfile       # Docker configuration
└── requirements.txt # Dependencies
```

### Добавление новых фич:

1. **AI сервисы** → `services/`
2. **Telegram handlers** → `handlers/`
3. **База данных** → `models/` + `supabase_schema.sql`
4. **Конфигурация** → `config.py`
5. **Безопасность** → `utils/rate_limiter.py`, `utils/validators.py`
6. **Миграции** → `migrations/`

## 🔒 Security

### Rate Limiting
Система защиты от злоупотреблений:
- **5 команд в минуту** - базовые команды
- **3 AI запроса в 5 минут** - генерация писем
- **Sliding window algorithm** - точный подсчет запросов
- **Admin bypass** - админы обходят лимиты

### Input Validation
- **Максимальный размер текста**: 50KB
- **Санитизация данных** - защита от вредоносного контента
- **Валидация команд** - проверка корректности входных данных

### Data Protection
- **GDPR compliance** - согласие на обработку ПД
- **RLS (Row Level Security)** - защита на уровне БД
- **Логирование** - детальные логи без чувствительных данных

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 💬 **Telegram**: Команда `/support` в боте
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/tg_soprovod/issues)
- 📋 **Документация**: [docs/](docs/) папка в репозитории
- 🔒 **Политика конфиденциальности**: Команда `/privacy` в боте

## 📈 Roadmap

### Планируемые функции:
- **Redis cache** - кэширование AI ответов
- **Webhook mode** - более быстрый отклик
- **Расширенная аналитика** - A/B тестирование промптов
- **API для интеграций** - подключение внешних сервисов
- **Мультиязычность** - поддержка английского языка

### Техническая roadmap:
- **Auto-scaling** - горизонтальное масштабирование
- **Real-time monitoring** - система алертов
- **Data retention policies** - автоматическая очистка данных
- **Advanced security** - WAF, IP filtering

---

**Made with ❤️ for job seekers worldwide**  
**v9.10 - Production-ready with security & monetization** 