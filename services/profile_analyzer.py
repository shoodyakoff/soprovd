"""
Анализатор профилей пользователей на основе ключевых слов
"""
import re
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
import logging

from models.profile_models import AnalyzedProfile, ProfileAnalysisResult
from models.style_definitions import (
    KEYWORDS, LEVEL_KEYWORDS, STYLE_MAP, DEFAULT_STYLES
)

logger = logging.getLogger(__name__)


class ProfileAnalyzer:
    """Анализирует резюме и вакансию для определения профессии и уровня"""
    
    def __init__(self, min_confidence_threshold: float = 0.3):
        self.min_confidence_threshold = min_confidence_threshold
    
    def analyze_profile(self, job_description: str, resume: str) -> AnalyzedProfile:
        """
        Основной метод анализа профиля
        
        Args:
            job_description: Описание вакансии
            resume: Резюме кандидата
            
        Returns:
            AnalyzedProfile с определенной профессией, уровнем и стилем
        """
        # Объединяем тексты для анализа
        combined_text = f"{job_description.lower()} {resume.lower()}"
        
        # Анализируем профессию и уровень
        analysis_result = self._analyze_keywords(combined_text)
        
        # Определяем профессию и уровень
        profession = self._determine_profession(analysis_result.profession_matches)
        level = self._determine_level(analysis_result.level_matches)
        
        # Определяем стиль
        suggested_style = self._get_style_for_profile(profession, level)
        
        # Вычисляем уверенность
        confidence = self._calculate_confidence(analysis_result)
        
        # Логируем результат
        logger.info(f"Profile analysis: {profession}/{level}, confidence: {confidence:.2f}")
        
        return AnalyzedProfile(
            profession=profession,
            level=level,
            suggested_style=suggested_style,
            confidence_score=confidence,
            detected_keywords={
                "profession": list(analysis_result.profession_matches.keys()),
                "level": list(analysis_result.level_matches.keys())
            }
        )
    
    def _analyze_keywords(self, text: str) -> ProfileAnalysisResult:
        """Анализирует ключевые слова в тексте"""
        profession_matches = {}
        level_matches = {}
        total_keywords = 0
        
        # Ищем профессиональные ключевые слова
        for profession, keywords in KEYWORDS.items():
            matches = self._count_keyword_matches(text, keywords)
            if matches > 0:
                profession_matches[profession] = matches
                total_keywords += matches
        
        # Ищем ключевые слова уровня
        for level, keywords in LEVEL_KEYWORDS.items():
            matches = self._count_keyword_matches(text, keywords)
            if matches > 0:
                level_matches[level] = matches
                total_keywords += matches
        
        # Определяем уверенность
        is_confident = total_keywords >= 3 and (
            max(profession_matches.values()) if profession_matches else 0
        ) >= 2
        
        return ProfileAnalysisResult(
            profession_matches=profession_matches,
            level_matches=level_matches,
            total_keywords_found=total_keywords,
            is_confident=is_confident
        )
    
    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Подсчитывает совпадения ключевых слов в тексте"""
        matches = 0
        for keyword in keywords:
            # Ищем точные совпадения (с границами слов)
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            matches += len(re.findall(pattern, text))
        return matches
    
    def _determine_profession(self, profession_matches: Dict[str, int]) -> str:
        """Определяет профессию на основе совпадений"""
        if not profession_matches:
            return "unknown"
        
        # Возвращаем профессию с максимальным количеством совпадений
        return max(profession_matches.items(), key=lambda x: x[1])[0]
    
    def _determine_level(self, level_matches: Dict[str, int]) -> str:
        """Определяет уровень на основе совпадений"""
        if not level_matches:
            return "middle"  # По умолчанию middle
        
        # Возвращаем уровень с максимальным количеством совпадений
        return max(level_matches.items(), key=lambda x: x[1])[0]
    
    def _get_style_for_profile(self, profession: str, level: str):
        """Получает стиль для данной профессии и уровня"""
        # Ищем в STYLE_MAP
        style_key = (profession, level)
        if style_key in STYLE_MAP:
            return STYLE_MAP[style_key]
        
        # Fallback стратегии
        if profession == "unknown":
            return DEFAULT_STYLES["neutral"]
        
        # Пытаемся найти любой уровень для данной профессии
        for (prof, lvl), style in STYLE_MAP.items():
            if prof == profession:
                return style
        
        # Окончательный fallback
        return DEFAULT_STYLES["neutral"]
    
    def _calculate_confidence(self, analysis_result: ProfileAnalysisResult) -> float:
        """Вычисляет уверенность в анализе (0-1)"""
        total_keywords = analysis_result.total_keywords_found
        has_profession = bool(analysis_result.profession_matches)
        has_level = bool(analysis_result.level_matches)
        
        # Базовая уверенность на основе количества ключевых слов
        base_confidence = min(total_keywords / 10.0, 1.0)
        
        # Бонус за наличие и профессии, и уровня
        if has_profession and has_level:
            base_confidence *= 1.2
        elif has_profession or has_level:
            base_confidence *= 1.0
        else:
            base_confidence *= 0.5
        
        return min(base_confidence, 1.0)
    
    def get_fallback_styles(self) -> Dict[str, Any]:
        """Возвращает базовые стили для ручного выбора"""
        return {
            "neutral": DEFAULT_STYLES["neutral"],
            "creative": DEFAULT_STYLES["creative"], 
            "formal": DEFAULT_STYLES["formal"]
        }


# Глобальный экземпляр анализатора
analyzer = ProfileAnalyzer()


def analyze_profile(job_description: str, resume: str) -> AnalyzedProfile:
    """Удобная функция для анализа профиля"""
    return analyzer.analyze_profile(job_description, resume) 