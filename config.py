"""
Конфигурация для Telegram-бота Сопровод v4.0
Простой поток: вакансия → резюме → письмо
"""
import os
import logging
from dotenv import load_dotenv

# Настройка логирования ДО всего остального
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DEBUG: Принудительная отладка config.py
logger.info("🔧 CONFIG.PY LOADING START")
logger.info(f"🔧 Raw SUPABASE_URL from os.getenv: {os.getenv('SUPABASE_URL', 'NOT_FOUND')}")
logger.info(f"🔧 Raw SUPABASE_KEY from os.getenv: {os.getenv('SUPABASE_KEY', 'NOT_FOUND')[:20]}...")
logger.info(f"🔧 Raw ENVIRONMENT from os.getenv: {os.getenv('ENVIRONMENT', 'NOT_FOUND')}")
logger.info(f"🔧 Raw ANALYTICS_ENABLED from os.getenv: {os.getenv('ANALYTICS_ENABLED', 'NOT_FOUND')}")

# Загружаем переменные окружения
# Автоматически определяем окружение
environment = os.getenv('ENVIRONMENT', 'development')
logger.info(f"🔧 Detected environment: {environment}")

if environment == 'development':
    logger.info("🔧 Loading .env.dev for development")
    load_dotenv('.env.dev')  # Для разработки
elif environment == 'production':
    logger.info("🔧 Using Railway environment variables for production")
    # В продакшене Railway сам загружает переменные окружения
    pass  # Ничего не делаем, переменные уже доступны
else:
    logger.info(f"🔧 Unknown environment '{environment}', using development mode")
    load_dotenv('.env.dev')  # Безопасный fallback на dev

# Токены и ключи API
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Выбор AI-провайдера
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # 'openai' или 'claude'

# Настройки OpenAI
OPENAI_MODEL = "gpt-4o"
OPENAI_FALLBACK_MODEL = "gpt-4"
OPENAI_TIMEOUT = 60  # Оптимизирован для быстрой генерации
MAX_GENERATION_ATTEMPTS = 3

# Параметры генерации OpenAI
OPENAI_TEMPERATURE = 0.8  # Креативность (0.0-2.0)
OPENAI_TOP_P = 1.0        # Nucleus sampling (0.0-1.0)
OPENAI_PRESENCE_PENALTY = 0.3   # Штраф за повторы тем (-2.0 to 2.0)
OPENAI_FREQUENCY_PENALTY = 0.2  # Штраф за повторы слов (-2.0 to 2.0)

# Настройки Claude
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
CLAUDE_FALLBACK_MODEL = "claude-3-haiku-20240307"
CLAUDE_TIMEOUT = 60  # Оптимизирован для быстрой генерации
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

logger.info("🔧 RAILWAY ANALYTICS DEBUG:")
logger.info(f"   SUPABASE_URL: {SUPABASE_URL[:50] if SUPABASE_URL else 'NOT_FOUND'}...")
logger.info(f"   SUPABASE_KEY: {SUPABASE_KEY[:30] if SUPABASE_KEY else 'NOT_FOUND'}...")
logger.info(f"   ANALYTICS_ENABLED: {ANALYTICS_ENABLED}")
logger.info(f"   Environment: {environment}")

# Проверка аналитики при запуске
if ANALYTICS_ENABLED and (not SUPABASE_URL or not SUPABASE_KEY):
    logger.warning("⚠️  Warning: Analytics enabled but Supabase credentials missing")
    logger.warning(f"SUPABASE_URL exists: {bool(SUPABASE_URL)}")
    logger.warning(f"SUPABASE_KEY exists: {bool(SUPABASE_KEY)}")
    logger.warning(f"Environment: {environment}")
    logger.warning("🚨 RAILWAY: Check your environment variables in Railway dashboard!")
    ANALYTICS_ENABLED = False
elif ANALYTICS_ENABLED:
    logger.info(f"✅ Analytics configured: URL={SUPABASE_URL[:30] if SUPABASE_URL else 'None'}... KEY={SUPABASE_KEY[:20] if SUPABASE_KEY else 'None'}...")
else:
    logger.warning("⚠️ Analytics disabled by ANALYTICS_ENABLED=false")

# === НАСТРОЙКИ АЛГОРИТМА АНАЛИЗА v6.0 ===
USE_UNIFIED_ANALYSIS = os.getenv('USE_UNIFIED_ANALYSIS', 'true').lower() == 'true'

# Логируем выбранный алгоритм
if USE_UNIFIED_ANALYSIS:
    logger.info("🚀 Using new unified analysis algorithm v6.0")
else:
    logger.info("🔄 Using legacy multi-step analysis algorithm v5.0")

# Настройки системы подписок (НОВОЕ В V7.0)
SUBSCRIPTIONS_ENABLED = os.getenv('SUBSCRIPTIONS_ENABLED', 'false').lower() == 'true'
FREE_LETTERS_LIMIT = int(os.getenv('FREE_LETTERS_LIMIT', '3').split('#')[0].strip())  # 3 письма в месяц для free
PREMIUM_LETTERS_LIMIT = int(os.getenv('PREMIUM_LETTERS_LIMIT', '20').split('#')[0].strip())  # 20 писем в день для premium

# === НАСТРОЙКИ БЕЗОПАСНОСТИ v9.2 ===
RATE_LIMITING_ENABLED = os.getenv('RATE_LIMITING_ENABLED', 'true').lower() == 'true'
ADMIN_TELEGRAM_IDS = [int(x.strip()) for x in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if x.strip().isdigit()]

# Rate limiting лимиты
RATE_LIMIT_COMMANDS_PER_MINUTE = int(os.getenv('RATE_LIMIT_COMMANDS_PER_MINUTE', '5'))
RATE_LIMIT_AI_PER_5MIN = int(os.getenv('RATE_LIMIT_AI_PER_5MIN', '3'))
MAX_TEXT_SIZE_KB = int(os.getenv('MAX_TEXT_SIZE_KB', '50'))

logger.info("🔒 SECURITY SETTINGS v9.2:")
logger.info(f"   Rate limiting enabled: {RATE_LIMITING_ENABLED}")
logger.info(f"   Admin IDs: {ADMIN_TELEGRAM_IDS}")
logger.info(f"   Commands limit: {RATE_LIMIT_COMMANDS_PER_MINUTE}/min")
logger.info(f"   AI requests limit: {RATE_LIMIT_AI_PER_5MIN}/5min")
logger.info(f"   Max text size: {MAX_TEXT_SIZE_KB}KB") 