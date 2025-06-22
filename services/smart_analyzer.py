"""
Умный анализатор v3.0 - глубокий анализ через GPT промпты
Простое решение без велосипедов
"""
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# ============ НОВЫЕ ПРОМПТЫ ДЛЯ 4-ЭТАПНОГО АНАЛИЗА ============

VACANCY_ANALYSIS_PROMPT = """
ЗАДАЧА: Структурированный анализ вакансии для точного сопоставления с резюме.

АЛГОРИТМ АНАЛИЗА ВАКАНСИИ:

1. ЖЁСТКИЕ ТРЕБОВАНИЯ (hard requirements):
   - Обязательные технические навыки/инструменты
   - Конкретный опыт работы (годы, сферы)
   - Обязательное образование/сертификаты
   - Языки программирования/платформы

2. МЯГКИЕ ТРЕБОВАНИЯ (soft requirements):
   - Желательные навыки
   - Дополнительный опыт
   - Личностные качества
   - Методологии работы

3. КЛЮЧЕВЫЕ БИЗНЕС-ЗАДАЧИ:
   - Что конкретно нужно делать на позиции
   - Какие проблемы решать
   - Какие результаты ожидаются

4. КОНТЕКСТ КОМПАНИИ:
   - Размер компании/команды
   - Отрасль и специфика
   - Этап развития (стартап/корпорация)
   - Корпоративная культура

5. КЛЮЧЕВЫЕ СЛОВА И ТЕРМИНЫ:
   - Специфичные технологии
   - Отраслевые термины
   - Методологии и процессы
   - Инструменты и платформы

ФОРМАТ ОТВЕТА: JSON
{{
  "hard_requirements": [
    {{
      "requirement": "конкретное требование",
      "importance": "critical/high/medium",
      "specificity": "specific/general",
      "keywords": ["ключевые", "слова"]
    }}
  ],
  "soft_requirements": [...],
  "business_tasks": [...],
  "company_context": {{}},
  "key_terms": [...]
}}

ВАКАНСИЯ: {vacancy_text}
"""

RESUME_ANALYSIS_PROMPT = """
ЗАДАЧА: Структурированное извлечение навыков и опыта из резюме.

АЛГОРИТМ АНАЛИЗА РЕЗЮМЕ:

1. ТЕХНИЧЕСКИЕ НАВЫКИ:
   - Конкретные технологии/инструменты
   - Уровень владения (если указан)
   - Контекст использования
   - Результаты применения

2. ПРОФЕССИОНАЛЬНЫЙ ОПЫТ:
   - Конкретные роли и обязанности
   - Достижения с цифрами
   - Проекты и их результаты
   - Индустрии и сферы

3. БИЗНЕС-РЕЗУЛЬТАТЫ:
   - Конкретные метрики и KPI
   - Улучшения процессов
   - Решённые проблемы
   - Созданная ценность

4. ОБРАЗОВАНИЕ И СЕРТИФИКАТЫ:
   - Формальное образование
   - Профессиональные сертификаты
   - Курсы и тренинги

5. ДОПОЛНИТЕЛЬНЫЕ АКТИВНОСТИ:
   - Волонтёрство
   - Проекты в свободное время
   - Публикации/выступления
   - Хобби, связанные с работой

ФОРМАТ ОТВЕТА: JSON
{{
  "technical_skills": [
    {{
      "skill": "конкретный навык",
      "level": "beginner/intermediate/advanced/expert",
      "context": "где и как использовал",
      "results": "какие результаты достиг",
      "keywords": ["ключевые", "слова"]
    }}
  ],
  "experience": [...],
  "achievements": [...],
  "education": [...],
  "additional": [...]
}}

РЕЗЮМЕ: {resume_text}
"""

MATCHING_ANALYSIS_PROMPT = """
ЗАДАЧА: Найти ТОЧНЫЕ совпадения между требованиями вакансии и навыками в резюме.

КРИТИЧЕСКИ ВАЖНО:
1. Ищи КОНКРЕТНЫЕ совпадения, а не общие темы
2. Сопоставляй ТОЧНЫЕ термины и технологии
3. Не путай смежные отрасли (PropTech ≠ TravelTech)
4. Каждое совпадение должно иметь ДОКАЗАТЕЛЬСТВО из резюме

АЛГОРИТМ СОПОСТАВЛЕНИЯ:

1. ПРЯМЫЕ СОВПАДЕНИЯ (exact matches) - ОДИНАКОВЫЕ термины/процессы:
   Примеры: "OKR" в вакансии = "OKR" в резюме
           "управление бэклогом" = "работа с бэклогом"
           "UX-исследования" = "UX-тесты"
           "декомпозиция задач" = "декомпозиция на этапы"

2. СИЛЬНЫЕ СОВПАДЕНИЯ (strong matches) - СМЕЖНЫЕ навыки с доказательствами:
   Примеры: "B2B продукты" ← "B2B-решение PRYSM"
           "аналитическое мышление" ← "дерево метрик, NPV анализ"
           "запуск под ключ" ← "запустил MVP за 4 месяца"

3. СЛАБЫЕ СОВПАДЕНИЯ (weak matches) - ОБЩИЕ навыки:
   Примеры: "коммуникация", "работа в команде"

4. КРИТИЧЕСКИЕ ПРОБЕЛЫ (gaps) - ОТСУТСТВУЮЩИЕ жесткие требования:
   Примеры: Нет опыта в TravelTech (есть только PropTech)
           Нет прямого опыта А/В тестирования

5. КОМПЕНСИРУЮЩИЕ ФАКТОРЫ:
   Как смежный опыт может покрыть пробелы

ПРАВИЛА СОПОСТАВЛЕНИЯ:
- КОНКРЕТНОСТЬ > общность: "OKR квартальные" лучше чем "планирование"
- ДОКАЗАТЕЛЬСТВА: каждое совпадение подкрепляй ФАКТОМ из резюме
- ЧЕСТНОСТЬ: если требования нет - признай пробел, но покажи смежный опыт
- РЕЛЕВАНТНОСТЬ: показывай КАК опыт применим к новой роли

ФОРМАТ ОТВЕТА: JSON
{{
  "exact_matches": [
    {{
      "vacancy_requirement": "точное требование из вакансии",
      "resume_match": "точное совпадение в резюме", 
      "evidence": "конкретная цитата/факт из резюме",
      "relevance_score": 0.95,
      "bridge_explanation": "как именно этот опыт применим"
    }}
  ],
  "strong_matches": [
    {{
      "vacancy_requirement": "требование",
      "resume_match": "смежный опыт",
      "evidence": "доказательство",
      "relevance_score": 0.8,
      "bridge_explanation": "логическая связь"
    }}
  ],
  "weak_matches": [...],
  "critical_gaps": [
    {{
      "missing_requirement": "что отсутствует",
      "compensating_factor": "что может компенсировать",
      "mitigation_strategy": "как подать отсутствие опыта"
    }}
  ],
  "unique_advantages": [
    {{
      "advantage": "уникальное преимущество",
      "value_to_employer": "ценность для работодателя"
    }}
  ]
}}

АНАЛИЗ ВАКАНСИИ: {vacancy_analysis}
АНАЛИЗ РЕЗЮМЕ: {resume_analysis}
"""

LETTER_GENERATION_PROMPT = """
ЗАДАЧА: Написать сопроводительное письмо как СВЯЗНУЮ ИСТОРИЮ, а не список фактов.

У тебя есть ТОЧНЫЙ анализ совпадений между вакансией и резюме.

КРИТИЧЕСКАЯ ПРОБЛЕМА ТЕКУЩИХ ПИСЕМ:
❌ "У меня есть X. Также у меня есть Y. Кроме того, я делал Z."
✅ "Когда я работал с X, это научило меня Y, что позволило достичь Z."

ПРИНЦИПЫ СВЯЗНОЙ ИСТОРИИ:
1. ЛОГИЧЕСКАЯ ЦЕПОЧКА: каждый навык/результат вытекает из предыдущего
2. ПРИЧИННО-СЛЕДСТВЕННЫЕ СВЯЗИ: "благодаря этому", "это позволило", "поэтому"
3. ЕДИНАЯ НАРРАТИВА: все опыты работают на одну главную мысль
4. ПРОГРЕССИЯ: от простого к сложному, показать развитие

СВЯЗУЮЩИЕ СЛОВА И КОНСТРУКЦИИ:
- "Это научило меня..."
- "Благодаря опыту в X, я смог..."
- "Именно поэтому..."
- "Развивая навыки в X, я перешел к Y..."
- "Этот опыт подготовил меня к..."
- "Комбинируя X и Y, я достиг..."

АЛГОРИТМ СОЗДАНИЯ ИСТОРИИ:

1. НАЙДИ ГЛАВНУЮ ТЕМУ (сквозную линию):
   Что объединяет все твои навыки? Например:
   - "Системный подход к продуктовому развитию"
   - "Эволюция от тактических задач к стратегическим"
   - "Путь от анализа к запуску продуктов"

2. ВЫСТРОЙ ЛОГИЧЕСКУЮ ПОСЛЕДОВАТЕЛЬНОСТЬ:
   - Что было ОСНОВОЙ (фундаментальный навык)
   - Что РАЗВИЛОСЬ из этого (следующий уровень)  
   - К чему это ПРИВЕЛО (конечный результат)
   
   Пример: Анализ метрик → Понимание продукта → Управление командой → Запуск MVP

3. СОЗДАЙ ПРИЧИННО-СЛЕДСТВЕННЫЕ СВЯЗИ:
   Вместо: "Я управлял бэклогом. Я запустил MVP."
   Пиши: "Управляя бэклогом команды из 20 человек, я научился видеть продукт целиком, что позволило успешно запустить MVP за 4 месяца."

4. СТРУКТУРА ПИСЬМА С ЛОГИКОЙ:

   АБЗАЦ 1 - Зацепка + фундамент (30-40 слов):
   "Ваша вакансия привлекла тем, что [конкретная причина]. В [компании] я прошел путь от [начальная точка] до [результат], что дало мне [ключевой навык]."

   АБЗАЦ 2 - Развитие навыков (50-60 слов):
   "Именно [базовый опыт] научил меня [следующий навык]. Благодаря этому я смог [конкретное достижение], что привело к [результат с цифрами]."

   АБЗАЦ 3 - Применение и результат (40-50 слов):
   "Комбинируя [навык 1] и [навык 2], я [ключевое достижение]. Этот опыт показал, что [инсайт/понимание], именно поэтому [как это применимо к новой роли]."

   АБЗАЦ 4 - Призыв к действию (20-30 слов):
   "Готов обсудить, как этот опыт поможет [конкретная ценность для компании]. Когда удобно встретиться?"

5. ПРИМЕРЫ ЛОГИЧЕСКИХ СВЯЗОК:

   ПЛОХО: "Я работал с OKR. Я управлял бэклогом. Я запустил MVP."
   
   ХОРОШО: "Внедряя OKR в команде, я понял важность четкого планирования. Это помогло мне структурировать управление бэклогом так, что команда из 20 человек работала синхронно. Именно такой системный подход позволил запустить MVP всего за 4 месяца."

6. ПРОВЕРКА СВЯЗНОСТИ:
   - Можно ли убрать любое предложение без потери смысла? (❌ должно быть НЕТ)
   - Есть ли логическая цепочка от первого к последнему предложению? (✅ должно быть ДА)
   - Понятно ли, КАК каждый опыт повлиял на следующий? (✅ должно быть ДА)

ВХОДНЫЕ ДАННЫЕ:
{matching_analysis}

ПРИМЕР СВЯЗНОЙ ИСТОРИИ:
"Работа с продуктовыми метриками в банке научила меня видеть влияние каждого изменения на бизнес. Именно поэтому, когда перешел к управлению командой, я смог выстроить процессы так, что мы улучшили ключевые показатели на 15%. Этот системный подход к продукту помог запустить MVP за рекордные 4 месяца - команда понимала, к какому результату мы идем."

Напиши СВЯЗНУЮ ИСТОРИЮ, а не список фактов. Каждое предложение должно ЛОГИЧЕСКИ вытекать из предыдущего.
"""

# ============ СТАРЫЕ ПРОМПТЫ (для совместимости) ============

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
    
    async def generate_full_analysis_and_letter(
        self,
        vacancy_text: str,
        resume_text: str,
        style: str = "professional"
    ) -> Dict[str, str]:
        """
        Новый 4-этапный анализ + генерация письма
        
        Args:
            vacancy_text: Текст вакансии
            resume_text: Текст резюме
            style: Стиль письма
            
        Returns:
            Dict с письмом и анализом совпадений
        """
        logger.info("🚀 Запускаю новый 4-этапный флоу...")
        logger.info(f"📊 Входные данные: вакансия={len(vacancy_text)} символов, резюме={len(resume_text)} символов")
        
        # ЭТАП 1: Анализ вакансии
        logger.info("🔍 ЭТАП 1: Анализ вакансии...")
        vacancy_analysis = await self.analyze_vacancy_structured(vacancy_text)
        logger.info("✅ ЭТАП 1 завершен")
        
        # ЭТАП 2: Анализ резюме  
        logger.info("👤 ЭТАП 2: Анализ резюме...")
        resume_analysis = await self.analyze_resume_structured(resume_text)
        logger.info("✅ ЭТАП 2 завершен")
        
        # ЭТАП 3: Анализ совпадений
        logger.info("⚡ ЭТАП 3: Анализ совпадений...")
        matching_analysis = await self.detailed_matching_analysis(
            vacancy_analysis, resume_analysis
        )
        logger.info("✅ ЭТАП 3 завершен")
        
        # ЭТАП 4: Генерация письма
        logger.info("✍️ ЭТАП 4: Генерация письма...")
        letter = await self.generate_letter_from_analysis(matching_analysis)
        logger.info(f"✅ ЭТАП 4 завершен. Длина письма: {len(letter)} символов")
        
        # ЭТАП 5: Де-ИИ-фикация
        logger.info("🔧 ЭТАП 5: Де-ИИ-фикация...")
        final_letter = await self.deai_text(letter)
        logger.info(f"✅ ЭТАП 5 завершен. Финальная длина: {len(final_letter)} символов")
        
        # Форматируем анализ для пользователя
        formatted_analysis = self.format_matching_summary(matching_analysis)
        
        logger.info("🎉 Новый 4-этапный флоу завершен!")
        return {
            'letter': final_letter,
            'analysis': formatted_analysis
        }
    
    async def analyze_vacancy_structured(self, vacancy_text: str) -> Dict[str, Any]:
        """
        ЭТАП 1: Структурированный анализ вакансии
        """
        prompt = VACANCY_ANALYSIS_PROMPT.format(vacancy_text=vacancy_text)
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.3,  # Для структурированного анализа
                max_tokens=2000
            )
            
            if not response:
                logger.error("❌ Получен пустой ответ при анализе вакансии")
                return self._get_fallback_vacancy_analysis()
            
            # Парсим JSON
            return self._parse_json_safely(response, "vacancy_analysis")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа вакансии: {e}")
            return self._get_fallback_vacancy_analysis()
    
    async def analyze_resume_structured(self, resume_text: str) -> Dict[str, Any]:
        """
        ЭТАП 2: Структурированный анализ резюме
        """
        prompt = RESUME_ANALYSIS_PROMPT.format(resume_text=resume_text)
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            if not response:
                logger.error("❌ Получен пустой ответ при анализе резюме")
                return self._get_fallback_resume_analysis()
            
            return self._parse_json_safely(response, "resume_analysis")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа резюме: {e}")
            return self._get_fallback_resume_analysis()
    
    async def detailed_matching_analysis(
        self, 
        vacancy_analysis: Dict[str, Any], 
        resume_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ЭТАП 3: Детальный анализ совпадений
        """
        prompt = MATCHING_ANALYSIS_PROMPT.format(
            vacancy_analysis=json.dumps(vacancy_analysis, ensure_ascii=False, indent=2),
            resume_analysis=json.dumps(resume_analysis, ensure_ascii=False, indent=2)
        )
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.4,
                max_tokens=2000
            )
            
            if not response:
                logger.error("❌ Получен пустой ответ при анализе совпадений")
                return self._get_fallback_matching_analysis()
            
            return self._parse_json_safely(response, "matching_analysis")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа совпадений: {e}")
            return self._get_fallback_matching_analysis()
    
    async def generate_letter_from_analysis(self, matching_analysis: Dict[str, Any]) -> str:
        """
        ЭТАП 4: Генерация письма на основе анализа
        """
        prompt = LETTER_GENERATION_PROMPT.format(
            matching_analysis=json.dumps(matching_analysis, ensure_ascii=False, indent=2)
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
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации письма: {e}")
            raise
    
    def format_matching_summary(self, matching_analysis: Dict[str, Any]) -> str:
        """
        Форматирование анализа совпадений для пользователя
        """
        try:
            summary = "📊 АНАЛИЗ СОВПАДЕНИЙ ВАКАНСИИ И РЕЗЮМЕ\n\n"
            
            # Прямые совпадения
            exact_matches = matching_analysis.get('exact_matches', [])
            if exact_matches:
                summary += "✅ ПРЯМЫЕ СОВПАДЕНИЯ:\n"
                for match in exact_matches[:5]:  # Показываем топ-5
                    req = match.get('vacancy_requirement', 'Требование')
                    evidence = match.get('evidence', 'Опыт подтвержден')
                    summary += f"• {req} → {evidence}\n"
                summary += "\n"
            
            # Сильные совпадения
            strong_matches = matching_analysis.get('strong_matches', [])
            if strong_matches:
                summary += "⚡ СИЛЬНЫЕ СОВПАДЕНИЯ:\n"
                for match in strong_matches[:3]:
                    req = match.get('vacancy_requirement', 'Требование')
                    evidence = match.get('evidence', 'Смежный опыт')
                    summary += f"• {req} → {evidence}\n"
                summary += "\n"
            
            # Пробелы
            gaps = matching_analysis.get('critical_gaps', [])
            if gaps:
                summary += "⚠️ ОБЛАСТИ ДЛЯ РАЗВИТИЯ:\n"
                for gap in gaps[:3]:
                    if isinstance(gap, str):
                        summary += f"• {gap}\n"
                    elif isinstance(gap, dict):
                        summary += f"• {gap.get('missing_requirement', 'Пробел в навыках')}\n"
                summary += "\n"
            
            # Уникальные преимущества
            advantages = matching_analysis.get('unique_advantages', [])
            if advantages:
                summary += "🎯 УНИКАЛЬНЫЕ ПРЕИМУЩЕСТВА:\n"
                for advantage in advantages[:3]:
                    if isinstance(advantage, str):
                        summary += f"• {advantage}\n"
                    elif isinstance(advantage, dict):
                        summary += f"• {advantage.get('advantage', 'Дополнительная ценность')}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования анализа: {e}")
            return "📊 Анализ совпадений выполнен, но возникла ошибка форматирования."

    async def generate_full_letter(
        self,
        vacancy_text: str,
        resume_text: str,
        style: str = "professional"
    ) -> str:
        """
        Старый метод - оставлен для обратной совместимости
        """
        logger.info("🔄 Используется старый метод generate_full_letter для совместимости")
        result = await self.generate_full_analysis_and_letter(vacancy_text, resume_text, style)
        return result['letter']
    
    def _parse_json_safely(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Безопасный парсинг JSON ответа от GPT"""
        try:
            # Очищаем ответ от markdown блоков
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # убираем ```json
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # убираем ```
            cleaned_response = cleaned_response.strip()
            
            # Парсим JSON
            parsed = json.loads(cleaned_response)
            logger.info(f"✅ JSON успешно распарсен для {analysis_type}")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON для {analysis_type}: {e}")
            logger.error(f"Ответ GPT: {response[:500]}...")
            
            # Возвращаем fallback в зависимости от типа анализа
            if analysis_type == "vacancy_analysis":
                return self._get_fallback_vacancy_analysis()
            elif analysis_type == "resume_analysis":
                return self._get_fallback_resume_analysis()
            elif analysis_type == "matching_analysis":
                return self._get_fallback_matching_analysis()
            else:
                return self._get_fallback_analysis()
    
    def _get_fallback_vacancy_analysis(self) -> Dict[str, Any]:
        """Fallback анализ вакансии"""
        return {
            "hard_requirements": [
                {
                    "requirement": "профессиональный опыт",
                    "importance": "high",
                    "specificity": "general",
                    "keywords": ["опыт", "навыки"]
                }
            ],
            "soft_requirements": [
                {
                    "requirement": "коммуникативные навыки",
                    "importance": "medium",
                    "specificity": "general",
                    "keywords": ["коммуникация"]
                }
            ],
            "business_tasks": ["выполнение профессиональных задач"],
            "company_context": {
                "size": "средняя компания",
                "industry": "различные отрасли",
                "culture": "профессиональная"
            },
            "key_terms": ["опыт", "навыки", "профессионализм"]
        }
    
    def _get_fallback_resume_analysis(self) -> Dict[str, Any]:
        """Fallback анализ резюме"""
        return {
            "technical_skills": [
                {
                    "skill": "профессиональные навыки",
                    "level": "intermediate",
                    "context": "рабочая деятельность",
                    "results": "успешное выполнение задач",
                    "keywords": ["навыки", "опыт"]
                }
            ],
            "experience": ["профессиональный опыт работы"],
            "achievements": ["выполнение рабочих задач"],
            "education": ["профессиональное образование"],
            "additional": ["дополнительные активности"]
        }
    
    def _get_fallback_matching_analysis(self) -> Dict[str, Any]:
        """Fallback анализ совпадений"""
        return {
            "exact_matches": [
                {
                    "vacancy_requirement": "профессиональный опыт",
                    "resume_match": "имеется опыт работы",
                    "evidence": "подтверждается резюме",
                    "relevance_score": 0.95,
                    "bridge_explanation": "как именно этот опыт применим"
                }
            ],
            "strong_matches": [
                {
                    "vacancy_requirement": "профессиональные навыки",
                    "resume_match": "релевантные компетенции",
                    "evidence": "описано в резюме",
                    "relevance_score": 0.8,
                    "bridge_explanation": "логическая связь"
                }
            ],
            "weak_matches": [],
            "critical_gaps": [],
            "unique_advantages": ["профессиональная экспертиза"]
        }

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback структура анализа на случай ошибок (старый формат)"""
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
    Удобная функция для полного флоу (обратная совместимость)
    
    Args:
        vacancy_text: Текст вакансии
        resume_text: Текст резюме  
        style: Стиль письма
        openai_service: Сервис OpenAI (опционально)
        
    Returns:
        Готовое сопроводительное письмо
    """
    analyzer = get_analyzer(openai_service)
    result = await analyzer.generate_full_analysis_and_letter(vacancy_text, resume_text, style)
    return result['letter']


async def analyze_and_generate_with_analysis(
    vacancy_text: str,
    resume_text: str,
    style: str = "professional",
    openai_service=None
) -> Dict[str, str]:
    """
    Новая функция с анализом совпадений
    
    Args:
        vacancy_text: Текст вакансии
        resume_text: Текст резюме  
        style: Стиль письма
        openai_service: Сервис OpenAI (опционально)
        
    Returns:
        Dict с письмом и анализом совпадений
    """
    analyzer = get_analyzer(openai_service)
    return await analyzer.generate_full_analysis_and_letter(vacancy_text, resume_text, style) 