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