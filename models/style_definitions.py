"""
Определения стилей, профессий и ключевых слов для анализа профилей
"""
from typing import Dict, Tuple
from .profile_models import SuggestedStyle, StyleRules


# Ключевые слова для определения профессий
KEYWORDS = {
    "product manager": ["product", "MVP", "backlog", "roadmap", "hypothesis", "discovery", "delivery"],
    "ux/ui designer": ["figma", "user flow", "wireframe", "prototype", "ux", "ui", "дизайн-система"],
    "frontend developer": ["react", "vue", "typescript", "javascript", "html", "css", "frontend"],
    "backend developer": ["node.js", "python", "django", "spring", "java", "api", "backend"],
    "qa engineer": ["test case", "pytest", "регрессия", "тест-план", "selenium", "qa", "тестирование"],
    "product analyst": ["sql", "product metrics", "cohort", "retention", "аналитика", "dashboards"],
    "business analyst": ["требования", "BRD", "gap analysis", "сценарии", "use case", "UML"],
    "marketing specialist": ["go-to-market", "рост", "трафик", "креатив", "воронка", "бренд"],
    "cto": ["architecture", "tech strategy", "инфраструктура", "cloud", "security"],
    "head of design": ["дизайн-ревью", "дизайн команда", "креатив", "арт-дирекшн", "стратегия дизайна"],
    "cpo": ["стратегия", "продуктовый портфель", "vision", "оргструктура", "product leadership"]
}

# Ключевые слова для определения уровня
LEVEL_KEYWORDS = {
    "junior": ["начинающий", "стажировка", "учусь", "изучаю", "развиваюсь"],
    "middle": ["отвечал за", "вёл", "самостоятельно", "опыт работы от 2 лет"],
    "senior": ["руководил", "экспертиза", "отвечал за весь цикл", "инициировал"],
    "lead": ["возглавлял", "руководил командой", "отвечал за направление"],
    "c-level": ["стратегия", "визионер", "организационные изменения", "top management"]
}

# Матрица стилей по профессии и уровню
STYLE_MAP: Dict[Tuple[str, str], SuggestedStyle] = {
    ("product manager", "junior"): SuggestedStyle("creative", True, False, "Живой, с нотками интереса и инициативности."),
    ("product manager", "middle"): SuggestedStyle("neutral", True, True, "Сдержанный, но гибкий стиль с умеренным креативом."),
    ("product manager", "senior"): SuggestedStyle("neutral", True, True, "Профессионально и сдержанно, с опорой на кейсы."),
    ("product manager", "lead"): SuggestedStyle("confident", True, True, "Уверенный тон, подчёркивающий лидерство и влияние."),
    ("product manager", "c-level"): SuggestedStyle("neutral", False, True, "Сдержанно и стратегически, без излишнего эмоционального окраса."),

    ("ux/ui designer", "junior"): SuggestedStyle("creative", True, False, "Живой и образный стиль, с акцентом на подход."),
    ("ux/ui designer", "middle"): SuggestedStyle("creative", True, False, "Креативная подача через опыт и визуальное мышление."),
    ("ux/ui designer", "senior"): SuggestedStyle("creative", True, False, "Сдержанно-креативный стиль с дизайнерской терминологией."),
    ("ux/ui designer", "lead"): SuggestedStyle("creative", True, False, "Метафоричный, но профессиональный стиль."),
    ("ux/ui designer", "c-level"): SuggestedStyle("neutral", True, False, "Выдержанный, с философией дизайна и продуктовой зрелостью."),

    ("frontend developer", "junior"): SuggestedStyle("neutral", False, True, "Простой и понятный стиль, без излишеств."),
    ("frontend developer", "middle"): SuggestedStyle("neutral", True, True, "Технически точный, с лёгким индивидуальным оттенком."),
    ("frontend developer", "senior"): SuggestedStyle("confident", True, True, "Твёрдый и зрелый тон, подчеркивающий опыт."),

    ("backend developer", "junior"): SuggestedStyle("neutral", False, True, "Фокус на понятности и аккуратности."),
    ("backend developer", "middle"): SuggestedStyle("neutral", False, True, "Без креатива, строго и по делу."),
    ("backend developer", "senior"): SuggestedStyle("confident", True, True, "Уверенный, архитектурно-прагматичный стиль."),

    ("qa engineer", "junior"): SuggestedStyle("neutral", False, True, "Строго и аккуратно, без лишнего."),
    ("qa engineer", "middle"): SuggestedStyle("neutral", True, True, "Умеренный стиль с элементами подхода."),
    ("qa engineer", "senior"): SuggestedStyle("neutral", True, True, "Профессиональный стиль с методологическим уклоном."),
    ("qa engineer", "lead"): SuggestedStyle("confident", True, True, "Уверенный тон, акцент на лидерство и процессы."),

    ("product analyst", "junior"): SuggestedStyle("neutral", False, True, "Аналитично, аккуратно, без образов."),
    ("product analyst", "middle"): SuggestedStyle("neutral", True, True, "Подача через аналитические выводы и продуктовый фокус."),
    ("product analyst", "senior"): SuggestedStyle("neutral", True, True, "Профессиональный стиль с рефлексией над влиянием."),
    ("product analyst", "lead"): SuggestedStyle("confident", True, True, "Лидершип через аналитическую ценность."),

    ("business analyst", "junior"): SuggestedStyle("neutral", False, True, "Без креатива, строго и логично."),
    ("business analyst", "middle"): SuggestedStyle("neutral", False, True, "Рационально и формально."),
    ("business analyst", "senior"): SuggestedStyle("neutral", True, True, "Зрелый аналитический стиль с выводами."),
    ("business analyst", "lead"): SuggestedStyle("confident", True, True, "Системный стиль с акцентом на бизнес-ценность."),

    ("marketing specialist", "junior"): SuggestedStyle("creative", True, False, "Живой, маркетинговый язык, акценты на вовлечении."),
    ("marketing specialist", "middle"): SuggestedStyle("creative", True, False, "Креативный стиль с элементами результативности."),
    ("marketing specialist", "senior"): SuggestedStyle("confident", True, True, "Уверенный стиль, подчёркивающий опыт и экспертизу."),
    ("marketing specialist", "lead"): SuggestedStyle("confident", True, True, "Лидерская подача с продуктовым фокусом."),

    ("cto", "c-level"): SuggestedStyle("neutral", True, True, "Стратегически выдержанный стиль с акцентом на системность."),
    ("head of design", "c-level"): SuggestedStyle("neutral", True, False, "Подача через философию дизайна, но без вольностей."),
    ("cpo", "c-level"): SuggestedStyle("neutral", False, True, "Сдержанный тон, подчёркивающий стратегическое мышление."),
}

# Правила генерации по стилю
STYLE_RULES: Dict[str, StyleRules] = {
    "creative": StyleRules(
        tone="живой, нестандартный, допускаются метафоры и неожиданные образы",
        suggestions=["используй нестандартную зацепку", "добавь немного юмора, если уместно"],
        avoid=["формальный канцелярит", "шаблонные обороты"]
    ),
    "neutral": StyleRules(
        tone="сдержанный, профессиональный, понятный человеку и читаемый быстро",
        suggestions=["упор на структуру", "используй короткие предложения, избегай художественности"],
        avoid=["метафоры", "модные словечки", "фигуры речи"]
    ),
    "confident": StyleRules(
        tone="уверенный, зрелый, с прямыми формулировками и акцентом на влияние",
        suggestions=["используй слова лидерства и влияния", "упоминай бизнес-результаты"],
        avoid=["неуверенность", "условные конструкции"]
    )
}

# Модификаторы по профессии и уровню
STYLE_MODIFIERS = {
    ("junior",): {
        "soften_confidence": True,
        "focus_on_learning": True,
        "avoid_big_claims": True
    },
    ("lead", "c-level"): {
        "highlight_impact": True,
        "use_strategy_words": True
    },
    ("designer",): {
        "allow_visual_language": True,
        "emphasize_empathy": True
    },
    ("developer",): {
        "simplify_language": True,
        "avoid_marketing_terms": True
    }
}

# Fallback стили для случаев, когда профессия/уровень не определены
DEFAULT_STYLES = {
    "neutral": SuggestedStyle("neutral", True, True, "Универсальный сбалансированный стиль"),
    "creative": SuggestedStyle("creative", True, False, "Креативный стиль для творческих ролей"),
    "formal": SuggestedStyle("neutral", False, True, "Формальный стиль для консервативных позиций")
} 