"""
Умный анализатор v6.0 - единый анализ через GPT
Революционная архитектура: 1 запрос вместо 4, быстрее в 2-3 раза

🚨🚨🚨 DEPRECATED WARNING 🚨🚨🚨
Этот файл УСТАРЕЛ и содержит legacy код!

ИСПОЛЬЗУЙТЕ ВМЕСТО НЕГО: services/smart_analyzer_v6.py

ПРИЧИНЫ ЗАМЕНЫ:
- Этот файл: 956 строк legacy кода с backward compatibility
- v6.py файл: 400+ строк только актуальной логики
- Дублирование функциональности создает путаницу
- v6.py имеет встроенную де-ИИ-фикацию и кэширование
- v6.py оптимизирован для производительности

ПЛАН МИГРАЦИИ:
1. Замените импорты: 
   from services.smart_analyzer import ... → from services.smart_analyzer_v6 import ...
2. Протестируйте работу
3. Удалите этот файл после полной миграции

🚨🚨🚨 DEPRECATED WARNING 🚨🚨🚨
"""
import json
import logging
import os
import re
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# ============ ПРОМПТЫ v6.0 ============

UNIFIED_ANALYSIS_PROMPT = """
ЗАДАЧА: Проанализируй вакансию и резюме ОДНОВРЕМЕННО, найди точные совпадения и напиши сопроводительное письмо.

КРИТИЧЕСКИ ВАЖНО:
1. Анализируй ОБА текста параллельно, не по отдельности
2. Ищи КОНКРЕТНЫЕ совпадения, а не общие темы
3. Каждое совпадение подкрепляй ТОЧНОЙ ЦИТАТОЙ из резюме
4. НЕ СМЕШИВАЙ разные компании и проекты в одну историю
5. Письмо должно быть СВЯЗНОЙ ИСТОРИЕЙ, а не списком фактов

АЛГОРИТМ ПОИСКА СОВПАДЕНИЙ:
1. ПРОЧИТАЙ вакансию и выдели ВСЕ ключевые требования (включая методологии, инструменты, процессы)
2. Для КАЖДОГО требования ищи в резюме:
   - ПРЯМЫЕ совпадения (одинаковые термины: "OKR" = "OKR")
   - СМЕЖНЫЕ совпадения (похожие процессы)
   - ОТСУТСТВИЕ (если требования нет в резюме)
3. Для каждого совпадения найди конкретную цитату-доказательство
4. Оцени силу каждого совпадения (0.0-1.0)

ПРАВИЛА КОНТЕКСТА:
- НЕ объединяй опыт из разных компаний в одно предложение
- Четко разделяй достижения по местам работы
- Если упоминаешь цифры - указывай контекст (какая компания)
- Пример: "В PRYSM запустил MVP за 4 месяца. В Т-Банке сохранил продажи на XXX млн NPV"

ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ ДЛЯ ПОИСКА:
- OKR (если есть в вакансии)
- A/B тестирование (если есть в вакансии)  
- Scrum/Agile (если есть в вакансии)
- Конкретные технологии и инструменты
- Отраслевой опыт (TravelTech, HotelTech, PropTech, FinTech)
- Управление командами (размер команды)
- Запуск продуктов
- Работа с метриками

ПРИНЦИПЫ СВЯЗНОЙ ИСТОРИИ:
- Каждое предложение логически вытекает из предыдущего
- Используй связки: "благодаря этому", "именно поэтому", "это позволило"
- Покажи ЭВОЛЮЦИЮ навыков: от простого к сложному
- Конкретные цифры и результаты С УКАЗАНИЕМ КОНТЕКСТА

СТРУКТУРА ПИСЬМА (ОБЯЗАТЕЛЬНО 4 АБЗАЦА С ПЕРЕНОСАМИ):
Абзац 1 (30-40 слов): Зацепка + самое сильное совпадение (ОДНА компания)

Абзац 2 (50-60 слов): Развитие навыков через логическую цепочку (можно другая компания)

Абзац 3 (40-50 слов): Применение опыта и результаты

Абзац 4 (20-30 слов): Призыв к действию

БЛОК ВОПРОСОВ ДЛЯ УЛУЧШЕНИЯ:
Если в вакансии есть требования, которых НЕТ в резюме, предложи 3-5 уточняющих вопросов:
- "Есть ли у вас опыт с A/B тестированием?"
- "Работали ли вы с OKR методологией?"
- "Какой у вас опыт в TravelTech индустрии?"

ВАКАНСИЯ:
{vacancy_text}

РЕЗЮМЕ:
{resume_text}

СТИЛЬ ПИСЬМА: {style}

ФОРМАТ ОТВЕТА: строго JSON без дополнительного текста
{{
  "matches": [
    {{
      "requirement": "конкретное требование из вакансии",
      "evidence": "найденный опыт в резюме",
      "quote": "точная цитата из резюме",
      "company_context": "в какой компании было",
      "strength": 0.95,
      "explanation": "почему это совпадение важно"
    }}
  ],
  "missing_requirements": [
    {{
      "requirement": "что отсутствует в резюме",
      "importance": "high/medium/low",
      "suggested_question": "вопрос для уточнения"
    }}
  ],
  "clarifying_questions": [
    "Вопрос 1 для улучшения резюме",
    "Вопрос 2 для сбора контекста",
    "Вопрос 3 для выявления скрытого опыта"
  ],
  "letter": "АБЗАЦ 1: текст первого абзаца\\n\\nАБЗАЦ 2: текст второго абзаца\\n\\nАБЗАЦ 3: текст третьего абзаца\\n\\nАБЗАЦ 4: текст четвертого абзаца",
  "confidence": 0.85
}}
"""

CONTEXTUAL_MATCHING_PROMPT = """
ЗАДАЧА: Найди ТОЧНЫЕ совпадения между вакансией и резюме.

ПРАВИЛА:
1. Анализируй ОБА текста ОДНОВРЕМЕННО
2. Ищи конкретные пересечения, не абстракции
3. Каждое совпадение = требование + доказательство + цитата
4. Игнорируй общие навыки (коммуникация, ответственность)
5. Фокус на специфичных технологиях, процессах, результатах

ПРИМЕРЫ ХОРОШИХ СОВПАДЕНИЙ:
- "OKR планирование" → "внедрил OKR в команде 12 человек" (цитата)
- "Python разработка" → "3 года опыта с Python, Django" (цитата)
- "A/B тестирование" → "провел 15+ A/B тестов, рост конверсии на 25%" (цитата)

ПРИМЕРЫ ПЛОХИХ СОВПАДЕНИЙ:
- "коммуникативные навыки" → "работал в команде"
- "ответственность" → "выполнял задачи"

ВАКАНСИЯ:
{vacancy_text}

РЕЗЮМЕ:
{resume_text}

ФОРМАТ ОТВЕТА: строго JSON
{{
  "matches": [
    {{
      "requirement": "требование из вакансии",
      "evidence": "опыт из резюме",
      "quote": "точная цитата",
      "strength": 0.9,
      "type": "exact|strong|weak"
    }}
  ],
  "gaps": [
    {{
      "missing_requirement": "чего не хватает",
      "potential_bridge": "чем можно компенсировать"
    }}
  ]
}}
"""

LETTER_FROM_CONTEXT_PROMPT = """
Напиши сопроводительное письмо как СВЯЗНУЮ ИСТОРИЮ на основе найденных совпадений.

ПРИНЦИПЫ:
1. Логическая цепочка: опыт → навык → результат
2. Причинно-следственные связи
3. Единая нарратива
4. Конкретные цифры и факты

СВЯЗУЮЩИЕ КОНСТРУКЦИИ:
- "Это научило меня..."
- "Благодаря опыту в X, я смог..."
- "Именно поэтому..."
- "Развивая навыки в X, я перешел к Y..."
- "Комбинируя X и Y, я достиг..."

СТРУКТУРА:
Абзац 1: Зацепка + фундаментальный навык
Абзац 2: Развитие через логическую цепочку
Абзац 3: Применение и результаты
Абзац 4: Призыв к действию

СОВПАДЕНИЯ:
{matches}

ИСХОДНАЯ ВАКАНСИЯ:
{vacancy_text}

ИСХОДНОЕ РЕЗЮМЕ:
{resume_text}

СТИЛЬ: {style}

Напиши ТОЛЬКО текст письма без комментариев.
"""

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


# ============ LEGACY ПРОМПТЫ (для обратной совместимости) ============
# Архивные промпты перенесены в prompts_archive.md

# Импортируем legacy промпты только при необходимости
def _get_legacy_prompts():
    """Ленивая загрузка legacy промптов для обратной совместимости"""
    # В случае необходимости можно загрузить из prompts_archive.md
    # Пока оставляем заглушки для критически важных методов
    
    DEEP_ANALYSIS_PROMPT = """Ты эксперт-аналитик по HR и рекрутингу. Проведи глубокий анализ вакансии и резюме.

ЗАДАЧА: Пошагово проанализируй и верни структурированный JSON

ЭТАПЫ АНАЛИЗА:
1. АНАЛИЗ ВАКАНСИИ - ищи КОНКРЕТНЫЕ требования
2. АНАЛИЗ РЕЗЮМЕ - ищи ТОЧНЫЕ совпадения  
3. ПОИСК ПРЯМЫХ СОВПАДЕНИЙ

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

    HUMAN_WRITING_PROMPT = """Ты пишешь сопроводительные письма для кандидатов на работу.

АНАЛИЗ ИЗ ПРЕДЫДУЩЕГО ЭТАПА:
{analysis_json}

СТИЛЬ: {writing_style}

Напиши ТОЛЬКО текст письма без комментариев."""

    return {
        'DEEP_ANALYSIS_PROMPT': DEEP_ANALYSIS_PROMPT,
        'HUMAN_WRITING_PROMPT': HUMAN_WRITING_PROMPT
    }


# ============ ОСНОВНОЙ КЛАСС ============

class SmartAnalyzer:
    """Умный анализатор v6.0 на основе единого GPT промпта"""
    
    def __init__(self, ai_service):
        self.ai = ai_service
        self.user_id: Optional[int] = None
        self.session_id: Optional[str] = None
        # Статистика AI запросов для сессии
        self.total_tokens_used: int = 0
        self.models_used: set = set()
        
        # Устанавливаем callback для сбора статистики
        self.ai.set_stats_callback(self._collect_stats)
    
    def _collect_stats(self, model: str, tokens: int):
        """Собирает статистику AI запросов"""
        self.total_tokens_used += tokens
        self.models_used.add(model)
    
    def optimize_input_texts(self, vacancy: str, resume: str) -> Tuple[str, str]:
        """
        Оптимизация входных текстов для экономии токенов
        - Удаление избыточных пробелов
        - Сжатие повторяющихся фраз
        - Сохранение ключевой информации
        """
        def clean_text(text: str) -> str:
            # Удаляем избыточные пробелы и переносы
            text = re.sub(r'\s+', ' ', text.strip())
            # Удаляем повторяющиеся фразы (простая эвристика)
            text = re.sub(r'(\b\w+\b)(\s+\1){2,}', r'\1', text)
            return text
        
        optimized_vacancy = clean_text(vacancy)
        optimized_resume = clean_text(resume)
        
        # Логируем экономию токенов (примерная оценка: 1 токен ≈ 4 символа)
        original_chars = len(vacancy) + len(resume)
        optimized_chars = len(optimized_vacancy) + len(optimized_resume)
        saved_chars = original_chars - optimized_chars
        
        if saved_chars > 0:
            logger.info(f"📊 Оптимизация текста: сэкономлено ~{saved_chars//4} токенов")
        
        return optimized_vacancy, optimized_resume
    
    async def analyze_and_generate_unified(
        self,
        vacancy_text: str,
        resume_text: str,
        style: str = "professional"
    ) -> Dict[str, Any]:
        """
        🚀 ОСНОВНОЙ v6.0: Единый анализ и генерация письма за один запрос
        
        Args:
            vacancy_text: Текст вакансии
            resume_text: Текст резюме
            style: Стиль письма
            
        Returns:
            {
                'letter': str,           # Готовое письмо
                'matches': List[Dict],   # Найденные совпадения
                'analysis_summary': str, # Краткий анализ для пользователя
                'stats': Dict           # Статистика токенов
            }
        """
        logger.info("🚀 v6.0: Запускаю единый анализ...")
        logger.info(f"📊 Входные данные: вакансия={len(vacancy_text)} символов, резюме={len(resume_text)} символов")
        import time
        start_time = time.time()
        
        # Оптимизируем входные тексты
        optimized_vacancy, optimized_resume = self.optimize_input_texts(vacancy_text, resume_text)
        
        # Формируем единый промпт
        prompt = UNIFIED_ANALYSIS_PROMPT.format(
            vacancy_text=optimized_vacancy,
            resume_text=optimized_resume,
            style=style
        )
        
        try:
            response = await self.ai.get_completion(
                prompt=prompt,
                temperature=0.6,  # Баланс между структурированностью и креативностью
                max_tokens=3000,  # Увеличено для полного анализа + письма
                user_id=self.user_id,
                session_id=self.session_id,
                request_type="unified_analysis"
            )
            
            if not response:
                logger.error("❌ Получен пустой ответ при едином анализе")
                # Fallback на старый алгоритм
                logger.warning("🔄 Переключаюсь на legacy алгоритм...")
                return await self._legacy_generate_full_analysis_and_letter(vacancy_text, resume_text, style)
            
            # Парсим JSON ответ
            result = self._parse_json_safely(response, "unified_analysis")
            
            # Проверяем обязательные поля
            if not result.get('letter') or not result.get('matches'):
                logger.error("❌ Неполный ответ от единого анализа")
                # Fallback на старый алгоритм
                return await self._legacy_generate_full_analysis_and_letter(vacancy_text, resume_text, style)
            
            # Применяем де-ИИ-фикацию к письму
            logger.info("🔧 Применяю де-ИИ-фикацию...")
            final_letter = await self.deai_text(result['letter'])
            
            # Форматируем анализ для пользователя
            analysis_summary = self.format_unified_analysis(result.get('matches', []))
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Единый анализ завершен за {execution_time:.2f}с")
            
            return {
                'letter': final_letter,
                'matches': result.get('matches', []),
                'analysis_summary': analysis_summary,
                'missing_requirements': result.get('missing_requirements', []),
                'clarifying_questions': result.get('clarifying_questions', []),
                'stats': {
                    'total_tokens_used': self.total_tokens_used,
                    'models_used': list(self.models_used),
                    'generated_letter_length': len(final_letter),
                    'matches_found': len(result.get('matches', [])),
                    'confidence': result.get('confidence', 0.0),
                    'execution_time': execution_time,
                    'algorithm_version': 'v6.0_unified'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка единого анализа: {e}")
            
            # 📊 АНАЛИТИКА: Логируем ошибку в базу данных
            try:
                import traceback
                from models.analytics_models import ErrorData
                from services.analytics_service import AnalyticsService
                
                error_data = ErrorData(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    user_id=self.user_id,
                    session_id=self.session_id,
                    stack_trace=traceback.format_exc(),
                    handler_name='analyze_and_generate_unified'
                )
                analytics = AnalyticsService()
                await analytics.log_error(error_data)
            except Exception as log_error:
                logger.error(f"Failed to log unified analysis error: {log_error}")
            
            # Fallback на старый алгоритм
            logger.warning("🔄 Переключаюсь на legacy алгоритм из-за ошибки...")
            return await self._legacy_generate_full_analysis_and_letter(vacancy_text, resume_text, style)
    
    def format_unified_analysis(self, matches: list) -> str:
        """
        Форматирование результатов единого анализа для пользователя
        """
        try:
            summary = "📊 АНАЛИЗ СОВПАДЕНИЙ (v6.0)\n\n"
            
            if not matches:
                return summary + "⚠️ Совпадения не найдены"
            
            # Сортируем по силе совпадения
            sorted_matches = sorted(matches, key=lambda x: x.get('strength', 0), reverse=True)
            
            # Показываем топ-5 совпадений
            summary += "✅ НАЙДЕННЫЕ СОВПАДЕНИЯ:\n"
            for i, match in enumerate(sorted_matches[:5], 1):
                requirement = match.get('requirement', 'Требование')
                evidence = match.get('evidence', 'Опыт')
                strength = match.get('strength', 0)
                strength_emoji = "🔥" if strength >= 0.9 else "⚡" if strength >= 0.7 else "✓"
                
                summary += f"{i}. {strength_emoji} {requirement}\n"
                summary += f"   → {evidence}\n"
                if match.get('quote'):
                    summary += f"   💬 \"{match['quote'][:100]}...\"\n"
                summary += "\n"
            
            # Общая статистика
            avg_strength = sum(m.get('strength', 0) for m in matches) / len(matches)
            summary += f"📈 СТАТИСТИКА:\n"
            summary += f"• Найдено совпадений: {len(matches)}\n"
            summary += f"• Средняя сила: {avg_strength:.2f}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования анализа: {e}")
            return "📊 Анализ совпадений выполнен, но возникла ошибка форматирования."
    
    async def analyze_and_generate_contextual(
        self,
        vacancy_text: str,
        resume_text: str,
        style: str = "professional"
    ) -> Dict[str, Any]:
        """
        🔄 АЛЬТЕРНАТИВНЫЙ v6.0: Двухэтапный анализ с сохранением контекста
        
        Args:
            vacancy_text: Текст вакансии
            resume_text: Текст резюме
            style: Стиль письма
            
        Returns:
            Dict с письмом и анализом совпадений
        """
        logger.info("🔄 АЛЬТЕРНАТИВНЫЙ v6.0: Запускаю двухэтапный анализ с контекстом...")
        import time
        start_time = time.time()
        
        try:
            # ЭТАП 1: Анализ совпадений с контекстом
            logger.info("🔍 ЭТАП 1: Анализ совпадений...")
            matches_result = await self._contextual_matching_analysis(vacancy_text, resume_text)
            
            # ЭТАП 2: Генерация письма с полным контекстом
            logger.info("✍️ ЭТАП 2: Генерация письма...")
            letter = await self._generate_letter_from_context(
                matches_result, vacancy_text, resume_text, style
            )
            
            # Де-ИИ-фикация
            logger.info("🔧 Применяю де-ИИ-фикацию...")
            final_letter = await self.deai_text(letter)
            
            # Форматируем результат
            analysis_summary = self.format_unified_analysis(matches_result.get('matches', []))
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Двухэтапный анализ завершен за {execution_time:.2f}с")
            
            return {
                'letter': final_letter,
                'matches': matches_result.get('matches', []),
                'analysis_summary': analysis_summary,
                'stats': {
                    'total_tokens_used': self.total_tokens_used,
                    'models_used': list(self.models_used),
                    'generated_letter_length': len(final_letter),
                    'matches_found': len(matches_result.get('matches', [])),
                    'gaps_found': len(matches_result.get('gaps', [])),
                    'execution_time': execution_time,
                    'algorithm_version': 'v6.0_contextual'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка двухэтапного анализа: {e}")
            # Fallback на старый алгоритм
            return await self._legacy_generate_full_analysis_and_letter(vacancy_text, resume_text, style)
    
    async def _contextual_matching_analysis(self, vacancy_text: str, resume_text: str) -> Dict[str, Any]:
        """Этап 1: Анализ совпадений с контекстом"""
        prompt = CONTEXTUAL_MATCHING_PROMPT.format(
            vacancy_text=vacancy_text,
            resume_text=resume_text
        )
        
        response = await self.ai.get_completion(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2000,
            user_id=self.user_id,
            session_id=self.session_id,
            request_type="contextual_matching"
        )
        
        return self._parse_json_safely(response, "contextual_matching")
    
    async def _generate_letter_from_context(
        self, 
        matches_result: Dict[str, Any], 
        vacancy_text: str, 
        resume_text: str, 
        style: str
    ) -> str:
        """Этап 2: Генерация письма с полным контекстом"""
        prompt = LETTER_FROM_CONTEXT_PROMPT.format(
            matches=json.dumps(matches_result, ensure_ascii=False, indent=2),
            vacancy_text=vacancy_text,
            resume_text=resume_text,
            style=style
        )
        
        response = await self.ai.get_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=1500,
            user_id=self.user_id,
            session_id=self.session_id,
            request_type="contextual_letter_generation"
        )
        
        return response.strip() if response else ""
    
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
            response = await self.ai.get_completion(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1500,
                user_id=self.user_id,
                session_id=self.session_id,
                request_type="deai_processing"
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
            if analysis_type == "unified_analysis":
                return self._get_fallback_unified_analysis()
            elif analysis_type == "contextual_matching":
                return self._get_fallback_contextual_matching()
            else:
                return self._get_fallback_analysis()
    
    def _get_fallback_unified_analysis(self) -> Dict[str, Any]:
        """Fallback для единого анализа"""
        return {
            "matches": [
                {
                    "requirement": "профессиональный опыт",
                    "evidence": "имеется релевантный опыт",
                    "quote": "подтверждается резюме",
                    "strength": 0.7,
                    "explanation": "базовое соответствие требованиям"
                }
            ],
            "letter": "Уважаемые коллеги! Ваша вакансия привлекла мое внимание. Мой опыт соответствует основным требованиям позиции. Готов обсудить возможности сотрудничества.",
            "confidence": 0.6
        }
    
    def _get_fallback_contextual_matching(self) -> Dict[str, Any]:
        """Fallback для контекстного анализа совпадений"""
        return {
            "matches": [
                {
                    "requirement": "профессиональные навыки",
                    "evidence": "релевантный опыт",
                    "quote": "описано в резюме",
                    "strength": 0.7,
                    "type": "strong"
                }
            ],
            "gaps": []
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

    # ============ LEGACY МЕТОДЫ (для обратной совместимости) ============
    
    async def _legacy_generate_full_analysis_and_letter(
        self,
        vacancy_text: str,
        resume_text: str,
        style: str = "professional"
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Старый многоэтапный анализ (оставлен для fallback)
        """
        logger.warning("⚠️ DEPRECATED: Используется legacy алгоритм")
        
        try:
            # Используем упрощенный legacy алгоритм
            legacy_prompts = _get_legacy_prompts()
            
            # Один запрос для анализа
            analysis = await self._legacy_deep_analyze(vacancy_text, resume_text, legacy_prompts)
            
            # Один запрос для письма
            letter = await self._legacy_generate_human_letter(analysis, style, legacy_prompts)
            
            # Де-ИИ-фикация
            final_letter = await self.deai_text(letter)
            
            # Форматируем legacy анализ
            formatted_analysis = self._format_legacy_analysis(analysis)
            
            return {
                'letter': final_letter,
                'analysis': formatted_analysis,
                'analysis_summary': formatted_analysis,
                'matches': [],  # Legacy не возвращает matches
                'stats': {
                    'total_tokens_used': self.total_tokens_used,
                    'models_used': list(self.models_used),
                    'generated_letter_length': len(final_letter),
                    'algorithm_version': 'legacy_v5.0'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка legacy алгоритма: {e}")
            # Возвращаем минимальный результат
            return {
                'letter': "Уважаемые коллеги! Рассматриваю возможность работы в вашей компании. Мой опыт и навыки соответствуют требованиям позиции. Готов обсудить детали сотрудничества.",
                'analysis': "Анализ выполнен в упрощенном режиме",
                'analysis_summary': "Анализ выполнен в упрощенном режиме",
                'matches': [],
                'stats': {
                    'algorithm_version': 'fallback_minimal'
                }
            }
    
    async def _legacy_deep_analyze(self, vacancy_text: str, resume_text: str, prompts: dict) -> Dict[str, Any]:
        """Legacy глубокий анализ"""
        prompt = prompts['DEEP_ANALYSIS_PROMPT'].format(
            vacancy_text=vacancy_text,
            resume_text=resume_text
        )
        
        try:
            response = await self.ai.get_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000,
                user_id=self.user_id,
                session_id=self.session_id,
                request_type="legacy_analysis"
            )
            
            if not response:
                return self._get_fallback_analysis()
            
            return self._parse_json_safely(response, "legacy_analysis")
            
        except Exception as e:
            logger.error(f"❌ Ошибка legacy анализа: {e}")
            return self._get_fallback_analysis()
    
    async def _legacy_generate_human_letter(
        self, 
        analysis: Dict[str, Any], 
        style: str,
        prompts: dict
    ) -> str:
        """Legacy генерация письма"""
        prompt = prompts['HUMAN_WRITING_PROMPT'].format(
            analysis_json=json.dumps(analysis, ensure_ascii=False, indent=2),
            writing_style=style
        )
        
        try:
            response = await self.ai.get_completion(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1500,
                user_id=self.user_id,
                session_id=self.session_id,
                request_type="legacy_letter_generation"
            )
            
            return response.strip() if response else "Письмо не удалось сгенерировать"
            
        except Exception as e:
            logger.error(f"❌ Ошибка legacy генерации письма: {e}")
            return "Письмо не удалось сгенерировать"
    
    def _format_legacy_analysis(self, analysis: Dict[str, Any]) -> str:
        """Форматирование legacy анализа"""
        try:
            summary = "📊 АНАЛИЗ СОВПАДЕНИЙ (legacy)\n\n"
            
            # Основные совпадения
            matches = analysis.get('matching_strategy', {}).get('direct_matches', [])
            if matches:
                summary += "✅ НАЙДЕННЫЕ СОВПАДЕНИЯ:\n"
                for i, match in enumerate(matches[:5], 1):
                    summary += f"{i}. {match}\n"
                summary += "\n"
            
            # Пробелы в навыках
            gaps = analysis.get('matching_strategy', {}).get('skill_gaps', [])
            if gaps:
                summary += "⚠️ ОБЛАСТИ ДЛЯ РАЗВИТИЯ:\n"
                for gap in gaps[:3]:
                    summary += f"• {gap}\n"
                summary += "\n"
            
            # Уверенность
            confidence = analysis.get('confidence_score', 0)
            summary += f"📈 УВЕРЕННОСТЬ: {confidence:.2f}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования legacy анализа: {e}")
            return "📊 Legacy анализ выполнен"

    # Deprecated методы для полной обратной совместимости
    async def deep_analyze(self, vacancy_text: str, resume_text: str) -> Dict[str, Any]:
        """DEPRECATED: Используйте analyze_and_generate_unified"""
        logger.warning("⚠️ DEPRECATED: deep_analyze устарел, используйте analyze_and_generate_unified")
        prompts = _get_legacy_prompts()
        return await self._legacy_deep_analyze(vacancy_text, resume_text, prompts)
    
    async def generate_human_letter(self, analysis: Dict[str, Any], style: str = "professional") -> str:
        """DEPRECATED: Используйте analyze_and_generate_unified"""
        logger.warning("⚠️ DEPRECATED: generate_human_letter устарел, используйте analyze_and_generate_unified")
        prompts = _get_legacy_prompts()
        return await self._legacy_generate_human_letter(analysis, style, prompts)
    
    async def generate_full_letter(self, vacancy_text: str, resume_text: str, style: str = "professional") -> str:
        """DEPRECATED: Используйте analyze_and_generate_unified"""
        logger.warning("⚠️ DEPRECATED: generate_full_letter устарел, используйте analyze_and_generate_unified")
        result = await self._legacy_generate_full_analysis_and_letter(vacancy_text, resume_text, style)
        return result['letter']
    
    async def generate_full_analysis_and_letter(self, vacancy_text: str, resume_text: str, style: str = "professional") -> Dict[str, Any]:
        """DEPRECATED: Используйте analyze_and_generate_unified"""
        logger.warning("⚠️ DEPRECATED: generate_full_analysis_and_letter устарел, используйте analyze_and_generate_unified")
        return await self._legacy_generate_full_analysis_and_letter(vacancy_text, resume_text, style)


# ============ ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР ============

_analyzer_instance: Optional[SmartAnalyzer] = None


def get_analyzer(ai_service=None) -> SmartAnalyzer:
    """Получить глобальный экземпляр анализатора"""
    global _analyzer_instance
    
    if _analyzer_instance is None:
        if ai_service is None:
            from services.ai_factory import get_ai_service
            ai_service = get_ai_service()
        _analyzer_instance = SmartAnalyzer(ai_service)
    
    return _analyzer_instance


async def analyze_and_generate(
    vacancy_text: str,
    resume_text: str,
    style: str = "professional",
    ai_service=None
) -> str:
    """
    DEPRECATED: Удобная функция для полного флоу (обратная совместимость)
    Используйте analyze_and_generate_with_analysis для новых проектов
    """
    logger.warning("⚠️ DEPRECATED: analyze_and_generate устарел, используйте analyze_and_generate_with_analysis")
    analyzer = get_analyzer(ai_service)
    result = await analyzer._legacy_generate_full_analysis_and_letter(vacancy_text, resume_text, style)
    return result['letter']


async def analyze_and_generate_with_analysis(
    vacancy_text: str,
    resume_text: str,
    style: str = "professional",
    ai_service=None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    🚀 ОСНОВНАЯ ФУНКЦИЯ v6.0: Анализ и генерация с A/B тестированием
    
    Args:
        vacancy_text: Текст вакансии
        resume_text: Текст резюме  
        style: Стиль письма
        openai_service: Сервис OpenAI (опционально)
        user_id: ID пользователя для аналитики
        session_id: ID сессии для аналитики
        
    Returns:
        Dict с письмом и анализом совпадений
    """
    analyzer = get_analyzer(ai_service)
    # Передаем аналитические параметры в анализатор
    analyzer.user_id = user_id
    analyzer.session_id = session_id
    
    # A/B тестирование: выбор алгоритма
    use_unified = os.getenv('USE_UNIFIED_ANALYSIS', 'true').lower() == 'true'
    
    if use_unified:
        logger.info("🚀 Используется новый алгоритм v6.0 (единый анализ)")
        return await analyzer.analyze_and_generate_unified(vacancy_text, resume_text, style)
    else:
        logger.info("🔄 Используется legacy алгоритм v5.0 (многоэтапный)")
        return await analyzer._legacy_generate_full_analysis_and_letter(vacancy_text, resume_text, style) 