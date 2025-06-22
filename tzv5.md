🚀 Предлагаемая новая схема
Улучшенная архитектура:
ЭТАП 1: structured_vacancy_analysis() → Структурированный анализ вакансии
         ↓
ЭТАП 2: structured_resume_analysis() → Структурированный анализ резюме  
         ↓
ЭТАП 3: precise_matching() → Точное сопоставление требований и навыков
         ↓
ЭТАП 4: generate_letter_from_matches() → Генерация письма на основе готовых совпадений
📋 Детализированные алгоритмы анализа
🎯 ЭТАП 1: Анализ вакансии
pythonVACANCY_ANALYSIS_PROMPT = """
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
{
  "hard_requirements": [
    {
      "requirement": "конкретное требование",
      "importance": "critical/high/medium",
      "specificity": "specific/general",
      "keywords": ["ключевые", "слова"]
    }
  ],
  "soft_requirements": [...],
  "business_tasks": [...],
  "company_context": {...},
  "key_terms": [...]
}
"""
👤 ЭТАП 2: Анализ резюме
pythonRESUME_ANALYSIS_PROMPT = """
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
{
  "technical_skills": [
    {
      "skill": "конкретный навык",
      "level": "beginner/intermediate/advanced/expert",
      "context": "где и как использовал",
      "results": "какие результаты достиг",
      "keywords": ["ключевые", "слова"]
    }
  ],
  "experience": [...],
  "achievements": [...],
  "education": [...],
  "additional": [...]
}
"""
🔗 ЭТАП 3: Точное сопоставление
pythonMATCHING_ALGORITHM_PROMPT = """
ЗАДАЧА: Найти ТОЧНЫЕ совпадения между требованиями вакансии и навыками в резюме.

АЛГОРИТМ СОПОСТАВЛЕНИЯ:

1. ПРЯМЫЕ СОВПАДЕНИЯ (exact matches):
   - Одинаковые технологии/инструменты
   - Похожий опыт работы
   - Совпадающие методологии
   - Идентичные процессы

2. СИЛЬНЫЕ СОВПАДЕНИЯ (strong matches):
   - Смежные технологии (React → Vue.js)
   - Переносимый опыт (B2B продажи → B2C продажи)
   - Похожие роли (Team Lead → Project Manager)

3. СЛАБЫЕ СОВПАДЕНИЯ (weak matches):
   - Общие навыки (коммуникация, лидерство)
   - Базовые требования (MS Office, английский)

4. ПРОБЕЛЫ (gaps):
   - Отсутствующие жёсткие требования
   - Недостающий опыт
   - Нехватка специфичных навыков

ПРАВИЛА ОЦЕНКИ СОВПАДЕНИЙ:
- Учитывать КОНТЕКСТ использования навыка
- Искать КОЛИЧЕСТВЕННЫЕ результаты  
- Приоритизировать СПЕЦИФИЧНОСТЬ над общностью
- Выделять УНИКАЛЬНЫЕ преимущества

ФОРМАТ ОТВЕТА: JSON
{
  "exact_matches": [
    {
      "requirement": "требование из вакансии",
      "match": "совпадение в резюме", 
      "strength": "exact/strong/weak",
      "evidence": "конкретные доказательства",
      "impact": "результат/метрика"
    }
  ],
  "strong_matches": [...],
  "weak_matches": [...],
  "gaps": [...],
  "unique_advantages": [...]
}
"""
✍️ ЭТАП 4: Генерация письма на основе совпадений
pythonLETTER_GENERATION_PROMPT = """
ЗАДАЧА: Написать сопроводительное письмо на основе ГОТОВОГО анализа совпадений.

У тебя есть:
- Структурированный анализ вакансии
- Детализированный анализ резюме  
- Точные совпадения требований и навыков
- Выявленные пробелы и уникальные преимущества

АЛГОРИТМ НАПИСАНИЯ ПИСЬМА:

1. ОТБОР ЛУЧШИХ СОВПАДЕНИЙ:
   - Выбери 5-7 самых сильных совпадений
   - Приоритизируй exact_matches и strong_matches
   - Игнорируй weak_matches и общие навыки

2. СОЗДАНИЕ "МОСТОВ":
   - Для каждого совпадения: "Вам важно X → У меня есть Y с результатом Z"
   - Используй конкретные цифры и факты
   - Покажи ЦЕННОСТЬ для работодателя

3. СТРУКТУРА ПИСЬМА:
   - Абзац 1: Конкретная мотивация + топ-1 совпадение
   - Абзац 2-3: 4-6 ключевых совпадений с результатами
   - Абзац 4: Уникальное преимущество + призыв к действию

4. РАБОТА С ПРОБЕЛАМИ:
   - НЕ упоминай отсутствующие навыки
   - Найди смежные навыки для компенсации
   - Покажи готовность к развитию

КЛЮЧЕВЫЕ ПРИНЦИПЫ:
- Каждое утверждение = конкретный факт
- Фокус на РЕЗУЛЬТАТАХ, а не процессах
- Использовать ЦИФРЫ и МЕТРИКИ
- Избегать общих фраз и клише

ВХОДНЫЕ ДАННЫЕ:
{ready_analysis}
"""


# Улучшенный алгоритм с анализом совпадений и веб-поиском

class EnhancedLetterGenerator:
    """Улучшенный генератор с анализом совпадений и контекста компании"""
    
    async def generate_full_analysis_and_letter(self, vacancy_text, resume_text):
        """
        Новый алгоритм: Анализ → Совпадения → Письмо → Обоснование
        """
        
        # ЭТАП 1: Расширенный анализ вакансии (с веб-поиском)
        logger.info("🔍 ЭТАП 1: Анализ вакансии + контекст компании...")
        vacancy_analysis = await self.analyze_vacancy_with_context(vacancy_text)
        
        # ЭТАП 2: Структурированный анализ резюме  
        logger.info("👤 ЭТАП 2: Анализ резюме...")
        resume_analysis = await self.analyze_resume_structured(resume_text)
        
        # ЭТАП 3: Детальный анализ совпадений
        logger.info("⚡ ЭТАП 3: Анализ совпадений...")
        matching_analysis = await self.detailed_matching_analysis(
            vacancy_analysis, resume_analysis
        )
        
        # ЭТАП 4: Генерация письма
        logger.info("✍️ ЭТАП 4: Генерация письма...")
        letter = await self.generate_letter_from_analysis(matching_analysis)
        
        # ЭТАП 5: Де-ИИ-фикация
        logger.info("🔧 ЭТАП 5: Финальная обработка...")
        final_letter = await self.deai_text(letter)
        
        # Возвращаем и письмо И анализ
        return {
            'letter': final_letter,
            'analysis': self.format_matching_summary(matching_analysis),
            'company_context': vacancy_analysis.get('company_context', {}),
            'recommendations': self.generate_recommendations(matching_analysis)
        }

    async def analyze_vacancy_with_context(self, vacancy_text):
        """Анализ вакансии с поиском информации о компании"""
        
        # Базовый анализ вакансии
        base_analysis = await self.analyze_vacancy_structured(vacancy_text)
        
        # Извлекаем название компании
        company_name = self.extract_company_name(vacancy_text)
        
        if company_name:
            # Веб-поиск информации о компании
            company_context = await self.research_company(company_name)
            base_analysis['company_context'] = company_context
            
            # Поиск отраслевых трендов и терминологии
            industry_context = await self.research_industry_trends(
                base_analysis.get('industry', ''),
                base_analysis.get('key_terms', [])
            )
            base_analysis['industry_context'] = industry_context
        
        return base_analysis

    async def research_company(self, company_name):
        """Исследование компании через веб-поиск"""
        
        # Поиск базовой информации
        basic_info = await self.web_search(f"{company_name} компания о нас")
        
        # Поиск отзывов сотрудников
        employee_reviews = await self.web_search(f"{company_name} отзывы сотрудников hh.ru")
        
        # Поиск новостей и событий
        recent_news = await self.web_search(f"{company_name} новости 2024 2025")
        
        return {
            'size': self.determine_company_size(basic_info),
            'industry': self.extract_industry(basic_info),
            'culture': self.analyze_culture(employee_reviews),
            'recent_events': self.extract_recent_events(recent_news),
            'growth_stage': self.determine_growth_stage(basic_info, recent_news)
        }

    async def detailed_matching_analysis(self, vacancy_analysis, resume_analysis):
        """Детальный анализ совпадений с оценками и рекомендациями"""
        
        prompt = f"""
        ЗАДАЧА: Создать детальный анализ совпадений вакансии и резюме с практическими рекомендациями.

        АНАЛИЗ ВАКАНСИИ: {vacancy_analysis}
        АНАЛИЗ РЕЗЮМЕ: {resume_analysis}

        АЛГОРИТМ АНАЛИЗА СОВПАДЕНИЙ:

        1. ПРЯМЫЕ СОВПАДЕНИЯ (90-100% match):
           - Точные технологии/инструменты
           - Идентичный опыт
           - Совпадающие методологии
           
        2. СИЛЬНЫЕ СОВПАДЕНИЯ (70-89% match):
           - Смежные технологии
           - Переносимый опыт
           - Похожие роли с доп. ответственностью
           
        3. ЧАСТИЧНЫЕ СОВПАДЕНИЯ (40-69% match):
           - Базовые навыки
           - Общий опыт индустрии
           - Схожие процессы
           
        4. КРИТИЧЕСКИЕ ПРОБЕЛЫ:
           - Отсутствующие жесткие требования
           - Недостающий специфичный опыт
           
        5. СКРЫТЫЕ ПРЕИМУЩЕСТВА:
           - Уникальные навыки кандидата
           - Дополнительная ценность
           - Компенсирующие сильные стороны

        ФОРМАТ ОТВЕТА: JSON с детальным описанием каждого совпадения/пробела
        """
        
        return await self.openai_service.get_completion(prompt)

    def format_matching_summary(self, matching_analysis):
        """Форматирование анализа совпадений для пользователя"""
        
        summary = """
        📊 АНАЛИЗ СОВПАДЕНИЙ ВАКАНСИИ И РЕЗЮМЕ

        ✅ СИЛЬНЫЕ СТОРОНЫ:
        {strong_matches}

        ⚡ ЧАСТИЧНЫЕ СОВПАДЕНИЯ:
        {partial_matches}

        ⚠️ ОБЛАСТИ ДЛЯ РАЗВИТИЯ:
        {gaps}

        🎯 УНИКАЛЬНЫЕ ПРЕИМУЩЕСТВА:
        {unique_advantages}

        💡 РЕКОМЕНДАЦИИ:
        {recommendations}
        """
        
        # Заполняем шаблон данными из анализа
        return summary.format(
            strong_matches=self.format_matches(matching_analysis.get('strong_matches', [])),
            partial_matches=self.format_matches(matching_analysis.get('partial_matches', [])),
            gaps=self.format_gaps(matching_analysis.get('gaps', [])),
            unique_advantages=self.format_advantages(matching_analysis.get('unique_advantages', [])),
            recommendations=self.format_recommendations(matching_analysis.get('recommendations', []))
        )

    async def research_industry_trends(self, industry, key_terms):
        """Исследование трендов индустрии и актуальности терминов"""
        
        if not industry or not key_terms:
            return {}
            
        # Поиск трендов в индустрии
        trends_query = f"{industry} тренды 2024 2025 технологии"
        trends_info = await self.web_search(trends_query)
        
        # Проверка актуальности ключевых терминов
        terms_relevance = {}
        for term in key_terms[:5]:  # Ограничиваем количество запросов
            term_query = f"{term} {industry} востребованность 2024"
            term_info = await self.web_search(term_query)
            terms_relevance[term] = self.analyze_term_relevance(term_info)
        
        return {
            'trends': self.extract_trends(trends_info),
            'terms_relevance': terms_relevance,
            'market_demand': self.analyze_market_demand(trends_info)
        }

# Новый обработчик для бота
class EnhancedConversationHandler:
    """Обновленный обработчик с анализом совпадений"""
    
    async def handle_resume_and_generate(self, update, context):
        """Обработка резюме с генерацией письма И анализа"""
        
        resume_text = update.message.text
        vacancy_text = context.user_data['vacancy']
        
        # Показываем прогресс
        progress_msg = await update.message.reply_text(
            "🔄 Создаю профессиональное письмо и анализ совпадений...\n\n"
            "⏳ Это займет 30-45 секунд\n"
            "🔍 Анализирую компанию и вакансию\n"
            "👤 Изучаю ваше резюме\n"
            "⚡ Ищу совпадения и преимущества\n"
            "✍️ Генерирую письмо и обоснование"
        )
        
        try:
            # Генерируем полный анализ
            result = await self.generator.generate_full_analysis_and_letter(
                vacancy_text, resume_text
            )
            
            # Удаляем сообщение о прогрессе
            await progress_msg.delete()
            
            # Отправляем письмо
            await update.message.reply_text(
                f"✍️ <b>СОПРОВОДИТЕЛЬНОЕ ПИСЬМО:</b>\n\n{result['letter']}",
                parse_mode='HTML'
            )
            
            # Отправляем анализ совпадений
            await update.message.reply_text(
                f"📊 <b>АНАЛИЗ СОВПАДЕНИЙ:</b>\n\n{result['analysis']}",
                parse_mode='HTML'
            )
            
            # Если есть контекст компании - отправляем
            if result.get('company_context'):
                company_summary = self.format_company_context(result['company_context'])
                await update.message.reply_text(
                    f"🏢 <b>КОНТЕКСТ КОМПАНИИ:</b>\n\n{company_summary}",
                    parse_mode='HTML'
                )
            
            # Кнопка для нового письма
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Создать новое письмо", callback_data="start_new")
            ]])
            
            await update.message.reply_text(
                "🎉 Готово! Письмо и анализ созданы.",
                reply_markup=keyboard
            )
            
        except Exception as e:
            await progress_msg.delete()
            await update.message.reply_text(
                "❌ Произошла ошибка при генерации. Попробуйте еще раз."
            )
            logger.error(f"Generation error: {e}")
        
        return ConversationHandler.END

# 📋 ПЛАН РЕАЛИЗАЦИИ НОВОЙ АРХИТЕКТУРЫ

## 🎯 Цель
Реализовать 4-этапную структурированную архитектуру анализа:
1. Анализ вакансии → структурированные требования  
2. Анализ резюме → структурированные навыки
3. Точное сопоставление → оценка совпадений
4. Генерация письма → на основе готовых совпадений

## 📝 ЭТАПЫ РЕАЛИЗАЦИИ

### ЭТАП 1: Обновление smart_analyzer.py (КРИТИЧНО) ✅ ВЫПОЛНЕНО
**Задачи:**
- [x] Добавить 4 новых промпта из текущего ТЗ
- [x] Переписать метод `generate_full_letter()` → `generate_full_analysis_and_letter()`
- [x] Добавить новые методы:
  - `analyze_vacancy_structured()`
  - `analyze_resume_structured()`  
  - `detailed_matching_analysis()`
  - `generate_letter_from_analysis()`
  - `format_matching_summary()`
- [x] Сохранить обратную совместимость со старым API

**Новые промпты:**
- `VACANCY_ANALYSIS_PROMPT` - структурированный анализ вакансии
- `RESUME_ANALYSIS_PROMPT` - структурированный анализ резюме  
- `MATCHING_ANALYSIS_PROMPT` - детальный анализ совпадений
- `LETTER_GENERATION_PROMPT` - генерация на основе анализа

### ЭТАП 2: Обновление simple_conversation.py (ВАЖНО) ✅ ВЫПОЛНЕНО
**Задачи:**
- [x] Изменить вызов в `handle_resume_simple()`: 
  - Заменить `analyze_and_generate()` на `analyze_and_generate_with_analysis()`
- [x] Добавить отправку анализа совпадений пользователю
- [x] Улучшить сообщение о прогрессе (4 этапа)
- [x] Добавить обработку нового формата результата

**Новая структура ответа:**
```python
result = {
    'letter': 'готовое письмо',
    'analysis': 'форматированный анализ совпадений'
}
```

### ЭТАП 3: Обновление openai_service.py (ПОДДЕРЖКА)
**Задачи:**
- [ ] Добавить метод `get_structured_analysis()` для JSON ответов
- [ ] Добавить метод `parse_json_safely()` для безопасного парсинга
- [ ] Улучшить обработку ошибок для структурированных запросов

### ЭТАП 4: Обновление utils/prompts.py (ОРГАНИЗАЦИЯ)
**Задачи:**
- [ ] Перенести новые промпты из smart_analyzer.py
- [ ] Организовать промпты по категориям
- [ ] Сохранить старые промпты для совместимости

## 🔄 ПОСЛЕДОВАТЕЛЬНОСТЬ ВЫПОЛНЕНИЯ

### ШАГ 1: Подготовка smart_analyzer.py
1. Добавить новые промпты в начало файла
2. Создать новые методы для каждого этапа анализа
3. Переписать главный метод `generate_full_analysis_and_letter()`
4. Добавить форматирование результата для пользователя

### ШАГ 2: Обновление обработчика
1. Изменить вызов в `handle_resume_simple()`
2. Добавить отправку анализа совпадений  
3. Улучшить UX с показом прогресса

### ШАГ 3: Тестирование и доработка
1. Протестировать новый флоу
2. Исправить ошибки парсинга JSON
3. Улучшить качество промптов по результатам

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

**До:**
- Пользователь получает только письмо
- Один большой промпт-анализ
- Нет понимания совпадений

**После:**  
- Пользователь получает письмо + анализ совпадений
- 4-этапный структурированный анализ
- Понимание сильных сторон и пробелов
- Более точные и релевантные письма

## 🎯 КРИТЕРИИ УСПЕХА

### Технические:
- [ ] Все 4 этапа работают стабильно
- [ ] JSON парсится без ошибок  
- [ ] Обратная совместимость сохранена
- [ ] Время генерации не превышает 45 секунд

### Пользовательские:
- [ ] Письма стали более релевантными
- [ ] Анализ совпадений понятен и полезен
- [ ] UX улучшился с показом прогресса
- [ ] Нет регрессии в качестве писем

## 🚀 ГОТОВ К РЕАЛИЗАЦИИ

План составлен, переходим к реализации ЭТАПА 1!