"""
Inline-клавиатуры для бота Сопровод v7.2
Упрощенная система оценок: только лайки/дизлайки
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_simple_keyboard():
    """
    Заглушка для совместимости
    В v4.0 не используются клавиатуры
    """
    return None

def get_restart_keyboard():
    """Клавиатура с кнопкой 'Начать заново'"""
    keyboard = [
        [InlineKeyboardButton("🔄 Начать заново", callback_data="restart")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_retry_keyboard(session_id: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой повторной генерации
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Повторить генерацию", 
                callback_data=f"retry_generation_{session_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🆕 Создать новое письмо", 
                callback_data="restart"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_feedback_keyboard(session_id: str, iteration: int):
    """Клавиатура для оценки письма - ТОЛЬКО лайки/дизлайки"""
    keyboard = [
        [
            InlineKeyboardButton("❤️ Нравится", callback_data=f"feedback_like_{session_id}_{iteration}"),
            InlineKeyboardButton("👎 Не подходит", callback_data=f"feedback_dislike_{session_id}_{iteration}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_iteration_keyboard(session_id: str, remaining_iterations: int):
    """Клавиатура для действий после обратной связи - ТОЛЬКО 2 кнопки"""
    keyboard = []
    
    if remaining_iterations > 0:
        keyboard.append([
            InlineKeyboardButton("🔄 Улучшить письмо", callback_data=f"improve_letter_{session_id}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🆕 Создать новое письмо", callback_data="restart")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_final_letter_keyboard():
    """Клавиатура для финального письма (без возможности улучшения)"""
    keyboard = [
        [InlineKeyboardButton("🆕 Создать новое письмо", callback_data="restart")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_start_work_keyboard():
    """Клавиатура для начала работы с ботом вне активной сессии"""
    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Создать сопроводительное письмо", 
                callback_data="start_work"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard) 