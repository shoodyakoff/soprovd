-- =====================================================
-- ОЧИСТКА БАЗЫ ДАННЫХ v7.3
-- Удаление устаревших полей и улучшение схемы подписок
-- =====================================================

BEGIN;

-- =====================================================
-- 1. УДАЛЕНИЕ УСТАРЕВШИХ ПОЛЕЙ ИЗ letter_sessions
-- =====================================================

-- Проверяем и удаляем устаревшие поля
DO $$ 
BEGIN
    -- final_rating - не используется в v7.2
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='final_rating') THEN
        ALTER TABLE letter_sessions DROP COLUMN final_rating;
        RAISE NOTICE 'Удалено поле final_rating из letter_sessions';
    END IF;
    
    -- regeneration_count - заменено на letter_iterations
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='regeneration_count') THEN
        ALTER TABLE letter_sessions DROP COLUMN regeneration_count;
        RAISE NOTICE 'Удалено поле regeneration_count из letter_sessions';
    END IF;
    
    -- user_regenerated - заменено на letter_iterations
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='user_regenerated') THEN
        ALTER TABLE letter_sessions DROP COLUMN user_regenerated;
        RAISE NOTICE 'Удалено поле user_regenerated из letter_sessions';
    END IF;
END $$;

-- =====================================================
-- 2. УЛУЧШЕНИЕ СХЕМЫ ПОДПИСОК - ИСТОРИЯ ПОДПИСОК
-- =====================================================

-- Сначала сохраняем существующие данные
CREATE TABLE subscriptions_backup AS SELECT * FROM subscriptions;

-- Удаляем UNIQUE constraint для user_id
ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_user_id_key;

-- Добавляем новые поля для истории подписок
DO $$
BEGIN
    -- Активность подписки
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscriptions' AND column_name='is_active') THEN
        ALTER TABLE subscriptions ADD COLUMN is_active BOOLEAN DEFAULT true;
    END IF;
    
    -- Причина отмены
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscriptions' AND column_name='cancellation_reason') THEN
        ALTER TABLE subscriptions ADD COLUMN cancellation_reason VARCHAR(100);
    END IF;
    
    -- Дата отмены
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscriptions' AND column_name='cancelled_at') THEN
        ALTER TABLE subscriptions ADD COLUMN cancelled_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Источник подписки
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscriptions' AND column_name='source') THEN
        ALTER TABLE subscriptions ADD COLUMN source VARCHAR(100) DEFAULT 'manual';
    END IF;
    
    -- ID предыдущей подписки (для upgrade/downgrade)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscriptions' AND column_name='previous_subscription_id') THEN
        ALTER TABLE subscriptions ADD COLUMN previous_subscription_id INTEGER REFERENCES subscriptions(id);
    END IF;
END $$;

-- Помечаем все существующие подписки как активные
UPDATE subscriptions SET is_active = true WHERE is_active IS NULL;

-- Создаем UNIQUE constraint только для активных подписок
CREATE UNIQUE INDEX idx_subscriptions_user_active 
ON subscriptions(user_id) 
WHERE is_active = true;

-- =====================================================
-- 3. ТАБЛИЦА КАНАЛОВ ПРИВЛЕЧЕНИЯ
-- =====================================================

CREATE TABLE IF NOT EXISTS acquisition_channels (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- UTM параметры
    utm_source VARCHAR(100),        -- telegram, google, facebook
    utm_medium VARCHAR(100),        -- cpc, social, referral
    utm_campaign VARCHAR(100),      -- winter_promo, dev_community
    utm_content VARCHAR(100),       -- banner_1, post_123
    utm_term VARCHAR(100),          -- cover letter, резюме
    
    -- Дополнительные параметры
    referrer_url TEXT,              -- откуда пришел
    landing_page VARCHAR(255),      -- на какую страницу попал
    device_type VARCHAR(50),        -- mobile, desktop
    
    -- Telegram специфичные
    telegram_start_param VARCHAR(100), -- /start параметр
    referral_user_id INTEGER REFERENCES users(id), -- кто пригласил
    
    -- Метрики
    session_count INTEGER DEFAULT 0,
    first_session_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_session_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для аналитики
CREATE INDEX idx_acquisition_user ON acquisition_channels(user_id);
CREATE INDEX idx_acquisition_source ON acquisition_channels(utm_source);
CREATE INDEX idx_acquisition_campaign ON acquisition_channels(utm_campaign);
CREATE INDEX idx_acquisition_referral ON acquisition_channels(referral_user_id);

-- =====================================================
-- 4. ОБНОВЛЕНИЕ letter_sessions - ДОБАВЛЯЕМ subscription_id
-- =====================================================

-- Заполняем subscription_id для существующих сессий
UPDATE letter_sessions 
SET subscription_id = (
    SELECT s.id 
    FROM subscriptions s 
    WHERE s.user_id = letter_sessions.user_id 
    AND s.is_active = true 
    LIMIT 1
)
WHERE subscription_id IS NULL;

-- =====================================================
-- 5. НОВЫЕ АНАЛИТИЧЕСКИЕ ПРЕДСТАВЛЕНИЯ
-- =====================================================

-- Обновляем subscription_stats с учетом истории
DROP VIEW IF EXISTS subscription_stats;
CREATE OR REPLACE VIEW subscription_stats AS
SELECT 
    plan_type,
    status,
    is_active,
    COUNT(*) as count,
    AVG(letters_used::numeric) as avg_letters_used,
    SUM(letters_used) as total_letters_used,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_this_month,
    COUNT(*) FILTER (WHERE cancelled_at IS NOT NULL) as cancelled_count
FROM subscriptions 
GROUP BY plan_type, status, is_active;

-- Статистика каналов привлечения
CREATE OR REPLACE VIEW acquisition_stats AS
SELECT 
    utm_source,
    utm_campaign,
    COUNT(DISTINCT ac.user_id) as users,
    AVG(ac.session_count) as avg_sessions_per_user,
    COUNT(DISTINCT s.user_id) as converted_users,
    COUNT(DISTINCT s.user_id) * 100.0 / COUNT(DISTINCT ac.user_id) as conversion_rate
FROM acquisition_channels ac
LEFT JOIN subscriptions s ON ac.user_id = s.user_id AND s.plan_type = 'premium'
GROUP BY utm_source, utm_campaign;

-- Когорты пользователей (базовая версия)
CREATE OR REPLACE VIEW user_cohorts_basic AS
SELECT 
    DATE_TRUNC('month', u.created_at) as cohort_month,
    ac.utm_source as acquisition_channel,
    COUNT(*) as cohort_size,
    COUNT(ls.user_id) as activated_users,
    COUNT(s.user_id) as premium_users,
    AVG(EXTRACT(days FROM ls.created_at - u.created_at)) as avg_days_to_first_letter
FROM users u
LEFT JOIN acquisition_channels ac ON u.id = ac.user_id
LEFT JOIN letter_sessions ls ON u.id = ls.user_id
LEFT JOIN subscriptions s ON u.id = s.user_id AND s.plan_type = 'premium'
GROUP BY DATE_TRUNC('month', u.created_at), ac.utm_source;

-- =====================================================
-- 6. ФУНКЦИИ ДЛЯ РАБОТЫ С ПОДПИСКАМИ
-- =====================================================

-- Функция для смены подписки
CREATE OR REPLACE FUNCTION change_subscription(
    p_user_id INTEGER,
    p_new_plan_type VARCHAR(20),
    p_reason VARCHAR(100) DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    old_subscription_id INTEGER;
    new_subscription_id INTEGER;
BEGIN
    -- Деактивируем старую подписку
    UPDATE subscriptions 
    SET is_active = false, 
        cancelled_at = NOW(),
        cancellation_reason = p_reason
    WHERE user_id = p_user_id AND is_active = true
    RETURNING id INTO old_subscription_id;
    
    -- Создаем новую подписку
    INSERT INTO subscriptions (
        user_id, 
        plan_type, 
        status, 
        letters_limit,
        letters_used,
        is_active,
        previous_subscription_id,
        source
    ) VALUES (
        p_user_id,
        p_new_plan_type,
        'active',
        CASE WHEN p_new_plan_type = 'premium' THEN 20 ELSE 3 END,
        0,
        true,
        old_subscription_id,
        'upgrade'
    ) RETURNING id INTO new_subscription_id;
    
    RETURN new_subscription_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. ПРОВЕРКА И ФИНАЛИЗАЦИЯ
-- =====================================================

-- Проверяем что все пользователи имеют активную подписку
INSERT INTO subscriptions (user_id, plan_type, status, letters_limit, letters_used, is_active)
SELECT 
    u.id,
    'free',
    'active',
    3,
    0,
    true
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM subscriptions s 
    WHERE s.user_id = u.id AND s.is_active = true
);

-- Финальная статистика
DO $$
DECLARE
    total_users INTEGER;
    active_subscriptions INTEGER;
    removed_fields INTEGER := 3; -- final_rating, regeneration_count, user_regenerated
BEGIN
    SELECT COUNT(*) INTO total_users FROM users;
    SELECT COUNT(*) INTO active_subscriptions FROM subscriptions WHERE is_active = true;
    
    RAISE NOTICE '================================';
    RAISE NOTICE 'МИГРАЦИЯ v7.3 ЗАВЕРШЕНА';
    RAISE NOTICE '================================';
    RAISE NOTICE 'Удалено устаревших полей: %', removed_fields;
    RAISE NOTICE 'Всего пользователей: %', total_users;
    RAISE NOTICE 'Активных подписок: %', active_subscriptions;
    RAISE NOTICE 'Создана таблица acquisition_channels';
    RAISE NOTICE 'Обновлена схема subscriptions (история)';
    RAISE NOTICE 'Созданы новые представления для аналитики';
    RAISE NOTICE '================================';
END $$;

COMMIT; 