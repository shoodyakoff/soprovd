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

# ============================================================================
# PREMIUM KEYBOARDS v9.3 - МОНЕТИЗАЦИЯ
# ============================================================================

def get_limit_reached_keyboard():
    """Клавиатура при исчерпании лимита - ГЛАВНЫЙ touchpoint"""
    keyboard = [
        [
            InlineKeyboardButton("Получить Premium", callback_data="premium_inquiry"),
            InlineKeyboardButton("Связаться с нами", callback_data="contact_support")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_post_generation_keyboard(session_id: str, iteration: int):
    """Клавиатура после генерации - SOFT SELL touchpoint"""
    keyboard = [
        [
            InlineKeyboardButton("❤️ Нравится", callback_data=f"feedback_like_{session_id}_{iteration}"),
            InlineKeyboardButton("👎 Не подходит", callback_data=f"feedback_dislike_{session_id}_{iteration}")
        ],
        [
            InlineKeyboardButton("Узнать о Premium", callback_data="premium_info")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_iteration_upsell_keyboard(session_id: str, remaining_iterations: int):
    """Клавиатура для повторных запросов - UPSELL touchpoint"""
    keyboard = []
    
    if remaining_iterations > 0:
        keyboard.append([
            InlineKeyboardButton("🔄 Улучшить письмо", callback_data=f"improve_letter_{session_id}")
        ])
        keyboard.append([
            InlineKeyboardButton("Разблокировать лимиты", callback_data="unlock_limits")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("Разблокировать лимиты", callback_data="unlock_limits")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🆕 Создать новое письмо", callback_data="restart")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_premium_info_keyboard():
    """Клавиатура для детальной информации о Premium"""
    keyboard = [
        [
            InlineKeyboardButton("Получить Premium", callback_data="premium_inquiry"),
            InlineKeyboardButton("Связаться с нами", callback_data="contact_support")
        ],
        [
            InlineKeyboardButton("◀️ Вернуться к боту", callback_data="back_to_bot")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================================================
# ЮKASSA PAYMENT KEYBOARDS v10.1 - АВТОМАТИЧЕСКИЕ ПЛАТЕЖИ
# ============================================================================

def get_payment_keyboard(payment_url: str):
    """Клавиатура для оплаты Premium через ЮKassa"""
    keyboard = [
        [
            InlineKeyboardButton("💳 Оплатить 199₽", url=payment_url)
        ],
        [
            InlineKeyboardButton("❌ Отменить", callback_data="cancel_payment")
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_premium")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_success_keyboard():
    """Клавиатура после успешной оплаты"""
    keyboard = [
        [
            InlineKeyboardButton("✍️ Написать сопроводительное", callback_data="start_work")
        ],
        [
            InlineKeyboardButton("📊 Моя подписка", callback_data="subscription_info")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_error_keyboard():
    """Клавиатура при ошибке оплаты"""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Попробовать снова", callback_data="retry_payment")
        ],
        [
            InlineKeyboardButton("📞 Написать в поддержку", callback_data="contact_support")
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_premium")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_processing_keyboard():
    """Клавиатура во время обработки платежа"""
    keyboard = [
        [
            InlineKeyboardButton("⏳ Обрабатывается...", callback_data="payment_processing")
        ],
        [
            InlineKeyboardButton("📞 Поддержка", callback_data="contact_support")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_premium_activation_keyboard():
    """Клавиатура после активации Premium подписки"""
    keyboard = [
        [
            InlineKeyboardButton("✍️ Написать сопроводительное", callback_data="start_work")
        ],
        [
            InlineKeyboardButton("📊 Моя подписка", callback_data="subscription_info")
        ]
    ]
    return InlineKeyboardMarkup(keyboard) 