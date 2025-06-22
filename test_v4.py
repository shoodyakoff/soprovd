"""
Тестирование LetterGenius v4.0
Простой поток: вакансия → резюме → письмо
"""
import asyncio
import logging
from services.smart_analyzer import analyze_and_generate

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Тестовые данные
VACANCY_TEXT = """
Senior Python Developer
Мы ищем опытного Python разработчика для работы над высоконагруженными веб-сервисами.

Требования:
- Опыт работы с Python 3.8+ не менее 5 лет
- Знание Django/FastAPI
- Опыт работы с PostgreSQL, Redis
- Знание Docker, Kubernetes
- Опыт работы с микросервисной архитектурой
- Английский язык B2+

Обязанности:
- Разработка и поддержка веб-сервисов
- Проектирование архитектуры
- Код-ревью
- Менторинг junior разработчиков

Условия:
- Зарплата от 300,000 руб
- Гибкий график
- Удаленная работа
- ДМС
"""

RESUME_TEXT = """
Иван Петров
Senior Python Developer

Опыт работы: 6 лет

Ключевые навыки:
- Python 3.9, Django, FastAPI
- PostgreSQL, MongoDB, Redis
- Docker, Kubernetes, AWS
- Git, CI/CD
- Английский B2

Опыт работы:
2020-2024: Senior Python Developer в Tech Corp
- Разработал микросервисную архитектуру для e-commerce платформы
- Оптимизировал производительность API на 40%
- Руководил командой из 3 junior разработчиков
- Внедрил автоматизированное тестирование

2018-2020: Middle Python Developer в StartupX
- Создал RESTful API для мобильного приложения
- Работал с высоконагруженными системами (1M+ запросов/день)
- Интегрировал платежные системы

Образование:
МГУ, Факультет ВМК, 2018
"""

async def test_v4_generation():
    """
    Тестирует полный цикл генерации v4.0
    """
    logger.info("🚀 Тестирование LetterGenius v4.0")
    logger.info("=" * 50)
    
    try:
        logger.info("📝 Генерирую письмо...")
        
        cover_letter = await analyze_and_generate(
            vacancy_text=VACANCY_TEXT,
            resume_text=RESUME_TEXT,
            style="professional"  # Фиксированный стиль в v4.0
        )
        
        logger.info("✅ Письмо успешно сгенерировано!")
        logger.info("=" * 50)
        logger.info("📄 РЕЗУЛЬТАТ:")
        logger.info("=" * 50)
        print(cover_letter)
        logger.info("=" * 50)
        
        # Проверки качества
        if len(cover_letter) < 200:
            logger.warning("⚠️  Письмо слишком короткое")
        
        if "AI" in cover_letter or "ИИ" in cover_letter:
            logger.warning("⚠️  Обнаружены ИИ-штампы")
        
        # Проверка ключевых элементов
        checks = [
            ("Python" in cover_letter, "Упоминание Python"),
            ("опыт" in cover_letter.lower(), "Упоминание опыта"),
            ("команд" in cover_letter.lower(), "Упоминание работы в команде"),
            (len(cover_letter.split()) > 100, "Достаточная длина")
        ]
        
        logger.info("🔍 Проверки качества:")
        for check, description in checks:
            status = "✅" if check else "❌"
            logger.info(f"{status} {description}")
        
        logger.info("🎉 Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_v4_generation()) 