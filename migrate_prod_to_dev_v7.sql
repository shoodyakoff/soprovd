-- =====================================================
-- ИСПРАВЛЕННАЯ МИГРАЦИЯ: PROD → DEV v7.x
-- Учитывает все различия между prod и dev схемами
-- =====================================================

BEGIN;

-- 0. Включаем расширение UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. ИСПРАВЛЕНИЕ ТИПОВ ID (КРИТИЧНО!)
-- =====================================================

-- Изменяем users.id с INTEGER на BIGINT
ALTER TABLE users ALTER COLUMN id TYPE BIGINT;

-- Обновляем все связанные поля user_id
ALTER TABLE letter_sessions ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE user_events ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE error_logs ALTER COLUMN user_id TYPE BIGINT;
ALTER TABLE openai_requests ALTER COLUMN user_id TYPE BIGINT;

-- Изменяем PRIMARY KEY полей с INTEGER на UUID где нужно
-- error_logs: id INTEGER → UUID
ALTER TABLE error_logs ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
UPDATE error_logs SET new_id = gen_random_uuid();
ALTER TABLE error_logs DROP CONSTRAINT error_logs_pkey;
ALTER TABLE error_logs DROP COLUMN id;
ALTER TABLE error_logs RENAME COLUMN new_id TO id;
ALTER TABLE error_logs ADD PRIMARY KEY (id);

-- user_events: id INTEGER → UUID  
ALTER TABLE user_events ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
UPDATE user_events SET new_id = gen_random_uuid();
ALTER TABLE user_events DROP CONSTRAINT user_events_pkey;
ALTER TABLE user_events DROP COLUMN id;
ALTER TABLE user_events RENAME COLUMN new_id TO id;
ALTER TABLE user_events ADD PRIMARY KEY (id);

-- openai_requests: id INTEGER → UUID
ALTER TABLE openai_requests ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
UPDATE openai_requests SET new_id = gen_random_uuid();
ALTER TABLE openai_requests DROP CONSTRAINT openai_requests_pkey;
ALTER TABLE openai_requests DROP COLUMN id;
ALTER TABLE openai_requests RENAME COLUMN new_id TO id;
ALTER TABLE openai_requests ADD PRIMARY KEY (id);

-- =====================================================
-- 2. ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ ПОЛЕЙ В СУЩЕСТВУЮЩИЕ ТАБЛИЦЫ
-- =====================================================

-- Добавляем поля в users
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_generations INTEGER DEFAULT 0;

-- Добавляем поля в letter_sessions для системы подписок и итераций
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS subscription_id INTEGER;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS letters_used_count INTEGER DEFAULT 1;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS is_premium_feature BOOLEAN DEFAULT false;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS max_iterations INTEGER DEFAULT 3;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS current_iteration INTEGER DEFAULT 1;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS has_feedback BOOLEAN DEFAULT false;

-- Удаляем устаревшее поле user_regenerated
ALTER TABLE letter_sessions DROP COLUMN IF EXISTS user_regenerated;

-- =====================================================
-- 3. СОЗДАНИЕ НОВЫХ ТАБЛИЦ
-- =====================================================

-- Таблица подписок
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(20) DEFAULT 'free' CHECK (plan_type IN ('free', 'premium')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired')),
    letters_limit INTEGER DEFAULT 3,
    letters_used INTEGER DEFAULT 0,
    period_start TIMESTAMP WITH TIME ZONE DEFAULT date_trunc('month', CURRENT_DATE),
    period_end TIMESTAMP WITH TIME ZONE DEFAULT (date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'),
    auto_renew BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    cancellation_reason VARCHAR(100),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    source VARCHAR(100) DEFAULT 'manual',
    previous_subscription_id INTEGER REFERENCES subscriptions(id)
);

-- Таблица платежей
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    payment_id VARCHAR(100) UNIQUE NOT NULL,
    amount NUMERIC NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    provider VARCHAR(50),
    plan_type VARCHAR(20) DEFAULT 'premium',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица итераций писем
CREATE TABLE IF NOT EXISTS letter_iterations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES letter_sessions(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL DEFAULT 1,
    user_feedback TEXT,
    improvement_request TEXT,
    generated_letter TEXT,
    generation_time_seconds INTEGER,
    ai_model_used VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    feedback_id INTEGER,
    iteration_type VARCHAR(20) DEFAULT 'initial' CHECK (iteration_type IN ('initial', 'improvement'))
);

-- Таблица обратной связи (упрощенная v7.2)
CREATE TABLE IF NOT EXISTS letter_feedback (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES letter_sessions(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL DEFAULT 1,
    feedback_type VARCHAR(20) CHECK (feedback_type IN ('like', 'dislike')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица каналов привлечения
CREATE TABLE IF NOT EXISTS acquisition_channels (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_content VARCHAR(100),
    utm_term VARCHAR(100),
    referrer_url TEXT,
    landing_page VARCHAR(255),
    device_type VARCHAR(50),
    telegram_start_param VARCHAR(100),
    referral_user_id BIGINT REFERENCES users(id),
    session_count INTEGER DEFAULT 0,
    first_session_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_session_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Резервная таблица подписок
CREATE TABLE IF NOT EXISTS subscriptions_backup (
    id INTEGER,
    user_id BIGINT,
    plan_type VARCHAR(20),
    status VARCHAR(20),
    letters_limit INTEGER,
    letters_used INTEGER,
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- 4. ОБНОВЛЕНИЕ FOREIGN KEY CONSTRAINTS
-- =====================================================

-- Добавляем constraint для subscription_id в letter_sessions
ALTER TABLE letter_sessions ADD CONSTRAINT letter_sessions_subscription_id_fkey 
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id);

-- =====================================================
-- 5. СОЗДАНИЕ ИНДЕКСОВ
-- =====================================================

-- Индексы для subscriptions
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_type ON subscriptions(plan_type);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_user_active ON subscriptions(user_id) WHERE is_active = true;

-- Индексы для payments
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_payment_id ON payments(payment_id);

-- Индексы для letter_iterations
CREATE INDEX IF NOT EXISTS idx_iterations_session_id ON letter_iterations(session_id);
CREATE INDEX IF NOT EXISTS idx_iterations_user_id ON letter_iterations(user_id);
CREATE INDEX IF NOT EXISTS idx_iterations_number ON letter_iterations(iteration_number);

-- Индексы для letter_feedback
CREATE INDEX IF NOT EXISTS idx_letter_feedback_session ON letter_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_letter_feedback_user ON letter_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_letter_feedback_type ON letter_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_letter_feedback_created ON letter_feedback(created_at);

-- Индексы для acquisition_channels
CREATE INDEX IF NOT EXISTS idx_acquisition_user ON acquisition_channels(user_id);
CREATE INDEX IF NOT EXISTS idx_acquisition_source ON acquisition_channels(utm_source);
CREATE INDEX IF NOT EXISTS idx_acquisition_campaign ON acquisition_channels(utm_campaign);
CREATE INDEX IF NOT EXISTS idx_acquisition_referral ON acquisition_channels(referral_user_id);

-- =====================================================
-- 6. ФУНКЦИИ И ТРИГГЕРЫ
-- =====================================================

-- Функция обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры
DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at 
    BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_payments_updated_at ON payments;
CREATE TRIGGER update_payments_updated_at 
    BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 7. RLS ПОЛИТИКИ
-- =====================================================

-- Включаем RLS для новых таблиц
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE letter_iterations ENABLE ROW LEVEL SECURITY;
ALTER TABLE letter_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE acquisition_channels ENABLE ROW LEVEL SECURITY;

-- Политики для service_role
CREATE POLICY "Service role can do everything" ON subscriptions FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role can do everything" ON payments FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role can do everything" ON letter_iterations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role can do everything" ON letter_feedback FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role can do everything" ON acquisition_channels FOR ALL USING (auth.role() = 'service_role');

-- =====================================================
-- 8. ИНИЦИАЛИЗАЦИЯ ДАННЫХ
-- =====================================================

-- Создаем подписки для всех существующих пользователей
INSERT INTO subscriptions (user_id, plan_type, status, letters_limit, letters_used, is_active)
SELECT 
    id,
    'free',
    'active',
    3,
    0,
    true
FROM users 
WHERE id NOT IN (SELECT user_id FROM subscriptions WHERE is_active = true);

-- Связываем существующие сессии с подписками
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
-- 9. ФИНАЛЬНАЯ ПРОВЕРКА
-- =====================================================

DO $$
DECLARE
    users_count INTEGER;
    subscriptions_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO users_count FROM users;
    SELECT COUNT(*) INTO subscriptions_count FROM subscriptions WHERE is_active = true;
    
    RAISE NOTICE '================================';
    RAISE NOTICE 'МИГРАЦИЯ PROD → DEV v7.x ЗАВЕРШЕНА';
    RAISE NOTICE '================================';
    RAISE NOTICE 'Исправлены типы ID: INTEGER → BIGINT/UUID';
    RAISE NOTICE 'Пользователей: %', users_count;
    RAISE NOTICE 'Активных подписок: %', subscriptions_count;
    RAISE NOTICE 'Создано таблиц: 6 (subscriptions, payments, iterations, feedback, acquisition, backup)';
    RAISE NOTICE 'Обновлено таблиц: 5 (users, letter_sessions, error_logs, user_events, openai_requests)';
    RAISE NOTICE '================================';
END $$;

COMMIT; 