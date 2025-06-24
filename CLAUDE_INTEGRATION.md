# Интеграция Claude API 🤖

## Обзор

Бот теперь поддерживает два AI-провайдера:
- **OpenAI GPT-4** (по умолчанию)
- **Anthropic Claude** (новый)

## Переключение провайдера

### В файле окружения (.env)
```bash
# Выбор провайдера
AI_PROVIDER=claude  # или 'openai'

# API ключи
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_claude_key
```

### Программно
```python
import os
os.environ['AI_PROVIDER'] = 'claude'

from services.ai_factory import get_ai_service
ai_service = get_ai_service()  # Вернет ClaudeService
```

## Архитектура

```
services/
├── ai_service.py      # Абстрактный интерфейс
├── ai_factory.py      # Фабрика для выбора провайдера
├── openai_service.py  # OpenAI реализация
├── claude_service.py  # Claude реализация
└── smart_analyzer.py  # Использует ai_factory
```

## API

Все AI-сервисы имеют единый интерфейс:

```python
# Универсальные методы
await ai_service.test_api_connection()
await ai_service.get_completion(prompt, temperature, max_tokens)
await ai_service.generate_personalized_letter(prompt)
```

## Модели

### OpenAI
- Основная: `gpt-4o`
- Fallback: `gpt-4`

### Claude
- Основная: `claude-3-5-sonnet-20241022`
- Fallback: `claude-3-haiku-20240307`

## Тестирование

```bash
# Тестируем интеграцию
python test_claude_integration.py

# Тестируем полный флоу
python test_v6_unified.py
```

## Конфигурация

Настройки для Claude в `config.py`:

```python
# Claude API
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
CLAUDE_FALLBACK_MODEL = "claude-3-haiku-20240307"
CLAUDE_TIMEOUT = 120
CLAUDE_MAX_TOKENS = 2000
CLAUDE_TEMPERATURE = 0.8
```

## Мониторинг

Аналитика работает для обоих провайдеров:
- Логирование запросов в Supabase
- Подсчет токенов
- Отслеживание ошибок

## Совместимость

✅ Полная обратная совместимость  
✅ Старый код работает без изменений  
✅ Переключение "на горячую" через переменную окружения 