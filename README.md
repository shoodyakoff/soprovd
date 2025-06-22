# Сопровод v4.0 🚀

**Умный генератор сопроводительных писем для Telegram**

Текущий бот: [@tvoi_soprovod_bot](https://t.me/tvoi_soprovod_bot)

## 🎯 Что делает бот

Сопровод анализирует вакансию и ваше резюме, а затем создает персональное сопроводительное письмо за 30 секунд. Простой поток: вакансия → резюме → готовое письмо.

## ✨ Особенности v4.0

- **Простота**: Убран выбор режимов и стилей - только один умный поток
- **Скорость**: Генерация письма за 30 секунд
- **Качество**: 3-этапная обработка через GPT для естественного текста
- **Умность**: Находит конкретные совпадения между вакансией и резюме

## 🏗️ Архитектура

```
Сопровод v4.0
├── handlers/
│   └── simple_conversation.py    # Единственный обработчик
├── services/
│   ├── openai_service.py        # Интеграция с OpenAI
│   └── smart_analyzer.py        # 3-этапная обработка
├── utils/
│   ├── keyboards.py             # Кнопки интерфейса
│   └── prompts.py               # Умные промпты
├── config.py                    # Конфигурация
└── main.py                      # Точка входа
```

## 🚀 Быстрый старт

### Локальная разработка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd tg_soprovod
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp env.example .env
# Отредактируйте .env файл с вашими токенами
```

5. **Запустите бота:**
```bash
python main.py
```

## 🌍 Деплой в Production

### Railway Deploy

1. **Создайте второй бот в BotFather:**
   - Отправьте `/newbot` в [@BotFather](https://t.me/BotFather)
   - Назовите: `Сопровод Production`
   - Username: `soprovod_prod_bot` (или любой доступный)

2. **Подключите GitHub к Railway:**
   - Зайдите на [railway.com](https://railway.com)
   - Создайте аккаунт и подключите GitHub
   - Выберите этот репозиторий для деплоя

3. **Настройте переменные окружения в Railway:**
   ```
   TELEGRAM_BOT_TOKEN=<prod_bot_token>
   OPENAI_API_KEY=<your_openai_key>
   OPENAI_TIMEOUT=120
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

4. **Автоматический деплой:**
   - Railway автоматически соберет Docker образ
   - Каждый push в main ветку = автоматический деплой

### Другие платформы

Проект готов для деплоя на любой платформе с поддержкой Docker:
- **Heroku**: `git push heroku main`
- **DigitalOcean App Platform**: Подключите GitHub репозиторий
- **AWS/GCP**: Используйте Dockerfile

## 🛠️ Разработка

### Структура переменных окружения

```bash
# Development
TELEGRAM_BOT_TOKEN=<dev_bot_token>
OPENAI_API_KEY=<your_api_key>
ENVIRONMENT=development

# Production  
TELEGRAM_BOT_TOKEN=<prod_bot_token>
OPENAI_API_KEY=<your_api_key>
ENVIRONMENT=production
```

### Тестирование

```bash
# Запуск тестов
python test_v4.py

# Проверка синтаксиса
python -m py_compile main.py
```

### Логирование

- **Development**: Логи в консоль + `bot.log`
- **Production**: Логи в Railway dashboard

## 📋 Требования

- Python 3.11+
- OpenAI API ключ
- Telegram Bot Token

## 🔧 Технологии

- **python-telegram-bot** - Telegram Bot API
- **openai** - GPT интеграция
- **asyncio** - Асинхронность
- **Docker** - Контейнеризация

## 📈 Мониторинг

В production доступны метрики:
- Количество запросов
- Время генерации писем
- Ошибки API
- Логи пользователей

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи в Railway dashboard
2. Убедитесь, что переменные окружения настроены
3. Проверьте, что OpenAI API ключ активен

---

**Сопровод v4.0** - Ваш умный помощник в поиске работы! 🎯 