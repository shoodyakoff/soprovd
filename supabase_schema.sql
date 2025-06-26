-- ===================================================
-- Сопровод v6.0 - Supabase Database Schema
-- ===================================================
-- Выполните этот SQL в SQL Editor вашего Supabase проекта

-- Включаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===================================================
-- 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
-- ===================================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT NOT NULL DEFAULT nextval('users_id_seq'::regclass) PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    consent_given BOOLEAN DEFAULT NULL,
    consent_timestamp TIMESTAMP DEFAULT NULL,
    consent_version VARCHAR(10) DEFAULT 'v1.0',
    marketing_consent BOOLEAN DEFAULT FALSE
);

-- Индексы для users
CREATE INDEX idx_users_telegram_id ON users(telegram_user_id);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_consent ON users(consent_given, consent_timestamp);
CREATE INDEX idx_users_consent_version ON users(consent_version, consent_timestamp);

-- ===================================================
-- 2. ТАБЛИЦА СЕССИЙ ГЕНЕРАЦИИ ПИСЕМ v6.0
-- ===================================================
CREATE TABLE IF NOT EXISTS letter_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'started' CHECK (status IN ('started', 'completed', 'abandoned')),
    mode VARCHAR(20),
    job_description TEXT,
    job_description_length INTEGER,
    resume_text TEXT,
    resume_length INTEGER,
    selected_style VARCHAR(50),
    generated_letter TEXT,
    generated_letter_length INTEGER,
    generation_time_seconds INTEGER,
    openai_model_used VARCHAR(50),
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    subscription_id INTEGER REFERENCES subscriptions(id),
    letters_used_count INTEGER DEFAULT 1,
    is_premium_feature BOOLEAN DEFAULT false,
    max_iterations INTEGER DEFAULT 3,
    current_iteration INTEGER DEFAULT 1,
    has_feedback BOOLEAN DEFAULT false
);

-- Индексы для letter_sessions
CREATE INDEX idx_sessions_user_id ON letter_sessions(user_id);
CREATE INDEX idx_sessions_status ON letter_sessions(status);
CREATE INDEX idx_sessions_mode ON letter_sessions(mode);
CREATE INDEX idx_sessions_created_at ON letter_sessions(created_at);
CREATE INDEX idx_sessions_generation_time ON letter_sessions(generation_time_seconds);
CREATE INDEX idx_sessions_openai_model ON letter_sessions(openai_model_used);

-- ===================================================
-- 3. ТАБЛИЦА СОБЫТИЙ ПОЛЬЗОВАТЕЛЕЙ
-- ===================================================
CREATE TABLE IF NOT EXISTS user_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    session_id UUID REFERENCES letter_sessions(id) ON DELETE SET NULL,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для user_events
CREATE INDEX idx_events_user_id ON user_events(user_id);
CREATE INDEX idx_events_type ON user_events(event_type);
CREATE INDEX idx_events_session_id ON user_events(session_id);
CREATE INDEX idx_events_created_at ON user_events(created_at);
CREATE INDEX idx_events_data_gin ON user_events USING GIN(event_data);

-- ===================================================
-- 4. ТАБЛИЦА ЛОГОВ ОШИБОК
-- ===================================================
CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES letter_sessions(id) ON DELETE SET NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    handler_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для error_logs
CREATE INDEX idx_errors_type ON error_logs(error_type);
CREATE INDEX idx_errors_user_id ON error_logs(user_id);
CREATE INDEX idx_errors_created_at ON error_logs(created_at);

-- ===================================================
-- 5. ТАБЛИЦА ЗАПРОСОВ К OPENAI
-- ===================================================
CREATE TABLE IF NOT EXISTS openai_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES letter_sessions(id) ON DELETE SET NULL,
    model VARCHAR(50) NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для openai_requests
CREATE INDEX idx_openai_model ON openai_requests(model);
CREATE INDEX idx_openai_type ON openai_requests(request_type);
CREATE INDEX idx_openai_user_id ON openai_requests(user_id);
CREATE INDEX idx_openai_session_id ON openai_requests(session_id);
CREATE INDEX idx_openai_created_at ON openai_requests(created_at);
CREATE INDEX idx_openai_tokens ON openai_requests(total_tokens);
CREATE INDEX idx_openai_success ON openai_requests(success);

-- ===================================================
-- 6. ФУНКЦИИ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ updated_at
-- ===================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON letter_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================================================
-- 7. RLS (Row Level Security) ПОЛИТИКИ
-- ===================================================
-- Включаем RLS для всех таблиц
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE letter_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE openai_requests ENABLE ROW LEVEL SECURITY;

-- Политики для сервисного ключа (полный доступ)
CREATE POLICY "Service role can do everything" ON users
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON letter_sessions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON user_events
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON error_logs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON openai_requests
    FOR ALL USING (auth.role() = 'service_role');

-- ===================================================
-- 8. НОВЫЕ ТАБЛИЦЫ ДЛЯ V7.2 - УПРОЩЕННАЯ СИСТЕМА ОЦЕНОК
-- ===================================================

-- Таблица подписок пользователей
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(20) DEFAULT 'free' CHECK (plan_type IN ('free', 'premium')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired')),
    letters_limit INTEGER DEFAULT 3,
    letters_used INTEGER DEFAULT 0,
    period_start TIMESTAMP WITH TIME ZONE DEFAULT DATE_TRUNC('month', CURRENT_DATE),
    period_end TIMESTAMP WITH TIME ZONE DEFAULT (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'),
    auto_renew BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    cancellation_reason VARCHAR(100),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    source VARCHAR(100) DEFAULT 'manual',
    previous_subscription_id INTEGER REFERENCES subscriptions(id)
);

-- Индексы для subscriptions
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_type ON subscriptions(plan_type);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Таблица платежей
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    payment_id VARCHAR(100) UNIQUE NOT NULL, -- ID от платежной системы
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    provider VARCHAR(50), -- yookassa, stripe, etc
    plan_type VARCHAR(20) DEFAULT 'premium',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для payments
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_payment_id ON payments(payment_id);

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для letter_iterations
CREATE INDEX idx_iterations_session_id ON letter_iterations(session_id);
CREATE INDEX idx_iterations_user_id ON letter_iterations(user_id);
CREATE INDEX idx_iterations_number ON letter_iterations(iteration_number);

-- Упрощенная таблица оценок писем (БЕЗ комментариев)
CREATE TABLE IF NOT EXISTS letter_feedback (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES letter_sessions(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL DEFAULT 1,
    -- Только лайки и дизлайки, БЕЗ комментариев
    feedback_type VARCHAR(20) CHECK (feedback_type IN ('like', 'dislike')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, iteration_number)
);

-- Индексы для letter_feedback
CREATE INDEX idx_letter_feedback_session ON letter_feedback(session_id);
CREATE INDEX idx_letter_feedback_user ON letter_feedback(user_id);
CREATE INDEX idx_letter_feedback_type ON letter_feedback(feedback_type);
CREATE INDEX idx_letter_feedback_created ON letter_feedback(created_at);

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

-- Индексы для acquisition_channels
CREATE INDEX idx_acquisition_user ON acquisition_channels(user_id);
CREATE INDEX idx_acquisition_source ON acquisition_channels(utm_source);
CREATE INDEX idx_acquisition_campaign ON acquisition_channels(utm_campaign);
CREATE INDEX idx_acquisition_referral ON acquisition_channels(referral_user_id);

-- Триггеры для новых таблиц
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS для новых таблиц
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE letter_iterations ENABLE ROW LEVEL SECURITY;
ALTER TABLE letter_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE acquisition_channels ENABLE ROW LEVEL SECURITY;

-- Политики для новых таблиц
CREATE POLICY "Service role can do everything" ON subscriptions
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON payments
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON letter_iterations
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON letter_feedback
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do everything" ON acquisition_channels
    FOR ALL USING (auth.role() = 'service_role');

-- ===================================================
-- 9. ПОЛЕЗНЫЕ VIEWS ДЛЯ АНАЛИТИКИ
-- ===================================================

-- Сводка пользователей
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 day') as users_today,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as users_week,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as users_month
FROM users;

-- Сводка сессий
CREATE OR REPLACE VIEW session_stats AS
SELECT 
    status,
    mode,
    openai_model_used,
    COUNT(*) as count,
    ROUND(AVG(generation_time_seconds), 2) as avg_generation_time,
    ROUND(AVG(generated_letter_length), 0) as avg_letter_length,
    ROUND(AVG(resume_length), 0) as avg_resume_length,
    ROUND(AVG(job_description_length), 0) as avg_job_length
FROM letter_sessions
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY status, mode, openai_model_used;

-- Активность пользователей
CREATE OR REPLACE VIEW user_activity AS
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_events
FROM user_events
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Использование OpenAI
CREATE OR REPLACE VIEW openai_usage AS
SELECT 
    DATE(created_at) as date,
    model,
    COUNT(*) as requests,
    SUM(total_tokens) as total_tokens,
    ROUND(AVG(response_time_ms), 0) as avg_response_time,
    ROUND(COUNT(*) FILTER (WHERE success = true) * 100.0 / COUNT(*), 2) as success_rate
FROM openai_requests
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), model
ORDER BY date DESC, model;

-- ===================================================
-- ГОТОВО! 
-- ===================================================
-- После выполнения этого SQL:
-- 1. Проверьте что все таблицы созданы в Table Editor
-- 2. Запустите тест: python test_analytics.py
-- 3. Проверьте что данные появились в таблицах 