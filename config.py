"""
Конфигурация для Telegram-бота Сопровод v4.0
Простой поток: вакансия → резюме → письмо
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токены и ключи API
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Настройки OpenAI
OPENAI_MODEL = "gpt-4o"
OPENAI_FALLBACK_MODEL = "gpt-4"
OPENAI_TIMEOUT = 120  # Увеличен для сложных анализов
MAX_GENERATION_ATTEMPTS = 3

# Параметры генерации OpenAI
OPENAI_TEMPERATURE = 0.8  # Креативность (0.0-2.0)
OPENAI_TOP_P = 1.0        # Nucleus sampling (0.0-1.0)
OPENAI_PRESENCE_PENALTY = 0.3   # Штраф за повторы тем (-2.0 to 2.0)
OPENAI_FREQUENCY_PENALTY = 0.2  # Штраф за повторы слов (-2.0 to 2.0)

# Минимальная длина ответа для проверки полноты
MIN_RESPONSE_LENGTH = 100 