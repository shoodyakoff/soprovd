"""
Модели данных для анализа профилей пользователей
"""
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List


@dataclass
class SuggestedStyle:
    """Предлагаемый стиль письма с настройками"""
    style: str  # 'neutral', 'confident', 'creative'
    allow_creativity: bool
    allow_formalism: bool
    tone_description: str


@dataclass
class AnalyzedProfile:
    """Результат анализа профиля пользователя"""
    profession: str
    level: str
    suggested_style: SuggestedStyle
    confidence_score: float = 0.0  # Уверенность в определении (0-1)
    detected_keywords: Optional[Dict[str, List[str]]] = None  # Какие ключевые слова нашли
    
    def __post_init__(self):
        if self.detected_keywords is None:
            self.detected_keywords = {}


@dataclass
class StyleRules:
    """Правила генерации по стилю"""
    tone: str
    suggestions: List[str]
    avoid: List[str]


@dataclass 
class ProfileAnalysisResult:
    """Детальный результат анализа для отладки"""
    profession_matches: Dict[str, int]  # профессия -> кол-во совпадений
    level_matches: Dict[str, int]      # уровень -> кол-во совпадений
    total_keywords_found: int
    is_confident: bool                 # Уверены ли в результате
    fallback_used: bool = False        # Использовали ли fallback 