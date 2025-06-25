-- =====================================================
-- РУЧНОЕ УПРАВЛЕНИЕ ПОДПИСКАМИ ПОЛЬЗОВАТЕЛЕЙ
-- =====================================================

-- 1. ПРОСМОТР ВСЕХ ПОДПИСОК
SELECT 
    s.id,
    s.user_id,
    u.username,
    u.first_name,
    s.plan_type,
    s.status,
    s.letters_limit,
    s.letters_used,
    s.period_start,
    s.period_end,
    s.created_at
FROM subscriptions s
JOIN users u ON s.user_id = u.id
ORDER BY s.created_at DESC;

-- 2. НАЙТИ ПОЛЬЗОВАТЕЛЯ ПО TELEGRAM USERNAME
SELECT 
    u.id,
    u.telegram_user_id,
    u.username,
    u.first_name,
    s.plan_type,
    s.status,
    s.letters_used,
    s.letters_limit
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id
WHERE u.username = 'YOUR_USERNAME_HERE'  -- Замените на нужный username
   OR u.first_name ILIKE '%YOUR_NAME%';   -- Или поиск по имени

-- 3. ДАТЬ ПОЛЬЗОВАТЕЛЮ ПРЕМИУМ ПОДПИСКУ
-- Замените USER_ID на реальный ID пользователя
UPDATE subscriptions 
SET 
    plan_type = 'premium',
    status = 'active',
    letters_limit = 20,  -- 20 писем в день для премиум
    period_start = CURRENT_DATE,
    period_end = CURRENT_DATE + INTERVAL '1 day',
    updated_at = NOW()
WHERE user_id = USER_ID_HERE;

-- 4. СБРОСИТЬ СЧЕТЧИК ИСПОЛЬЗОВАННЫХ ПИСЕМ
UPDATE subscriptions 
SET 
    letters_used = 0,
    updated_at = NOW()
WHERE user_id = USER_ID_HERE;

-- 5. ВЕРНУТЬ ПОЛЬЗОВАТЕЛЯ НА БЕСПЛАТНЫЙ ПЛАН
UPDATE subscriptions 
SET 
    plan_type = 'free',
    status = 'active',
    letters_limit = 3,  -- 3 письма в месяц для free
    letters_used = 0,
    period_start = DATE_TRUNC('month', CURRENT_DATE),
    period_end = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month',
    updated_at = NOW()
WHERE user_id = USER_ID_HERE;

-- 6. ЗАБЛОКИРОВАТЬ ПОЛЬЗОВАТЕЛЯ
UPDATE subscriptions 
SET 
    status = 'cancelled',
    updated_at = NOW()
WHERE user_id = USER_ID_HERE;

-- 7. РАЗБЛОКИРОВАТЬ ПОЛЬЗОВАТЕЛЯ
UPDATE subscriptions 
SET 
    status = 'active',
    updated_at = NOW()
WHERE user_id = USER_ID_HERE;

-- 8. СТАТИСТИКА ИСПОЛЬЗОВАНИЯ
SELECT 
    plan_type,
    COUNT(*) as users_count,
    AVG(letters_used) as avg_letters_used,
    SUM(letters_used) as total_letters_used,
    COUNT(CASE WHEN letters_used >= letters_limit THEN 1 END) as users_at_limit
FROM subscriptions 
WHERE status = 'active'
GROUP BY plan_type;

-- 9. ПОЛЬЗОВАТЕЛИ, КОТОРЫЕ ИСЧЕРПАЛИ ЛИМИТ
SELECT 
    u.username,
    u.first_name,
    s.letters_used,
    s.letters_limit,
    s.plan_type,
    s.updated_at
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE s.letters_used >= s.letters_limit 
  AND s.status = 'active'
ORDER BY s.updated_at DESC;

-- 10. АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ ЗА ПОСЛЕДНИЕ 7 ДНЕЙ
SELECT 
    u.username,
    u.first_name,
    s.plan_type,
    s.letters_used,
    COUNT(ls.id) as sessions_count,
    MAX(ls.created_at) as last_session
FROM users u
JOIN subscriptions s ON u.id = s.user_id
LEFT JOIN letter_sessions ls ON u.id = ls.user_id
WHERE ls.created_at >= NOW() - INTERVAL '7 days'
GROUP BY u.id, u.username, u.first_name, s.plan_type, s.letters_used
ORDER BY sessions_count DESC;

-- =====================================================
-- БЫСТРЫЕ КОМАНДЫ ДЛЯ ЧАСТОГО ИСПОЛЬЗОВАНИЯ
-- =====================================================

-- ДАТЬ ПРЕМИУМ КОНКРЕТНОМУ ПОЛЬЗОВАТЕЛЮ (по username)
/*
UPDATE subscriptions 
SET 
    plan_type = 'premium',
    letters_limit = 20,  -- 20 писем в день для премиум
    period_end = CURRENT_DATE + INTERVAL '1 day'
WHERE user_id = (
    SELECT id FROM users WHERE username = 'username_here'
);
*/

-- СБРОСИТЬ ЛИМИТЫ ВСЕМ ПОЛЬЗОВАТЕЛЯМ (начало месяца)
/*
UPDATE subscriptions 
SET 
    letters_used = 0,
    period_start = NOW(),
    period_end = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
WHERE status = 'active';
*/ 