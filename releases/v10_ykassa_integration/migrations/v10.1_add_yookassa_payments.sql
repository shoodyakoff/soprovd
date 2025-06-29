-- ============================================================================
-- Migration: v10.1_add_yookassa_payments
-- Release: v10_ykassa_integration  
-- Date: 2024-12-19
-- Author: @shoodyakoff
-- Description: Добавление поддержки ЮKassa платежей для автоматизации Premium подписок
-- ============================================================================

-- ВАЖНО: Каждая миграция должна быть идемпотентной!
-- Используйте IF NOT EXISTS, IF EXISTS и другие проверки

BEGIN;

-- ============================================================================
-- 1. РАСШИРЕНИЕ ТАБЛИЦЫ PAYMENTS
-- ============================================================================

-- Добавление поля payment_method для указания способа оплаты
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'payment_method'
    ) THEN
        ALTER TABLE payments ADD COLUMN payment_method VARCHAR(50) DEFAULT 'manual';
    END IF;
END $$;

-- Добавление поля confirmation_url для ссылки на оплату
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'confirmation_url'
    ) THEN
        ALTER TABLE payments ADD COLUMN confirmation_url TEXT;
    END IF;
END $$;

-- Добавление поля metadata для хранения данных от ЮKassa
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE payments ADD COLUMN metadata JSONB DEFAULT '{}';
    END IF;
END $$;

-- Добавление поля updated_at для отслеживания изменений
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE payments ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- ============================================================================
-- 2. РАСШИРЕНИЕ ТАБЛИЦЫ SUBSCRIPTIONS
-- ============================================================================

-- Добавление поля payment_id для связи с платежом
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscriptions' AND column_name = 'payment_id'
    ) THEN
        ALTER TABLE subscriptions ADD COLUMN payment_id VARCHAR(255);
    END IF;
END $$;

-- Добавление поля upgraded_at для отслеживания апгрейдов
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscriptions' AND column_name = 'upgraded_at'
    ) THEN
        ALTER TABLE subscriptions ADD COLUMN upgraded_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- ============================================================================
-- 3. ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- ============================================================================

-- Индекс на payment_method для группировки платежей
CREATE INDEX IF NOT EXISTS idx_payments_payment_method ON payments(payment_method);

-- Индекс на metadata для поиска по ЮKassa данным (GIN для JSONB)
CREATE INDEX IF NOT EXISTS idx_payments_metadata ON payments USING GIN(metadata);

-- Индекс на payment_id в subscriptions для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_subscriptions_payment_id ON subscriptions(payment_id);

-- ============================================================================
-- 4. ПРЕДСТАВЛЕНИЯ ДЛЯ АНАЛИТИКИ
-- ============================================================================

-- Создание представления для аналитики платежей
CREATE OR REPLACE VIEW payment_analytics AS
SELECT 
    DATE(created_at) as payment_date,
    payment_method,
    status,
    COUNT(*) as payments_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    COUNT(CASE WHEN status = 'succeeded' THEN 1 END) as successful_payments,
    ROUND(
        COUNT(CASE WHEN status = 'succeeded' THEN 1 END)::DECIMAL / COUNT(*) * 100, 
        2
    ) as success_rate_percent
FROM payments 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at), payment_method, status
ORDER BY payment_date DESC, payment_method;

-- ============================================================================
-- 5. ФУНКЦИИ И ТРИГГЕРЫ
-- ============================================================================

-- Создание функции для автоматического обновления updated_at в payments
CREATE OR REPLACE FUNCTION update_payments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггера для автоматического обновления updated_at
DROP TRIGGER IF EXISTS update_payments_updated_at ON payments;
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_payments_updated_at();

-- ============================================================================
-- 6. РАЗРЕШЕНИЯ
-- ============================================================================

-- Даем права на новое представление
GRANT SELECT ON payment_analytics TO authenticated;
GRANT SELECT ON payment_analytics TO service_role;

-- ============================================================================
-- 7. КОММЕНТАРИИ
-- ============================================================================

COMMENT ON COLUMN payments.payment_method IS 'Способ оплаты: yookassa, manual, etc';
COMMENT ON COLUMN payments.confirmation_url IS 'URL для перехода на оплату (от ЮKassa)';
COMMENT ON COLUMN payments.metadata IS 'Дополнительные данные платежа (JSON)';
COMMENT ON COLUMN subscriptions.payment_id IS 'ID платежа, активировавшего подписку';
COMMENT ON COLUMN subscriptions.upgraded_at IS 'Время апгрейда до Premium';
COMMENT ON VIEW payment_analytics IS 'Аналитика платежей за последние 30 дней';

-- Добавлено для поддержки продления подписки при повторной оплате и новых статусов платежей (см. TZ_NUANCES_REPORT_v3.md)

COMMIT;

-- ============================================================================
-- ПРОВЕРКА МИГРАЦИИ
-- ============================================================================

-- Проверяем что все поля добавлены
DO $$ 
DECLARE
    missing_fields TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- Проверяем payments
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'payments' AND column_name = 'payment_method') THEN
        missing_fields := missing_fields || 'payments.payment_method';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'payments' AND column_name = 'confirmation_url') THEN
        missing_fields := missing_fields || 'payments.confirmation_url';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'payments' AND column_name = 'metadata') THEN
        missing_fields := missing_fields || 'payments.metadata';
    END IF;
    
    -- Проверяем subscriptions  
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'subscriptions' AND column_name = 'payment_id') THEN
        missing_fields := missing_fields || 'subscriptions.payment_id';
    END IF;
    
    -- Выводим результат
    IF array_length(missing_fields, 1) > 0 THEN
        RAISE WARNING 'Migration incomplete. Missing: %', array_to_string(missing_fields, ', ');
    ELSE
        RAISE NOTICE '✅ ЮKassa payments migration completed successfully!';
    END IF;
END $$;

-- ============================================================================
-- ROLLBACK COMMANDS (в комментариях для ручного отката)
-- ============================================================================

/*
-- ROLLBACK MIGRATION (выполнять только при необходимости!)

-- Удалить представление
DROP VIEW IF EXISTS payment_analytics;

-- Удалить триггер
DROP TRIGGER IF EXISTS update_payments_updated_at ON payments;

-- Удалить функцию
DROP FUNCTION IF EXISTS update_payments_updated_at();

-- Удалить индексы
DROP INDEX IF EXISTS idx_payments_payment_method;
DROP INDEX IF EXISTS idx_payments_metadata;
DROP INDEX IF EXISTS idx_subscriptions_payment_id;

-- Удалить поля из subscriptions
ALTER TABLE subscriptions DROP COLUMN IF EXISTS payment_id;
ALTER TABLE subscriptions DROP COLUMN IF EXISTS upgraded_at;

-- Удалить поля из payments
ALTER TABLE payments DROP COLUMN IF EXISTS payment_method;
ALTER TABLE payments DROP COLUMN IF EXISTS confirmation_url;
ALTER TABLE payments DROP COLUMN IF EXISTS metadata;
ALTER TABLE payments DROP COLUMN IF EXISTS updated_at;

*/ 