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

1. АНАЛИЗ ВАКАНСИИ:
   - Извлеки ключевые требования (обязательные/желательные)
   - Выяви скрытые болевые точки компании 
   - Определи приоритеты работодателя
   - Проанализируй корпоративную культуру
   - Найди сигналы срочности и роста

2. АНАЛИЗ РЕЗЮМЕ:  
   - Извлеки опыт, навыки, достижения
   - Найди количественные метрики и результаты
   - Определи уникальные преимущества (USP)
   - Проанализируй карьерную траекторию
   - Выяви transferable skills

3. СТРАТЕГИЧЕСКОЕ СОПОСТАВЛЕНИЕ:
   - Найди прямые совпадения навыков
   - Определи переносимые навыки  
   - Выяви пробелы и способы их закрытия
   - Создай стратегию позиционирования
   - Подготовь конкретные отсылки к вакансии

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


HUMAN_WRITING_PROMPT = """Ты опытный специалист по написанию сопроводительных писем. 
Твоя задача - создать ЕСТЕСТВЕННОЕ, ЧЕЛОВЕЧНОЕ письмо без ИИ-штампов.

АНАЛИЗ ИЗ ПРЕДЫДУЩЕГО ЭТАПА:
{analysis_json}

ТРЕБОВАНИЯ К ПИСЬМУ:
1. ЧЕЛОВЕЧНОСТЬ: 
   ❌ Избегай: "хотел бы выразить заинтересованность", "рассмотрите мою кандидатуру"
   ✅ Используй: естественные обороты, личные инсайты

2. КОНКРЕТНОСТЬ:
   - Прямые отсылки к пунктам вакансии
   - Количественные метрики из опыта
   - Конкретные примеры решения проблем

3. СТРАТЕГИЧНОСТЬ:
   - Покажи понимание болевых точек компании
   - Позиционируй через уникальные преимущества
   - Предложи конкретную ценность

4. СТРУКТУРА:
   - Интригующее начало (не "пишу по поводу вакансии")
   - 2-3 абзаца с конкретными примерами  
   - Естественное завершение с next step

АНТИ-ИИ ПРАВИЛА:
- Никаких клише типа "идеально подхожу"
- Никаких формальных оборотов
- Живые переходы между абзацами
- Персональные инсайты и мотивация

СТИЛЬ: {writing_style}

Создай письмо, которое HR не отличит от написанного опытным человеком.
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
            raise
    
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
        
        # Этап 1: Глубокий анализ
        analysis = await self.deep_analyze(vacancy_text, resume_text)
        
        # Этап 2: Генерация письма
        letter = await self.generate_human_letter(analysis, style)
        
        # Этап 3: ДеИИ-фикация
        final_letter = await self.deai_text(letter)
        
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