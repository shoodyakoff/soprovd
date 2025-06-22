"""
Умный анализатор v3.0 - глубокий анализ через GPT промпты
Простое решение без велосипедов
"""
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# ============ ПРОМПТЫ ============

DEEP_ANALYSIS_PROMPT = """Ты эксперт-аналитик по HR и рекрутингу. Проведи глубокий анализ вакансии и резюме.

ЗАДАЧА: Пошагово проанализируй и верни структурированный JSON

ЭТАПЫ АНАЛИЗА:

1. АНАЛИЗ ВАКАНСИИ - ищи КОНКРЕТНЫЕ требования:
   - Технологии и инструменты (Python, React, Figma, Tableau, etc.)
   - Методологии (Scrum, Agile, Design Thinking, OKR, etc.)
   - Специфичные навыки (A/B тестирование, SQL, лидерство команд, etc.)
   - Отрасли и продукты (fintech, e-commerce, SaaS, etc.)
   - Количественные требования (опыт X лет, команда Y человек)

2. АНАЛИЗ РЕЗЮМЕ - ищи ТОЧНЫЕ совпадения:
   - Те же технологии и инструменты
   - Те же методологии и процессы  
   - Конкретные достижения с цифрами
   - Релевантный отраслевой опыт
   - Схожие проектные роли

3. ПОИСК ПРЯМЫХ СОВПАДЕНИЙ:
   - Сопоставь требование 1:1 с опытом
   - Игнорируй общие навыки (коммуникация, ответственность)
   - Фокусируйся на специфичных совпадениях
   - Найди уникальные пересечения (редкие технологии, нишевый опыт)
   - Выяви самые сильные совпадения для позиционирования

ФОРМАТ ОТВЕТА: строго JSON без дополнительного текста
{{
  "vacancy_analysis": {{
    "key_requirements": ["требование1", "требование2"],
    "pain_points": ["проблема1", "проблема2"], 
    "priorities": ["приоритет1", "приоритет2"],
    "company_culture": "описание культуры",
    "urgency_signals": ["сигнал1", "сигнал2"],
    "hidden_needs": ["скрытая потребность1", "скрытая потребность2"]
  }},
  "resume_analysis": {{
    "key_skills": ["навык1", "навык2"],
    "achievements": ["достижение с метриками1", "достижение с метриками2"],
    "unique_advantages": ["УТП1", "УТП2"],
    "career_trajectory": "описание карьерного пути",
    "transferable_skills": ["переносимый навык1", "переносимый навык2"]
  }},
  "matching_strategy": {{
    "direct_matches": ["совпадение1", "совпадение2"],
    "skill_gaps": ["пробел1", "пробел2"],
    "positioning": "стратегия позиционирования",
    "value_proposition": "ценностное предложение",
    "specific_references": ["конкретная отсылка к вакансии1", "конкретная отсылка к вакансии2"]
  }},
  "confidence_score": 0.85
}}

ВАКАНСИЯ:
{vacancy_text}

РЕЗЮМЕ:
{resume_text}"""


HUMAN_WRITING_PROMPT = """Ты пишешь сопроводительные письма для кандидатов на работу. Твоя задача - создать персонализированное письмо, которое цепляет HR за конкретные совпадения между требованиями и опытом.

АНАЛИЗ ИЗ ПРЕДЫДУЩЕГО ЭТАПА:
{analysis_json}

ЭТАП 1: Анализ совпадений
• Выпиши 5-7 ключевых требований из вакансии
• Для каждого найди КОНКРЕТНОЕ совпадение в резюме (не общие слова, а специфичные навыки/опыт/инструменты)
• Если точного совпадения нет - пропусти это требование

ЭТАП 2: Создай "мосты" между требованиями и опытом
Формат: "Вам важно X → У меня есть конкретно Y"

Примеры ПРАВИЛЬНЫХ совпадений:
• "управление проектами по методологии Scrum" → "3 года работы со Scrum в команде из 15 человек"
• "анализ пользовательского поведения" → "настройка Google Analytics и проведение A/B тестов"
• "работа с базами данных MySQL" → "оптимизация запросов в MySQL, сокращение времени отклика на 40%"
• "OKR и целеполагание" → "внедрил систему OKR в команде из 12 человек, достигли 95% целей"
• "стратегическое планирование" → "разработал 3-летнюю продуктовую стратегию, увеличившую DAU на 150%"

Примеры НЕПРАВИЛЬНЫХ совпадений:
• "коммуникативные навыки" → "работал в команде" (слишком общее)
• "опыт продаж" → "увеличил выручку" (нет прямой связи с продажами)

ЭТАП 3: Структура письма

Абзац 1: Мотивация/зацепка
• Почему именно эта компания/продукт привлекает
• Можно упомянуть 1 самое сильное совпадение

Абзац 2: Основные совпадения
• 2-3 самых сильных совпадения с конкретными результатами
• Каждое совпадение = требование + твой опыт + результат с цифрами

Абзац 3: Дополнительная экспертиза
• Еще 2-3 совпадения, показывающие глубину знаний
• Менее очевидные, но важные навыки

Абзац 4: Призыв к действию
• Конкретное предложение встречи/звонка
• Временные рамки

ПРАВИЛА:
• Убери воду и клише ("с полной отдачей", "это то что искал")
• Используй только конкретные цифры и факты
• Максимум 4 абзаца
• Тон - профессиональный, но живой
• СТИЛЬ: {writing_style}

Теперь напиши сопроводительное письмо на основе предоставленной вакансии и резюме.
Напиши ТОЛЬКО текст письма без комментариев."""


DEAI_PROMPT = """Проверь текст на ИИ-штампы и сделай его более человечным.

ДЕТЕКТИРУЕМЫЕ ПАТТЕРНЫ:
- "хотел бы выразить заинтересованность" 
- "рассмотрите мою кандидатуру"
- "идеально подхожу для позиции"
- "уникальная комбинация навыков"
- "готов внести значительный вклад"
- "буду рад возможности обсудить"
- "с нетерпением жду вашего ответа"
- "страстно увлечен"
- "также стоит упомянуть"
- "кроме того, хочу отметить"

ЗАМЕНИ НА ЧЕЛОВЕЧНЫЕ ВАРИАНТЫ:
- "заметил вашу вакансию и понял - это то, что искал"
- "ваше объявление привлекло внимание"
- "думаю, мой опыт здесь пригодится"
- "в [компания] мне довелось"
- "когда работал над [проект], столкнулся с"
- "за X лет работы в [сфера] научился"

ПРАВИЛА УЛУЧШЕНИЯ:
1. Убери все формальные обороты
2. Добавь живые детали и контекст
3. Замени общие фразы на конкретные примеры
4. Сделай переходы между предложениями естественными
5. Добавь эмоциональную составляющую, но без пафоса

ТЕКСТ ДЛЯ ПРОВЕРКИ:
{text}

Верни только улучшенный текст без дополнительных комментариев и пометок."""


# ============ ОСНОВНОЙ КЛАСС ============

class SmartAnalyzer:
    """Умный анализатор на основе GPT промптов"""
    
    def __init__(self, openai_service):
        self.openai = openai_service
        
    async def deep_analyze(self, vacancy_text: str, resume_text: str) -> Dict[str, Any]:
        """
        Глубокий анализ через GPT
        
        Args:
            vacancy_text: Текст вакансии
            resume_text: Текст резюме
            
        Returns:
            Dict с результатами анализа
        """
        logger.info("🔍 Начинаю глубокий анализ через GPT...")
        
        prompt = DEEP_ANALYSIS_PROMPT.format(
            vacancy_text=vacancy_text,
            resume_text=resume_text
        )
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.3,  # Для структурированного анализа
                max_tokens=2000
            )
            
            if not response:
                logger.error("❌ Получен пустой ответ от GPT")
                return self._get_fallback_analysis()
            
            # Очищаем ответ от markdown блоков
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # убираем ```json
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # убираем ```
            cleaned_response = cleaned_response.strip()
            
            # Парсим JSON
            analysis = json.loads(cleaned_response)
            logger.info(f"✅ Анализ завершен, уверенность: {analysis.get('confidence_score', 0):.2f}")
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            logger.error(f"Ответ GPT: {response}")
            # Возвращаем базовую структуру
            return self._get_fallback_analysis()
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            logger.error(f"🔍 Контекст: вакансия={len(vacancy_text)} символов, резюме={len(resume_text)} символов")
            # Возвращаем fallback вместо raise для стабильности
            logger.warning("🔄 Переключаюсь на fallback анализ...")
            return self._get_fallback_analysis()
    
    async def generate_human_letter(
        self, 
        analysis: Dict[str, Any], 
        style: str = "professional"
    ) -> str:
        """
        Генерация человечного письма
        
        Args:
            analysis: Результат глубокого анализа
            style: Стиль письма
            
        Returns:
            Готовое письмо
        """
        logger.info("✍️ Генерирую человечное письмо...")
        
        prompt = HUMAN_WRITING_PROMPT.format(
            analysis_json=json.dumps(analysis, ensure_ascii=False, indent=2),
            writing_style=style
        )
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.7,  # Для креативности
                max_tokens=1500
            )
            
            if not response:
                logger.error("❌ Получен пустой ответ при генерации письма")
                raise Exception("Пустой ответ от GPT")
            
            logger.info("✅ Письмо сгенерировано")
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации письма: {e}")
            raise
    
    async def deai_text(self, text: str) -> str:
        """
        ДеИИ-фикация текста - убираем ИИ-штампы
        
        Args:
            text: Исходный текст
            
        Returns:
            Улучшенный человечный текст
        """
        logger.info("🔧 Применяю деИИ-фикацию...")
        
        prompt = DEAI_PROMPT.format(text=text)
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1500
            )
            
            if not response:
                logger.warning("❌ Получен пустой ответ при деИИ-фикации, возвращаю исходный текст")
                return text
            
            logger.info("✅ ДеИИ-фикация завершена")
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка деИИ-фикации: {e}")
            # Возвращаем исходный текст, если что-то пошло не так
            return text
    
    async def generate_full_letter(
        self,
        vacancy_text: str,
        resume_text: str,
        style: str = "professional"
    ) -> str:
        """
        Полный флоу: анализ + генерация + деИИ-фикация
        
        Args:
            vacancy_text: Текст вакансии
            resume_text: Текст резюме
            style: Стиль письма
            
        Returns:
            Готовое человечное письмо
        """
        logger.info("🚀 Запускаю полный флоу v3.0...")
        logger.info(f"📊 Входные данные: вакансия={len(vacancy_text)} символов, резюме={len(resume_text)} символов")
        
        # Этап 1: Глубокий анализ
        logger.info("🔍 ЭТАП 1: Начинаю глубокий анализ...")
        analysis = await self.deep_analyze(vacancy_text, resume_text)
        logger.info(f"✅ ЭТАП 1 завершен. Confidence: {analysis.get('confidence_score', 0):.2f}")
        
        # Этап 2: Генерация письма
        logger.info("✍️ ЭТАП 2: Начинаю генерацию письма...")
        letter = await self.generate_human_letter(analysis, style)
        logger.info(f"✅ ЭТАП 2 завершен. Длина письма: {len(letter)} символов")
        
        # Этап 3: ДеИИ-фикация
        logger.info("🔧 ЭТАП 3: Начинаю деИИ-фикацию...")
        final_letter = await self.deai_text(letter)
        logger.info(f"✅ ЭТАП 3 завершен. Финальная длина: {len(final_letter)} символов")
        
        logger.info("🎉 Полный флоу завершен!")
        return final_letter
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback структура анализа на случай ошибок"""
        return {
            "vacancy_analysis": {
                "key_requirements": ["Опыт работы", "Профессиональные навыки"],
                "pain_points": ["Потребность в квалифицированном специалисте"],
                "priorities": ["Качество выполнения задач"],
                "company_culture": "Профессиональная среда",
                "urgency_signals": [],
                "hidden_needs": ["Надежный исполнитель"]
            },
            "resume_analysis": {
                "key_skills": ["Профессиональные навыки", "Опыт работы"],
                "achievements": ["Успешное выполнение задач"],
                "unique_advantages": ["Профессиональная экспертиза"],
                "career_trajectory": "Стабильное развитие",
                "transferable_skills": ["Аналитическое мышление"]
            },
            "matching_strategy": {
                "direct_matches": ["Соответствие требованиям"],
                "skill_gaps": [],
                "positioning": "Квалифицированный специалист",
                "value_proposition": "Профессиональная экспертиза и опыт",
                "specific_references": ["Релевантный опыт работы"]
            },
            "confidence_score": 0.6
        }


# ============ ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ============

_analyzer_instance: Optional[SmartAnalyzer] = None


def get_analyzer(openai_service=None) -> SmartAnalyzer:
    """Получить глобальный экземпляр анализатора"""
    global _analyzer_instance
    
    if _analyzer_instance is None:
        if openai_service is None:
            from services.openai_service import openai_service as default_service
            openai_service = default_service
        _analyzer_instance = SmartAnalyzer(openai_service)
    
    return _analyzer_instance


async def analyze_and_generate(
    vacancy_text: str,
    resume_text: str,
    style: str = "professional",
    openai_service=None
) -> str:
    """
    Удобная функция для полного флоу
    
    Args:
        vacancy_text: Текст вакансии
        resume_text: Текст резюме  
        style: Стиль письма
        openai_service: Сервис OpenAI (опционально)
        
    Returns:
        Готовое сопроводительное письмо
    """
    analyzer = get_analyzer(openai_service)
    return await analyzer.generate_full_letter(vacancy_text, resume_text, style) 