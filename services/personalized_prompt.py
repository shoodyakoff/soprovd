"""
Генератор персонализированных промптов для OpenAI
"""
from typing import Dict, Any
from models.profile_models import AnalyzedProfile, SuggestedStyle
from models.style_definitions import STYLE_RULES, STYLE_MODIFIERS


class PersonalizedPromptGenerator:
    """Генерирует персонализированные промпты на основе профиля пользователя"""
    
    def __init__(self):
        self.base_prompt_template = self._get_base_prompt_template()
    
    def generate_prompt(
        self, 
        job_description: str, 
        resume: str, 
        profile: AnalyzedProfile
    ) -> str:
        """
        Генерирует персонализированный промпт
        
        Args:
            job_description: Описание вакансии
            resume: Резюме кандидата
            profile: Анализированный профиль пользователя
            
        Returns:
            Готовый промпт для OpenAI
        """
        # Получаем правила стиля
        style_rules = self._get_style_rules(profile.suggested_style)
        
        # Получаем модификаторы
        modifiers = self._get_modifiers(profile.profession, profile.level)
        
        # Формируем описание стиля
        style_description = self._build_style_description(
            profile.suggested_style, style_rules, modifiers
        )
        
        # Генерируем параметры
        temperature = self._get_temperature(profile.suggested_style)
        max_tokens = self._get_max_tokens(profile.suggested_style)
        
        # Заполняем шаблон
        prompt = self.base_prompt_template.format(
            style_description=style_description,
            temperature=temperature,
            max_tokens=max_tokens,
            job_description=job_description,
            resume=resume,
            profession=profile.profession,
            level=profile.level,
            tone=style_rules.tone if style_rules else "профессиональный"
        )
        
        return prompt
    
    def _get_base_prompt_template(self) -> str:
        """Базовый шаблон промпта"""
        return """Ты — опытный карьерный коуч, который пишет сопроводительные письма от лица кандидата (не от третьего лица).

Кандидат: {profession}, уровень {level}

Ключевые принципы:
- Естественность: письмо должно звучать как написанное живым человеком, избегай штампов и "нейросетевых" фраз
- Конкретность: каждое утверждение подкрепляй фактами из резюме
- Релевантность: четко связывай опыт кандидата с требованиями вакансии
- Честность: если опыта в какой-то области нет — признавай это, но показывай смежные навыки

Приветствие:
- Если стиль нейтральный или формальный: начинай с "Здравствуйте!"
- Если стиль креативный или уверенный: можешь использовать "Привет!" или другое неформальное приветствие

Структура письма:
1. Приветствие (1 предложение): в зависимости от стиля
2. Зацепка (1 длинное или 2 коротких предложения): личная история или наблюдение, которое показывает понимание индустрии/продукта
3. Опыт и достижения (до 2 длинных или 3 средних предложений): конкретные кейсы с цифрами, прямо связанные с требованиями вакансии
4. Мотивация (1 предложение): почему именно эта компания/продукт, что хочешь достичь
5. Завершение: простое завершение без подписи "С уважением" или "[Ваше имя]"

Чего избегать:
- Повторов одних и тех же слов/фраз
- Слов-маркеров ИИ: "недавно", "знаете что", "это кайф", "особенно круто"
- Неестественных конструкций: "всё под мою ответственность", "погрузиться глубоко"
- Лести и преувеличений о компании
- Агрессивных P.S. с "вызовами"
- Смайликов и других очевидных маркеров ИИ
- Обращений типа "Уважаемый [Имя]" - используй только простое приветствие
- Подписи "С уважением, [Ваше имя]" в конце письма

Стиль письма: {style_description}
Тон: {tone}

Обязательно:
- Матчинг с требованиями: для каждого ключевого требования вакансии найди соответствующий опыт в резюме
- Честность о пробелах: если опыта в чем-то нет, скажи об этом прямо, но покажи смежные навыки
- Конкретные цифры: используй достижения из резюме с точными метриками
- Проверка на естественность: каждое предложение должно звучать так, как сказал бы реальный человек

Входные данные:
Описание вакансии: {job_description}

Резюме кандидата: {resume}

Финальная проверка:
Перечитай письмо и спроси себя:
- Звучит ли это как живой человек?
- Ясно ли, почему этого кандидата стоит позвать на интервью?
- Нет ли повторов или штампов?
- Соответствует ли каждое утверждение фактам из резюме?

Напиши сопроводительное письмо:"""
    
    def _get_style_rules(self, suggested_style: SuggestedStyle):
        """Получает правила стиля"""
        if suggested_style.style in STYLE_RULES:
            return STYLE_RULES[suggested_style.style]
        return None
    
    def _get_modifiers(self, profession: str, level: str) -> Dict[str, Any]:
        """Получает модификаторы для профессии и уровня"""
        modifiers = {}
        
        # Проверяем модификаторы по уровню
        for levels, mods in STYLE_MODIFIERS.items():
            if level in levels:
                modifiers.update(mods)
        
        # Проверяем модификаторы по профессии (упрощенно)
        if "designer" in profession.lower():
            modifiers.update(STYLE_MODIFIERS.get(("designer",), {}))
        elif "developer" in profession.lower():
            modifiers.update(STYLE_MODIFIERS.get(("developer",), {}))
        
        return modifiers
    
    def _build_style_description(
        self, 
        suggested_style: SuggestedStyle, 
        style_rules,
        modifiers: Dict[str, Any]
    ) -> str:
        """Строит описание стиля"""
        description_parts = [suggested_style.tone_description]
        
        if style_rules:
            description_parts.append(f"Тон: {style_rules.tone}")
            
            if style_rules.suggestions:
                description_parts.append(f"Рекомендации: {', '.join(style_rules.suggestions)}")
                
            if style_rules.avoid:
                description_parts.append(f"Избегай: {', '.join(style_rules.avoid)}")
        
        # Добавляем модификаторы
        if modifiers:
            modifier_descriptions = []
            if modifiers.get("soften_confidence"):
                modifier_descriptions.append("смягчи уверенные утверждения")
            if modifiers.get("focus_on_learning"):
                modifier_descriptions.append("подчеркни готовность к обучению")
            if modifiers.get("highlight_impact"):
                modifier_descriptions.append("акцентируй влияние и результаты")
            if modifiers.get("use_strategy_words"):
                modifier_descriptions.append("используй стратегическую терминологию")
            if modifiers.get("allow_visual_language"):
                modifier_descriptions.append("можешь использовать визуальные метафоры")
            if modifiers.get("simplify_language"):
                modifier_descriptions.append("используй простой и точный язык")
                
            if modifier_descriptions:
                description_parts.append(f"Особенности: {', '.join(modifier_descriptions)}")
        
        return ". ".join(description_parts)
    
    def _get_temperature(self, suggested_style: SuggestedStyle) -> float:
        """Определяет температуру для OpenAI в зависимости от стиля"""
        if suggested_style.style == "creative":
            return 0.9
        elif suggested_style.style == "confident":
            return 0.7
        else:  # neutral
            return 0.8
    
    def _get_max_tokens(self, suggested_style: SuggestedStyle) -> int:
        """Определяет максимальное количество токенов"""
        # Базовое значение - достаточно для качественного письма
        return 800


# Глобальный экземпляр генератора
prompt_generator = PersonalizedPromptGenerator()


def generate_personalized_prompt(
    job_description: str, 
    resume: str, 
    profile: AnalyzedProfile
) -> str:
    """Удобная функция для генерации персонализированного промпта"""
    return prompt_generator.generate_prompt(job_description, resume, profile) 