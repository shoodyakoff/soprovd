"""
Inline-клавиатуры для бота
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_style_keyboard():
    """
    Создает inline-клавиатуру для выбора стиля письма
    """
    keyboard = [
        [InlineKeyboardButton("Нейтральный", callback_data="style_neutral")],
        [InlineKeyboardButton("Смелый", callback_data="style_bold")],
        [InlineKeyboardButton("Формальный", callback_data="style_formal")],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_main_menu():
    """
    Создает главное меню выбора режима
    """
    keyboard = [
        [InlineKeyboardButton("🔥 Умный генератор v3.0", callback_data="mode_v3")],
        [InlineKeyboardButton("🎯 Персонализированный", callback_data="mode_personalized")],
        [InlineKeyboardButton("⚡ Классический", callback_data="mode_classic")],
    ]
    
    return InlineKeyboardMarkup(keyboard) 