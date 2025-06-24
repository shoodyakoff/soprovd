"""
Конфигурация для Telegram-бота Сопровод v4.0
Простой поток: вакансия → резюме → письмо
"""
import os
from dotenv import load_dotenv

# DEBUG: Принудительная отладка config.py
print("🔧 CONFIG.PY LOADING START")
print(f"🔧 Raw SUPABASE_URL from os.getenv: {os.getenv('SUPABASE_URL', 'NOT_FOUND')}")
print(f"🔧 Raw SUPABASE_KEY from os.getenv: {os.getenv('SUPABASE_KEY', 'NOT_FOUND')[:20]}...")
print(f"🔧 Raw ENVIRONMENT from os.getenv: {os.getenv('ENVIRONMENT', 'NOT_FOUND')}")

# Загружаем переменные окружения
# Автоматически определяем окружение
environment = os.getenv('ENVIRONMENT', 'development')
if environment == 'development':
    load_dotenv('.env.dev')  # Для разработки
elif environment == 'production':
    # В продакшене Railway сам загружает переменные окружения
    pass  # Ничего не делаем, переменные уже доступны
else:
    load_dotenv('.env')      # Fallback

# Токены и ключи API
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Выбор AI-провайдера
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # 'openai' или 'claude'

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

# Настройки Claude
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
CLAUDE_FALLBACK_MODEL = "claude-3-haiku-20240307"
CLAUDE_TIMEOUT = 120
CLAUDE_MAX_TOKENS = 2000

# Параметры генерации Claude
CLAUDE_TEMPERATURE = 0.8

# Минимальная длина ответа для проверки полноты
MIN_RESPONSE_LENGTH = 100

# === НАСТРОЙКИ АНАЛИТИКИ ===
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') 
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true'

# Проверка аналитики при запуске
if ANALYTICS_ENABLED and (not SUPABASE_URL or not SUPABASE_KEY):
    print("⚠️  Warning: Analytics enabled but Supabase credentials missing")
    print(f"SUPABASE_URL exists: {bool(SUPABASE_URL)}")
    print(f"SUPABASE_KEY exists: {bool(SUPABASE_KEY)}")
    print(f"Environment: {environment}")
    ANALYTICS_ENABLED = False
else:
    print(f"✅ Analytics configured: URL={SUPABASE_URL[:30] if SUPABASE_URL else 'None'}... KEY={SUPABASE_KEY[:20] if SUPABASE_KEY else 'None'}...")

# === НАСТРОЙКИ АЛГОРИТМА АНАЛИЗА v6.0 ===
USE_UNIFIED_ANALYSIS = os.getenv('USE_UNIFIED_ANALYSIS', 'true').lower() == 'true'

# Логируем выбранный алгоритм
if USE_UNIFIED_ANALYSIS:
    print("🚀 Using new unified analysis algorithm v6.0")
else:
    print("🔄 Using legacy multi-step analysis algorithm v5.0") 