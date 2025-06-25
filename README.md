# 🤖 Сопровод v6.0 - AI-powered Cover Letter Generator

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-Latest-blue.svg)](https://core.telegram.org/bots/api)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://platform.openai.com/)
[![Claude](https://img.shields.io/badge/Anthropic-Claude--3.5-purple.svg)](https://www.anthropic.com/)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-blueviolet.svg)](https://railway.app/)

> **AI-powered Telegram bot that generates personalized cover letters in 30-45 seconds**

Сопровод помогает соискателям создавать персонализированные сопроводительные письма, анализируя вакансию и резюме с помощью современных AI моделей.

## 🎯 Основные возможности

### ✨ **AI-анализ**
- **Умный анализ вакансий** - извлечение ключевых требований и болевых точек компании
- **Персонализация под резюме** - поиск точных совпадений навыков и опыта
- **Стилистическая адаптация** - профессиональный тон с человечными нотками

### 🚀 **Производительность**
- **30-45 секунд** - время генерации письма
- **Dual AI support** - OpenAI GPT-4 + Anthropic Claude
- **Асинхронная обработка** - не блокирует других пользователей
- **Smart fallbacks** - переключение между моделями при ошибках

### 📊 **Аналитика**
- **Real-time метрики** через Supabase
- **User journey tracking** - от start до готового письма
- **Performance monitoring** - время отклика, ошибки, использование токенов
- **A/B тестирование** алгоритмов генерации

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
- **Backend**: Python 3.9+, python-telegram-bot
- **AI Models**: OpenAI GPT-4, Anthropic Claude 3.5 Sonnet
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Railway
- **Monitoring**: Custom analytics + logging

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

#### Аналитика (опционально):
```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
ANALYTICS_ENABLED=true
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
- `/about` - О боте
- `/support` - Связаться с поддержкой
- `/cancel` - Отменить текущий процесс

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
users              -- Пользователи Telegram
letter_sessions     -- Сессии генерации писем  
user_events         -- События пользователей
openai_requests     -- Логи AI запросов
error_logs          -- Системные ошибки
```

## 🚢 Production Deployment

Проект настроен для **Railway** deployment:

1. **Подключите** GitHub репозиторий к Railway
2. **Настройте** environment variables в Railway dashboard
3. **Deploy** происходит автоматически при push в main

### Railway Environment Variables:
```
ENVIRONMENT=production
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
ANALYTICS_ENABLED=true
```

## 🛠️ Разработка

### Структура проекта:
```
tg_soprovod/
├── handlers/           # Telegram bot handlers
├── services/          # AI services & analytics  
├── models/            # Data models
├── utils/             # Database & utilities
├── config.py          # Configuration
├── main.py           # Bot entry point
└── requirements.txt   # Dependencies
```

### Добавление новых фич:

1. **AI сервисы** → `services/`
2. **Telegram handlers** → `handlers/`
3. **База данных** → `models/` + `supabase_schema.sql`
4. **Конфигурация** → `config.py`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 **Email**: support@soprovod.bot
- 💬 **Telegram**: @support_soprovod_bot
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/tg_soprovod/issues)

---

**Made with ❤️ for job seekers worldwide** 