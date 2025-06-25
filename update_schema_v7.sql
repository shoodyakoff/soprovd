-- =====================================================
-- ОБНОВЛЕНИЕ СХЕМЫ ДО ВЕРСИИ 7.0 - СИСТЕМА ПОДПИСОК
-- =====================================================

-- 0. УБЕДИМСЯ ЧТО РАСШИРЕНИЕ UUID ВКЛЮЧЕНО
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. СОЗДАНИЕ ТАБЛИЦЫ ПОДПИСОК
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(20) DEFAULT 'free' CHECK (plan_type IN ('free', 'premium')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired')),
    letters_limit INTEGER DEFAULT 3,
    letters_used INTEGER DEFAULT 0,
    period_start TIMESTAMP WITH TIME ZONE DEFAULT DATE_TRUNC('month', CURRENT_DATE),
    period_end TIMESTAMP WITH TIME ZONE DEFAULT (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'),
    auto_renew BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Индексы для быстрого поиска
    UNIQUE(user_id)
);

-- 2. СОЗДАНИЕ ТАБЛИЦЫ ПЛАТЕЖЕЙ
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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

-- 3. СОЗДАНИЕ ТАБЛИЦЫ ИТЕРАЦИЙ ПИСЕМ
CREATE TABLE IF NOT EXISTS letter_iterations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES letter_sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL DEFAULT 1,
    user_feedback TEXT,
    improvement_request TEXT,
    generated_letter TEXT,
    generation_time_seconds INTEGER,
    ai_model_used VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. ОБНОВЛЕНИЕ СУЩЕСТВУЮЩИХ ТАБЛИЦ

-- Добавляем новые поля в letter_sessions (если их нет)
DO $$ 
BEGIN
    -- Проверяем и добавляем поля по одному
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='subscription_id') THEN
        ALTER TABLE letter_sessions ADD COLUMN subscription_id INTEGER REFERENCES subscriptions(id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='letters_used_count') THEN
        ALTER TABLE letter_sessions ADD COLUMN letters_used_count INTEGER DEFAULT 1;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='is_premium_feature') THEN
        ALTER TABLE letter_sessions ADD COLUMN is_premium_feature BOOLEAN DEFAULT false;
    END IF;
END $$;

-- 5. СОЗДАНИЕ ИНДЕКСОВ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status ON subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period ON subscriptions(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at);
CREATE INDEX IF NOT EXISTS idx_letter_iterations_session ON letter_iterations(session_id);
CREATE INDEX IF NOT EXISTS idx_letter_iterations_user ON letter_iterations(user_id);

-- 6. НАСТРОЙКА RLS ПОЛИТИК (Row Level Security)
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE letter_iterations ENABLE ROW LEVEL SECURITY;

-- Политики для service_role (полный доступ)
DROP POLICY IF EXISTS "Service role can manage subscriptions" ON subscriptions;
CREATE POLICY "Service role can manage subscriptions" ON subscriptions FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Service role can manage payments" ON payments;
CREATE POLICY "Service role can manage payments" ON payments FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Service role can manage iterations" ON letter_iterations;
CREATE POLICY "Service role can manage iterations" ON letter_iterations FOR ALL TO service_role USING (true);

-- 7. СОЗДАНИЕ ФУНКЦИЙ ДЛЯ АВТОМАТИЗАЦИИ

-- Функция обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автообновления updated_at
DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_payments_updated_at ON payments;
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. СОЗДАНИЕ АНАЛИТИЧЕСКИХ ПРЕДСТАВЛЕНИЙ

-- Статистика подписок
CREATE OR REPLACE VIEW subscription_stats AS
SELECT 
    plan_type,
    status,
    COUNT(*) as count,
    AVG(letters_used::numeric) as avg_letters_used,
    SUM(letters_used) as total_letters_used
FROM subscriptions 
GROUP BY plan_type, status;

-- Статистика платежей
CREATE OR REPLACE VIEW payment_stats AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    status,
    COUNT(*) as count,
    SUM(amount) as total_amount,
    currency
FROM payments 
GROUP BY DATE_TRUNC('day', created_at), status, currency
ORDER BY date DESC;

-- 9. ИНИЦИАЛИЗАЦИЯ ПОДПИСОК ДЛЯ СУЩЕСТВУЮЩИХ ПОЛЬЗОВАТЕЛЕЙ

-- Создаем бесплатные подписки для всех существующих пользователей
INSERT INTO subscriptions (user_id, plan_type, status, letters_limit, letters_used, period_start, period_end)
SELECT 
    id as user_id,
    'free' as plan_type,
    'active' as status,
    3 as letters_limit,
    0 as letters_used,
    DATE_TRUNC('month', CURRENT_DATE) as period_start,
    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' as period_end
FROM users 
WHERE id NOT IN (SELECT user_id FROM subscriptions)
ON CONFLICT (user_id) DO NOTHING;

-- 10. ФИНАЛЬНАЯ ПРОВЕРКА
DO $$
BEGIN
    RAISE NOTICE 'Схема обновлена до версии 7.0!';
    RAISE NOTICE 'Создано таблиц: subscriptions, payments, letter_iterations';
    RAISE NOTICE 'Обновлена таблица: letter_sessions';
    RAISE NOTICE 'Создано представлений: subscription_stats, payment_stats';
    RAISE NOTICE 'Всего пользователей с подписками: %', (SELECT COUNT(*) FROM subscriptions);
END $$;

-- =====================================================
-- МИГРАЦИЯ К ВЕРСИИ 7.2: УПРОЩЕНИЕ СИСТЕМЫ ОЦЕНОК
-- =====================================================
-- Убираем комментарии из letter_feedback, оставляем только лайки/дизлайки
-- Детальные комментарии теперь только в letter_iterations

BEGIN;

-- 1. СОЗДАЕМ НОВУЮ ТАБЛИЦУ letter_feedback БЕЗ user_comment
CREATE TABLE IF NOT EXISTS letter_feedback_new (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES letter_sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL DEFAULT 1,
    -- Только лайки и дизлайки, БЕЗ комментариев
    feedback_type VARCHAR(20) CHECK (feedback_type IN ('like', 'dislike')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, iteration_number)
);

-- 2. КОПИРУЕМ ДАННЫЕ (только лайки и дизлайки)
INSERT INTO letter_feedback_new (session_id, user_id, iteration_number, feedback_type, created_at)
SELECT session_id, user_id, iteration_number, feedback_type, created_at
FROM letter_feedback 
WHERE feedback_type IN ('like', 'dislike');

-- 3. УДАЛЯЕМ СТАРУЮ ТАБЛИЦУ И ПЕРЕИМЕНОВЫВАЕМ
DROP TABLE IF EXISTS letter_feedback CASCADE;
ALTER TABLE letter_feedback_new RENAME TO letter_feedback;

-- 4. СОЗДАЕМ ИНДЕКСЫ
CREATE INDEX idx_letter_feedback_session ON letter_feedback(session_id);
CREATE INDEX idx_letter_feedback_user ON letter_feedback(user_id);
CREATE INDEX idx_letter_feedback_type ON letter_feedback(feedback_type);
CREATE INDEX idx_letter_feedback_created ON letter_feedback(created_at);

-- 5. НАСТРАИВАЕМ RLS
ALTER TABLE letter_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role can do everything" ON letter_feedback
    FOR ALL USING (auth.role() = 'service_role');

-- 6. ОБНОВЛЯЕМ КОММЕНТАРИЙ В ТАБЛИЦЕ
COMMENT ON TABLE letter_feedback IS 'Упрощенные оценки писем v7.2: только лайки/дизлайки БЕЗ комментариев';
COMMENT ON COLUMN letter_feedback.feedback_type IS 'Только like или dislike - комментарии перенесены в letter_iterations';

COMMIT;

-- =====================================================
-- ПРОВЕРКА МИГРАЦИИ
-- =====================================================

-- Проверяем структуру новой таблицы
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'letter_feedback' 
ORDER BY ordinal_position;

-- Проверяем ограничения
SELECT 
    tc.constraint_name, 
    tc.constraint_type,
    cc.check_clause
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.check_constraints cc 
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_name = 'letter_feedback';

-- Подсчитываем записи
SELECT 
    feedback_type,
    COUNT(*) as count
FROM letter_feedback 
GROUP BY feedback_type;

COMMIT; 