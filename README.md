# 🤖 AI Сопроводительное письмо - Telegram Bot

> **Telegram бот для генерации персонализированных сопроводительных писем с использованием GPT-4o и Claude-3.5**

## 🎯 Проблема и решение

**Проблема:** Соискатели тратят часы на написание уникальных сопроводительных писем для каждой вакансии  
**Решение:** AI бот создает персонализированное письмо за 30 секунд, анализируя вакансию и резюме

## 💼 Бизнес-модель

### 🆓 **Бесплатная версия**
- 3 письма в месяц
- Базовый GPT-4o
- Основная функциональность

### 💎 **Premium подписка** 
- 20 писем в день
- GPT-4o + Claude-3.5 (двойная проверка)
- Приоритетная генерация
- **199₽/месяц**

## 🚀 Быстрый старт

```bash
# Клонирование
git clone <repo-url>
cd tg_soprovod

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных среды
cp env.example .env
# Заполнить .env файл

# Запуск
python main.py
```

## 📁 Структура проекта

```
tg_soprovod/
├── 📋 releases/                    # Система релизов
│   ├── templates/                  # Шаблоны для задач
│   ├── v9_master_release/         # Релиз v9 (PROD)
│   ├── v10_ykassa_integration/    # Релиз v10 (PAUSE)
│   └── current/                   # Текущие задачи
├── 📚 docs/                        # Документация
│   ├── CJM.md                     # Customer Journey Map
│   └── ARCHITECTURE.md            # Техническая архитектура
├── 🗂️ handlers/                   # Telegram handlers
├── 🛠️ services/                   # Бизнес-логика
├── 📊 models/                     # Модели данных
├── 🔧 utils/                      # Утилиты
└── 🗄️ backup/                     # Резервные копии
```

## 🏗️ Техническая архитектура

- **Backend:** Python 3.11+, python-telegram-bot
- **AI:** OpenAI GPT-4o + Anthropic Claude-3.5 (dual provider)
- **Database:** Supabase (PostgreSQL)
- **Deployment:** Railway (auto-deploy)
- **Security:** Rate limiting, PII sanitization, GDPR compliance

## 🔄 Customer Journey

1. **Вход:** `/start` → объяснение процесса
2. **Сбор данных:** Вакансия → Резюме  
3. **Генерация:** AI анализ (30-45 сек) → готовое письмо
4. **Оценка:** ❤️ Нравится / 👎 Улучшить / 🔄 Еще раз
5. **Монетизация:** Premium touchpoints при лимитах

## 📊 Текущий статус

- **Релиз v9.0:** ✅ Завершен и развернут в продакшене
- **Релиз v10.0:** ⏸️ На паузе (ЮKassa интеграция)
- **Пользователи:** Стартап стадия, подготовка к масштабированию
- **Архитектура:** Готова к 1000+ пользователей

## 📈 Ключевые метрики

- **Time to Value:** 30 секунд от старта до письма
- **Completion Rate:** % пользователей получивших письмо  
- **Premium Conversion:** % конверсии в платную подписку
- **Retention:** % возвращений для новых писем

## 🛠️ Development

### Система задач
- Все задачи хранятся в `releases/`
- Каждый релиз содержит `tasks/` и `migrations/`
- Шаблоны в `releases/templates/`

### Документация
- **CJM:** `docs/CJM.md` - пользовательский путь
- **Architecture:** `docs/ARCHITECTURE.md` - техническая архитектура  
- **Releases:** README в каждом релизе

## 📞 Поддержка

- **Telegram:** @shoodyakoff
- **Email:** s.hoodyakoff@yandex.ru  
- **Issues:** GitHub Issues

---

**Создано с ❤️ для поиска работы мечты** 