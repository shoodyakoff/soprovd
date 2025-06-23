"""
Smart Analyzer v6.0 - Чистая версия
Только рабочая логика без legacy кода

АРХИТЕКТУРА:
1. Анализ вакансии (структурированный)
2. Анализ резюме (структурированный) 
3. Анализ совпадений (точные матчи)
4. Генерация письма (связная история)
5. Де-ИИ-фикация (убираем штампы)

ПУБЛИЧНЫЕ ФУНКЦИИ:
- analyze_and_generate_with_analysis() - основная функция продакшна
"""

import json
import logging
from typing import Dict, Any, Optional

from utils.prompts import (
    VACANCY_ANALYSIS_PROMPT,
    RESUME_ANALYSIS_PROMPT, 
    MATCHING_ANALYSIS_PROMPT,
    LETTER_GENERATION_PROMPT,
    DEAI_PROMPT
)

logger = logging.getLogger(__name__)


class SmartAnalyzer:
    """Умный анализатор v6.0 - только рабочая логика"""
    
    def __init__(self, openai_service):
        self.openai = openai_service
    
    async def generate_full_analysis_and_letter(
        self,
        vacancy_text: str,
        resume_text: str,
        style: str = "professional"
    ) -> Dict[str, str]:
        """
        Основной метод: 4-этапный анализ + генерация письма
        
        Returns:
            Dict с письмом и анализом: {'letter': str, 'analysis': str}
        """
        logger.info("🚀 Запускаю 4-этапный анализ v6.0...")
        logger.info(f"📊 Входные данные: вакансия={len(vacancy_text)} символов, резюме={len(resume_text)} символов")
        
        # ЭТАП 1: Анализ вакансии
        logger.info("🔍 ЭТАП 1: Анализ вакансии...")
        vacancy_analysis = await self._analyze_vacancy(vacancy_text)
        logger.info("✅ ЭТАП 1 завершен")
        
        # ЭТАП 2: Анализ резюме  
        logger.info("👤 ЭТАП 2: Анализ резюме...")
        resume_analysis = await self._analyze_resume(resume_text)
        logger.info("✅ ЭТАП 2 завершен")
        
        # ЭТАП 3: Анализ совпадений
        logger.info("⚡ ЭТАП 3: Анализ совпадений...")
        matching_analysis = await self._analyze_matching(vacancy_analysis, resume_analysis)
        logger.info("✅ ЭТАП 3 завершен")
        
        # ЭТАП 4: Генерация письма
        logger.info("✍️ ЭТАП 4: Генерация письма...")
        letter = await self._generate_letter(matching_analysis)
        logger.info(f"✅ ЭТАП 4 завершен. Длина письма: {len(letter)} символов")
        
        # ЭТАП 5: Де-ИИ-фикация
        logger.info("🔧 ЭТАП 5: Де-ИИ-фикация...")
        final_letter = await self._deai_text(letter)
        logger.info(f"✅ ЭТАП 5 завершен. Финальная длина: {len(final_letter)} символов")
        
        # Форматируем анализ для пользователя
        formatted_analysis = self._format_analysis(matching_analysis)
        
        logger.info("🎉 4-этапный анализ v6.0 завершен!")
        return {
            'letter': final_letter,
            'analysis': formatted_analysis
        }
    
    # ============ ПРИВАТНЫЕ МЕТОДЫ ЭТАПОВ ============
    
    async def _analyze_vacancy(self, vacancy_text: str) -> Dict[str, Any]:
        """ЭТАП 1: Структурированный анализ вакансии"""
        prompt = VACANCY_ANALYSIS_PROMPT.format(vacancy_text=vacancy_text)
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            if not response:
                logger.error("❌ Пустой ответ при анализе вакансии")
                return self._fallback_vacancy()
            
            return self._parse_json(response, "vacancy")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа вакансии: {e}")
            return self._fallback_vacancy()
    
    async def _analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """ЭТАП 2: Структурированный анализ резюме"""
        prompt = RESUME_ANALYSIS_PROMPT.format(resume_text=resume_text)
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            if not response:
                logger.error("❌ Пустой ответ при анализе резюме")
                return self._fallback_resume()
            
            return self._parse_json(response, "resume")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа резюме: {e}")
            return self._fallback_resume()
    
    async def _analyze_matching(
        self, 
        vacancy_analysis: Dict[str, Any], 
        resume_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ЭТАП 3: Детальный анализ совпадений"""
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
                logger.error("❌ Пустой ответ при анализе совпадений")
                return self._fallback_matching()
            
            return self._parse_json(response, "matching")
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа совпадений: {e}")
            return self._fallback_matching()
    
    async def _generate_letter(self, matching_analysis: Dict[str, Any]) -> str:
        """ЭТАП 4: Генерация письма на основе анализа"""
        prompt = LETTER_GENERATION_PROMPT.format(
            matching_analysis=json.dumps(matching_analysis, ensure_ascii=False, indent=2)
        )
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1500
            )
            
            if not response:
                logger.error("❌ Пустой ответ при генерации письма")
                raise Exception("Пустой ответ от GPT")
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации письма: {e}")
            raise
    
    async def _deai_text(self, text: str) -> str:
        """ЭТАП 5: Де-ИИ-фикация текста"""
        prompt = DEAI_PROMPT.format(text=text)
        
        try:
            response = await self.openai.get_completion(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1500
            )
            
            if not response:
                logger.warning("❌ Пустой ответ при де-ИИ-фикации, возвращаю исходный текст")
                return text
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка де-ИИ-фикации: {e}")
            return text  # Возвращаем исходный текст при ошибке
    
    # ============ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ============
    
    def _parse_json(self, response: str, stage: str) -> Dict[str, Any]:
        """Безопасный парсинг JSON ответа"""
        try:
            # Очищаем от markdown блоков
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            parsed = json.loads(cleaned)
            logger.info(f"✅ JSON успешно распарсен для {stage}")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка JSON для {stage}: {e}")
            logger.error(f"Ответ: {response[:200]}...")
            
            # Возвращаем fallback
            if stage == "vacancy":
                return self._fallback_vacancy()
            elif stage == "resume":
                return self._fallback_resume()
            elif stage == "matching":
                return self._fallback_matching()
            else:
                return {}
    
    def _format_analysis(self, matching_analysis: Dict[str, Any]) -> str:
        """Форматирование анализа для пользователя"""
        try:
            summary = "📊 АНАЛИЗ СОВПАДЕНИЙ ВАКАНСИИ И РЕЗЮМЕ\n\n"
            
            # Прямые совпадения
            exact_matches = matching_analysis.get('exact_matches', [])
            if exact_matches:
                summary += "✅ ПРЯМЫЕ СОВПАДЕНИЯ:\n"
                for match in exact_matches[:5]:
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
                    if isinstance(gap, dict):
                        summary += f"• {gap.get('missing_requirement', 'Пробел в навыках')}\n"
                    else:
                        summary += f"• {gap}\n"
                summary += "\n"
            
            # Уникальные преимущества
            advantages = matching_analysis.get('unique_advantages', [])
            if advantages:
                summary += "🎯 УНИКАЛЬНЫЕ ПРЕИМУЩЕСТВА:\n"
                for advantage in advantages[:3]:
                    if isinstance(advantage, dict):
                        summary += f"• {advantage.get('advantage', 'Дополнительная ценность')}\n"
                    else:
                        summary += f"• {advantage}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования анализа: {e}")
            return "📊 Анализ совпадений выполнен, но возникла ошибка форматирования."
    
    # ============ FALLBACK ДАННЫЕ ============
    
    def _fallback_vacancy(self) -> Dict[str, Any]:
        """Fallback данные для анализа вакансии"""
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
    
    def _fallback_resume(self) -> Dict[str, Any]:
        """Fallback данные для анализа резюме"""
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
    
    def _fallback_matching(self) -> Dict[str, Any]:
        """Fallback данные для анализа совпадений"""
        return {
            "exact_matches": [
                {
                    "vacancy_requirement": "профессиональный опыт",
                    "resume_match": "имеется опыт работы",
                    "evidence": "подтверждается резюме",
                    "relevance_score": 0.95,
                    "bridge_explanation": "опыт применим к новой роли"
                }
            ],
            "strong_matches": [
                {
                    "vacancy_requirement": "профессиональные навыки",
                    "resume_match": "релевантные компетенции",
                    "evidence": "описано в резюме",
                    "relevance_score": 0.8,
                    "bridge_explanation": "навыки переносимы"
                }
            ],
            "weak_matches": [],
            "critical_gaps": [],
            "unique_advantages": ["профессиональная экспертиза"]
        }


# ============ ГЛОБАЛЬНЫЕ ФУНКЦИИ ============

# Единственный глобальный экземпляр
_analyzer_instance: Optional[SmartAnalyzer] = None


def _get_analyzer(openai_service=None) -> SmartAnalyzer:
    """Получить глобальный экземпляр анализатора"""
    global _analyzer_instance
    
    if _analyzer_instance is None:
        if openai_service is None:
            from services.openai_service import openai_service as default_service
            openai_service = default_service
        _analyzer_instance = SmartAnalyzer(openai_service)
    
    return _analyzer_instance


async def analyze_and_generate_with_analysis(
    vacancy_text: str,
    resume_text: str,
    style: str = "professional",
    openai_service=None
) -> Dict[str, str]:
    """
    ЕДИНСТВЕННАЯ ПУБЛИЧНАЯ ФУНКЦИЯ для продакшна
    
    Args:
        vacancy_text: Текст вакансии
        resume_text: Текст резюме  
        style: Стиль письма (не используется, оставлен для совместимости)
        openai_service: Сервис OpenAI (опционально)
        
    Returns:
        Dict с письмом и анализом: {'letter': str, 'analysis': str}
    """
    analyzer = _get_analyzer(openai_service)
    return await analyzer.generate_full_analysis_and_letter(vacancy_text, resume_text, style) 