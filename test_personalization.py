"""
Простой тест системы персонализации
"""
from services.profile_analyzer import analyze_profile
from services.personalized_prompt import generate_personalized_prompt


def test_profile_analysis():
    """Тестируем анализ профиля"""
    
    # Тестовые данные
    job_description = """
    Ищем Senior Product Manager для развития мобильного продукта.
    Требования:
    - Опыт работы с MVP и гипотезами
    - Умение строить roadmap и работать с backlog
    - Опыт product discovery и delivery
    - Знание метрик и аналитики
    """
    
    resume = """
    Иван Петров, Product Manager
    Опыт работы: 5 лет
    
    - Руководил разработкой MVP для финтех-стартапа
    - Отвечал за весь цикл от discovery до delivery  
    - Построил product roadmap на 2 года вперед
    - Запустил A/B тесты, увеличил конверсию на 25%
    - Работал с backlog, приоритизировал фичи
    """
    
    print("=== ТЕСТ АНАЛИЗА ПРОФИЛЯ ===")
    print(f"Описание вакансии: {job_description}")
    print(f"Резюме: {resume}")
    print()
    
    # Анализируем профиль
    profile = analyze_profile(job_description, resume)
    
    print("=== РЕЗУЛЬТАТ АНАЛИЗА ===")
    print(f"Профессия: {profile.profession}")
    print(f"Уровень: {profile.level}")  
    print(f"Стиль: {profile.suggested_style.style}")
    print(f"Описание стиля: {profile.suggested_style.tone_description}")
    print(f"Уверенность: {profile.confidence_score:.2f}")
    print(f"Найденные ключевые слова: {profile.detected_keywords}")
    print()
    
    # Генерируем промпт
    prompt = generate_personalized_prompt(job_description, resume, profile)
    
    print("=== СГЕНЕРИРОВАННЫЙ ПРОМПТ ===")
    print(prompt)
    print()
    
    return profile, prompt


def test_fallback_scenario():
    """Тестируем fallback сценарий"""
    
    job_description = "Требуется специалист для работы в офисе"
    resume = "Хочу работать, имею высшее образование"
    
    print("=== ТЕСТ FALLBACK СЦЕНАРИЯ ===")
    print(f"Описание вакансии: {job_description}")
    print(f"Резюме: {resume}")
    print()
    
    profile = analyze_profile(job_description, resume)
    
    print("=== РЕЗУЛЬТАТ FALLBACK ===")
    print(f"Профессия: {profile.profession}")
    print(f"Уровень: {profile.level}")
    print(f"Стиль: {profile.suggested_style.style}")
    print(f"Уверенность: {profile.confidence_score:.2f}")
    print()


def test_designer_profile():
    """Тестируем профиль дизайнера"""
    
    job_description = """
    Middle UX/UI Designer в продуктовую команду
    - Создание wireframe и prototype в Figma
    - Проектирование user flow
    - Работа с дизайн-системой
    """
    
    resume = """
    Анна Дизайнова, UX/UI Designer
    - Создавала wireframe для е-commerce проекта
    - Проектировала user flow для 5 продуктов  
    - Вела дизайн-систему в Figma
    - Отвечала за UX исследования
    """
    
    print("=== ТЕСТ ПРОФИЛЯ ДИЗАЙНЕРА ===")
    
    profile = analyze_profile(job_description, resume)
    
    print(f"Профессия: {profile.profession}")
    print(f"Уровень: {profile.level}")
    print(f"Стиль: {profile.suggested_style.style}")
    print(f"Описание: {profile.suggested_style.tone_description}")
    print()


if __name__ == "__main__":
    print("🚀 Запуск тестов системы персонализации\n")
    
    try:
        # Основной тест
        test_profile_analysis()
        
        # Fallback тест  
        test_fallback_scenario()
        
        # Тест дизайнера
        test_designer_profile()
        
        print("✅ Все тесты выполнены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()