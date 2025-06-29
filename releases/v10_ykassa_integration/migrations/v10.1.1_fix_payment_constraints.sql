-- ============================================================================
-- Migration: v10.1.1_fix_payment_constraints
-- Release: v10_ykassa_integration  
-- Date: 2024-12-19
-- Author: @shoodyakoff
-- Description: Исправление constraint для статусов платежей
-- Причина: исправление constraint для поддержки статуса succeeded и корректной работы продления подписки при повторной оплате (см. TZ_NUANCES_REPORT_v3.md)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ИСПРАВЛЕНИЕ CONSTRAINT ДЛЯ СТАТУСОВ ПЛАТЕЖЕЙ
-- ============================================================================

-- Удаляем старый constraint если он существует
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'payments_status_check' 
        AND table_name = 'payments'
    ) THEN
        ALTER TABLE payments DROP CONSTRAINT payments_status_check;
    END IF;
END $$;

-- Создаем новый constraint с правильными статусами
ALTER TABLE payments ADD CONSTRAINT payments_status_check 
CHECK (status IN ('pending', 'succeeded', 'canceled', 'failed', 'refunded'));

-- ============================================================================
-- 2. ПРОВЕРКА МИГРАЦИИ
-- ============================================================================

-- Проверяем что constraint создан правильно
DO $$ 
DECLARE
    constraint_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'payments_status_check' 
        AND table_name = 'payments'
    ) INTO constraint_exists;
    
    IF constraint_exists THEN
        RAISE NOTICE '✅ Payment status constraint updated successfully!';
    ELSE
        RAISE WARNING '❌ Payment status constraint not found!';
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- ПРОВЕРКА РАБОТЫ
-- ============================================================================

-- Тестируем вставку с разными статусами
DO $$
BEGIN
    -- Тест успешного платежа
    BEGIN
        INSERT INTO payments (user_id, payment_id, amount, currency, status, payment_method, metadata)
        VALUES (999, 'test_succeeded', 199.00, 'RUB', 'succeeded', 'yookassa', '{"test": true}');
        RAISE NOTICE '✅ Test succeeded payment inserted successfully';
        DELETE FROM payments WHERE payment_id = 'test_succeeded';
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING '❌ Failed to insert succeeded payment: %', SQLERRM;
    END;
    
    -- Тест отмененного платежа
    BEGIN
        INSERT INTO payments (user_id, payment_id, amount, currency, status, payment_method, metadata)
        VALUES (999, 'test_canceled', 199.00, 'RUB', 'canceled', 'yookassa', '{"test": true}');
        RAISE NOTICE '✅ Test canceled payment inserted successfully';
        DELETE FROM payments WHERE payment_id = 'test_canceled';
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING '❌ Failed to insert canceled payment: %', SQLERRM;
    END;
    
    -- Тест неудачного платежа
    BEGIN
        INSERT INTO payments (user_id, payment_id, amount, currency, status, payment_method, metadata)
        VALUES (999, 'test_failed', 199.00, 'RUB', 'failed', 'yookassa', '{"test": true}');
        RAISE NOTICE '✅ Test failed payment inserted successfully';
        DELETE FROM payments WHERE payment_id = 'test_failed';
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING '❌ Failed to insert failed payment: %', SQLERRM;
    END;
END $$; 