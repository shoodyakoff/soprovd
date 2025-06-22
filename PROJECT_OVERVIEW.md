 # 🤖 LetterGenius - Архитектура и Описание Проекта

## 📋 Общее Описание

**LetterGenius** - это Telegram-бот для автоматической генерации персонализированных сопроводительных писем с использованием ИИ. Бот анализирует профессию и уровень кандидата, предлагает оптимальный стиль письма и генерирует качественный контент.

### 🎯 Основные Возможности
- **Классический режим**: Быстрая генерация с выбором стиля
- **Персонализированный режим**: Анализ профиля + автоматический подбор стиля
- **Поддержка OpenAI API**: GPT-4o/GPT-4 для генерации текста
- **Многоуровневая система стилей**: От формального до креативного

---

## 🏗️ Архитектура Проекта

```
tg_soprovod/
├── main.py                              # 🚀 Точка входа, настройка ConversationHandler
├── config.py                            # ⚙️ Конфигурация, константы, состояния
├── requirements.txt                     # 📦 Зависимости Python
├── README.md                           # 📖 Пользовательская документация
├── 
├── handlers/                           # 🎮 Обработчики пользовательских действий
│   ├── __init__.py
│   ├── start.py                        # 🎬 Команда /start, меню выбора режима
│   ├── conversation.py                 # 💬 Классический режим диалога
│   ├── personalized_conversation.py   # 🎯 Персонализированный режим
│   └── callback.py                     # 🔘 Обработка inline-кнопок
├── 
├── services/                           # 🧠 Бизнес-логика и внешние сервисы
│   ├── __init__.py
│   ├── openai_service.py              # 🤖 Интеграция с OpenAI API
│   ├── profile_analyzer.py            # 🔍 Анализ профессии и уровня
│   └── personalized_prompt.py         # 📝 Генерация персонализированных промптов
├── 
├── models/                            # 📊 Модели данных и определения
│   ├── __init__.py
│   ├── profile_models.py              # 🏷️ Dataclasses для профилей
│   └── style_definitions.py           # 🎨 Матрица стилей и ключевые слова
├── 
└── utils/                             # 🛠️ Вспомогательные утилиты
    ├── __init__.py
    ├── keyboards.py                   # ⌨️ Inline-клавиатуры
    └── prompts.py                     # 📋 Шаблоны промптов
```

---

## 🔄 Пользовательские Флоу

### 🎬 Общий Старт
```
/start → handlers/start.py
├── Показ приветствия
├── Создание inline-клавиатуры с выбором режима
└── Переход в состояние CHOOSING_MODE
```

### 🤖 Классический Режим
```
Выбор "Быстрый режим" → handlers/callback.py → handle_mode_choice()
├── Состояние: WAITING_JOB_DESCRIPTION
├── Пользователь отправляет описание вакансии → handlers/conversation.py
├── Состояние: WAITING_RESUME  
├── Пользователь отправляет резюме → handlers/conversation.py
├── Состояние: WAITING_STYLE_CHOICE
├── Показ кнопок выбора стиля → utils/keyboards.py
├── Пользователь выбирает стиль → handlers/callback.py
├── Генерация письма → services/openai_service.py
└── Отправка результата
```

### 🎯 Персонализированный Режим
```
Выбор "Персонализированный" → handlers/callback.py → handle_mode_choice()
├── Состояние: PERS_WAITING_JOB (10)
├── Пользователь отправляет описание → handlers/personalized_conversation.py
├── Состояние: PERS_WAITING_RESUME (11)
├── Пользователь отправляет резюме → handlers/personalized_conversation.py
├── 🔍 АНАЛИЗ ПРОФИЛЯ:
│   ├── services/profile_analyzer.py → analyze_profile()
│   ├── Поиск ключевых слов → models/style_definitions.py
│   ├── Определение профессии и уровня
│   └── Подбор стиля по матрице STYLE_MAP
├── Состояние: PERS_WAITING_STYLE (13)
├── Показ результатов анализа + кнопки подтверждения
├── Генерация персонализированного промпта → services/personalized_prompt.py
├── Генерация письма → services/openai_service.py
└── Отправка результата
```

---

## 📁 Подробное Описание Компонентов

### 🚀 main.py
**Назначение**: Точка входа приложения
- Настройка логирования
- Создание Application и ConversationHandler
- Определение состояний и их обработчиков
- Запуск polling

**Ключевые состояния**:
- `CHOOSING_MODE = 0` - Выбор режима работы
- `WAITING_JOB_DESCRIPTION = 1` - Ожидание описания вакансии (классический)
- `WAITING_RESUME = 2` - Ожидание резюме (классический)
- `WAITING_STYLE_CHOICE = 3` - Выбор стиля (классический)
- `PERS_WAITING_JOB = 10` - Ожидание описания (персонализированный)
- `PERS_WAITING_RESUME = 11` - Ожидание резюме (персонализированный)
- `PERS_WAITING_STYLE = 13` - Подтверждение стиля (персонализированный)

### ⚙️ config.py
**Назначение**: Центральная конфигурация
- Загрузка переменных окружения (.env)
- Константы состояний ConversationHandler
- Настройки OpenAI (модели, параметры генерации)
- Определения стилей писем

### 🎮 handlers/
#### start.py
- Обработка команды `/start`
- Создание приветственного сообщения
- Формирование меню выбора режима

#### conversation.py (Классический режим)
- `handle_job_description()` - Получение описания вакансии
- `handle_resume()` - Получение резюме и переход к выбору стиля
- `handle_text_in_style_choice()` - Обработка текста вместо кнопок
- `generate_letter_content()` - Генерация письма через OpenAI
- `cancel()` - Отмена процесса

#### personalized_conversation.py (Персонализированный режим)
- `receive_job_description()` - Получение описания вакансии
- `receive_resume()` - Получение резюме + запуск анализа профиля
- `send_analysis_results()` - Показ результатов анализа
- `handle_style_choice()` - Обработка выбора/подтверждения стиля
- Константы состояний: 10-14 (чтобы не конфликтовать с классическим режимом)

#### callback.py
- `handle_mode_choice()` - Выбор между классическим/персонализированным режимом
- `handle_style_callback()` - Выбор стиля в классическом режиме
- Обработка всех inline-кнопок

### 🧠 services/
#### openai_service.py
**Назначение**: Интеграция с OpenAI API
- `OpenAIService` - Основной класс для работы с API
- `test_api_connection()` - Проверка подключения при старте
- `generate_cover_letter()` - Генерация письма (классический режим)
- `generate_personalized_letter()` - Генерация с кастомным промптом
- `_make_openai_request()` - Низкоуровневые запросы к API
- `_is_response_complete()` - Проверка полноты ответа
- Поддержка fallback модели (GPT-4 если GPT-4o недоступен)
- Глобальный экземпляр `openai_service`

#### profile_analyzer.py
**Назначение**: Анализ профессии и уровня кандидата
- `analyze_profile()` - Главная функция анализа
- `_analyze_profession()` - Определение профессии по ключевым словам
- `_analyze_level()` - Определение уровня (Junior/Middle/Senior/Lead/C-Level)
- `_calculate_confidence()` - Расчет уверенности в анализе
- `_get_suggested_style()` - Подбор стиля по матрице STYLE_MAP
- Возвращает `AnalyzedProfile` с результатами

#### personalized_prompt.py
**Назначение**: Генерация персонализированных промптов
- `generate_personalized_prompt()` - Создание промпта на основе анализа
- `_get_style_instructions()` - Инструкции для конкретного стиля
- `_get_profession_context()` - Контекст для профессии
- `_get_level_context()` - Контекст для уровня
- Адаптация промпта под результаты анализа профиля

### 📊 models/
#### profile_models.py
**Назначение**: Модели данных
```python
@dataclass
class SuggestedStyle:
    style_name: str           # Название стиля
    confidence_score: float   # Уверенность в подборе
    tone_description: str     # Описание тона
    temperature: float        # Параметр для OpenAI

@dataclass  
class AnalyzedProfile:
    profession: str           # Определенная профессия
    level: str               # Уровень (junior/middle/senior/etc)
    confidence_score: float   # Общая уверенность анализа
    suggested_style: SuggestedStyle  # Рекомендуемый стиль
    keywords_found: List[str] # Найденные ключевые слова
```

#### style_definitions.py
**Назначение**: Бизнес-логика стилей и анализа
- `PROFESSION_KEYWORDS` - Ключевые слова для определения профессий
- `LEVEL_KEYWORDS` - Ключевые слова для определения уровня
- `STYLE_MAP` - Матрица профессия×уровень → стиль
- `DEFAULT_STYLES` - Определения стилей с параметрами
- `STYLE_DESCRIPTIONS` - Описания стилей для пользователя

### 🛠️ utils/
#### keyboards.py
**Назначение**: Создание inline-клавиатур
- `get_mode_selection_keyboard()` - Кнопки выбора режима
- `get_style_keyboard()` - Кнопки выбора стиля
- `get_style_confirmation_keyboard()` - Кнопки подтверждения в персонализированном режиме

#### prompts.py
**Назначение**: Шаблоны промптов для OpenAI
- `get_cover_letter_prompt()` - Базовый промпт для классического режима
- Шаблоны для разных стилей (neutral, bold, formal)
- Инструкции по структуре и тону письма

---

## 🔧 Технические Детали

### 🗂️ Управление Состояниями
Используется `ConversationHandler` из python-telegram-bot:
- **Классический режим**: состояния 0-4
- **Персонализированный режим**: состояния 10-14
- Разделение предотвращает конфликты между режимами

### 🤖 Интеграция с OpenAI
- **Модели**: GPT-4o (основная), GPT-4 (fallback)
- **Параметры**: Temperature, top_p, presence_penalty, frequency_penalty
- **Retry-логика**: До 3 попыток при ошибках
- **Проверка полноты**: Валидация сгенерированного контента

### 🔍 Алгоритм Анализа Профиля
1. **Поиск ключевых слов** в описании вакансии и резюме
2. **Подсчет совпадений** для каждой профессии/уровня
3. **Расчет confidence score** на основе количества совпадений
4. **Подбор стиля** по матрице STYLE_MAP
5. **Fallback** на neutral стиль при низкой уверенности

### 📝 Система Стилей
- **Neutral**: Сбалансированный, профессиональный (temp: 0.7)
- **Bold**: Уверенный, амбициозный (temp: 0.8)  
- **Formal**: Строгий, официальный (temp: 0.6)
- **Creative**: Креативный, неформальный (temp: 0.9)

---

## 🚀 Запуск и Развертывание

### Переменные Окружения (.env)
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
```

### Команды
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python main.py
```

### Команды Бота
- `/start` - Начало работы, выбор режима
- `/cancel` - Отмена текущего процесса
- `/help` - Справка по командам

---

## 🔄 Логика Переходов Состояний

```
START → CHOOSING_MODE
├── mode_classic → WAITING_JOB_DESCRIPTION → WAITING_RESUME → WAITING_STYLE_CHOICE → END
└── mode_personalized → PERS_WAITING_JOB → PERS_WAITING_RESUME → PERS_WAITING_STYLE → END
```

## 📊 Матрица Стилей (Примеры)

| Профессия / Уровень | Junior | Middle | Senior | Lead | C-Level |
|---------------------|--------|--------|--------|------|---------|
| Product Manager     | neutral| neutral| neutral| bold | bold    |
| UX/UI Designer      | creative| creative| creative| creative| formal|
| Frontend Developer  | neutral| neutral| bold   | bold | formal  |
| Backend Developer   | formal | formal | formal | bold | formal  |

---

Этот файл содержит полную архитектуру проекта и может использоваться как справочник при работе с ИИ-помощниками для объяснения структуры и логики LetterGenius.