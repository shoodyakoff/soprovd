-- Скрипт для сброса пользователя на FREE план (DEV база)
-- Пользователь: 678674926 (shoodyakoff)

-- 1. Обновляем подписку на FREE план
UPDATE subscriptions 
SET 
    plan_type = 'free',
    letters_limit = 3,  -- ИСПРАВЛЕНИЕ: FREE план = 3 письма
    letters_used = 0,  -- Сбрасываем использованные письма
    period_start = CURRENT_DATE,
    period_end = (CURRENT_DATE + INTERVAL '1 month')::date,  -- Месячный период для FREE
    updated_at = NOW()
WHERE user_id = (
    SELECT id FROM users WHERE telegram_user_id = 678674926
);

-- 2. Проверяем результат
SELECT 
    u.telegram_user_id,
    u.username,
    s.plan_type,
    s.letters_limit,  -- Добавлено для проверки лимита
    s.letters_used,
    s.period_start,
    s.period_end,
    s.updated_at
FROM users u
JOIN subscriptions s ON u.id = s.user_id
WHERE u.telegram_user_id = 678674926;

-- 3. Дополнительно: очищаем активные сессии если нужно (опционально)
-- UPDATE letter_sessions 
-- SET status = 'completed'
-- WHERE user_id = (SELECT id FROM users WHERE telegram_user_id = 678674926)
--   AND status = 'active'; 