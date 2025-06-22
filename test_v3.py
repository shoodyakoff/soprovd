"""
Тест для v3.0 умного анализатора
"""
import asyncio
import logging
from services.smart_analyzer import SmartAnalyzer
from services.openai_service import OpenAIService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Тестовые данные
TEST_VACANCY = """
Senior Python Developer
Компания: TechCorp

Мы ищем опытного Python разработчика для работы над микросервисной архитектурой.

Требования:
- 5+ лет опыта Python разработки
- Опыт с Django/FastAPI
- Знание PostgreSQL, Redis
- Опыт работы с Docker, Kubernetes
- Понимание микросервисной архитектуры
- Английский язык от B2

Будет плюсом:
- Опыт с AWS/GCP
- Знание React
- Опыт team lead

Мы предлагаем:
- Зарплата от 200,000 руб
- Удаленная работа
- Гибкий график
- Медицинская страховка
"""

TEST_RESUME = """
Иван Петров
Python Developer, 6 лет опыта

Опыт работы:
- Senior Python Developer в StartupXYZ (2021-2024)
  • Разработал 15 микросервисов на FastAPI
  • Оптимизировал производительность на 40%
  • Внедрил CI/CD с Docker
  • Руководил командой из 3 разработчиков

- Middle Python Developer в WebAgency (2018-2021)
  • Разработка на Django
  • Интеграция с внешними API
  • Работа с PostgreSQL

Навыки:
- Python, Django, FastAPI
- PostgreSQL, Redis, MongoDB
- Docker, Kubernetes
- AWS (EC2, RDS, S3)
- Git, CI/CD
- Английский B2

Образование:
- МГУ, Факультет ВМК (2014-2018)
"""

async def test_smart_analyzer():
    """Тестирует работу умного анализатора"""
    logger.info("=== ТЕСТ УМНОГО АНАЛИЗАТОРА v3.0 ===")
    
    try:
        # Создаем сервисы
        openai_service = OpenAIService()
        analyzer = SmartAnalyzer(openai_service)
        
        # Проверяем API
        logger.info("🔍 Проверяю OpenAI API...")
        api_working = await openai_service.test_api_connection()
        if not api_working:
            logger.error("❌ OpenAI API не работает!")
            return
        
        logger.info("✅ OpenAI API работает")
        
        # Этап 1: Глубокий анализ
        logger.info("\n🧠 Этап 1: Глубокий анализ...")
        analysis = await analyzer.deep_analyze(TEST_VACANCY, TEST_RESUME)
        
        logger.info(f"📊 Результат анализа:")
        logger.info(f"- Уверенность: {analysis.get('confidence_score', 0):.2f}")
        logger.info(f"- Ключевые требования: {len(analysis.get('vacancy_analysis', {}).get('key_requirements', []))}")
        logger.info(f"- Навыки кандидата: {len(analysis.get('resume_analysis', {}).get('key_skills', []))}")
        
        # Этап 2: Генерация письма
        logger.info("\n✍️ Этап 2: Генерация человечного письма...")
        letter = await analyzer.generate_human_letter(analysis, "professional")
        
        logger.info(f"📝 Письмо сгенерировано: {len(letter)} символов")
        logger.info(f"Превью: {letter[:100]}...")
        
        # Этап 3: ДеИИ-фикация
        logger.info("\n🔧 Этап 3: ДеИИ-фикация...")
        final_letter = await analyzer.deai_text(letter)
        
        logger.info(f"✨ Финальное письмо: {len(final_letter)} символов")
        
        # Полный флоу
        logger.info("\n🚀 Тест полного флоу...")
        full_letter = await analyzer.generate_full_letter(
            TEST_VACANCY, 
            TEST_RESUME, 
            "professional"
        )
        
        logger.info("\n=== РЕЗУЛЬТАТ ===")
        logger.info(f"Длина письма: {len(full_letter)} символов")
        logger.info("Финальное письмо:")
        logger.info("-" * 50)
        logger.info(full_letter)
        logger.info("-" * 50)
        
        # Проверка на ИИ-штампы
        ai_patterns = [
            "хотел бы выразить заинтересованность",
            "рассмотрите мою кандидатуру",
            "идеально подхожу для позиции",
            "уникальная комбинация навыков",
            "с нетерпением жду"
        ]
        
        found_patterns = [p for p in ai_patterns if p.lower() in full_letter.lower()]
        
        if found_patterns:
            logger.warning(f"⚠️ Найдены ИИ-штампы: {found_patterns}")
        else:
            logger.info("✅ ИИ-штампы не обнаружены!")
        
        logger.info("\n🎉 Тест завершен успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_smart_analyzer()) 