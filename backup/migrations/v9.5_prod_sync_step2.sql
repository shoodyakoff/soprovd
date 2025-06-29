-- ============================================================================
-- МИГРАЦИЯ v9.5 - ЭТАП 2: ИЗМЕНЕНИЕ ТИПОВ USER_ID
-- ============================================================================
-- Дата: 2024-12-19
-- Цель: Изменить типы user_id с integer на bigint в нужных таблицах
-- 
-- ВНИМАНИЕ: Выполнять ТОЛЬКО после успешного завершения ЭТАПА 1!
-- ============================================================================

BEGIN;

-- ЭТАП 2: ИЗМЕНЕНИЕ ТИПОВ USER_ID С INTEGER НА BIGINT
-- ============================================================================

-- 2.1 acquisition_channels.user_id и referral_user_id
DO $$
BEGIN
    -- user_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'acquisition_channels' 
        AND column_name = 'user_id'
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.acquisition_channels 
        ALTER COLUMN user_id TYPE bigint;
        RAISE NOTICE 'Тип acquisition_channels.user_id изменен на bigint';
    ELSE
        RAISE NOTICE 'acquisition_channels.user_id уже имеет правильный тип';
    END IF;
    
    -- referral_user_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'acquisition_channels' 
        AND column_name = 'referral_user_id'
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.acquisition_channels 
        ALTER COLUMN referral_user_id TYPE bigint;
        RAISE NOTICE 'Тип acquisition_channels.referral_user_id изменен на bigint';
    ELSE
        RAISE NOTICE 'acquisition_channels.referral_user_id уже имеет правильный тип';
    END IF;
END $$;

-- 2.2 letter_feedback.user_id
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'letter_feedback' 
        AND column_name = 'user_id'
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.letter_feedback 
        ALTER COLUMN user_id TYPE bigint;
        RAISE NOTICE 'Тип letter_feedback.user_id изменен на bigint';
    ELSE
        RAISE NOTICE 'letter_feedback.user_id уже имеет правильный тип';
    END IF;
END $$;

-- 2.3 letter_iterations.user_id
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'letter_iterations' 
        AND column_name = 'user_id'
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.letter_iterations 
        ALTER COLUMN user_id TYPE bigint;
        RAISE NOTICE 'Тип letter_iterations.user_id изменен на bigint';
    ELSE
        RAISE NOTICE 'letter_iterations.user_id уже имеет правильный тип';
    END IF;
END $$;

-- 2.4 payments.user_id
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'payments' 
        AND column_name = 'user_id'
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.payments 
        ALTER COLUMN user_id TYPE bigint;
        RAISE NOTICE 'Тип payments.user_id изменен на bigint';
    ELSE
        RAISE NOTICE 'payments.user_id уже имеет правильный тип';
    END IF;
END $$;

-- 2.5 subscriptions.user_id
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscriptions' 
        AND column_name = 'user_id'
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.subscriptions 
        ALTER COLUMN user_id TYPE bigint;
        RAISE NOTICE 'Тип subscriptions.user_id изменен на bigint';
    ELSE
        RAISE NOTICE 'subscriptions.user_id уже имеет правильный тип';
    END IF;
END $$;

-- 2.6 subscriptions_backup.user_id
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscriptions_backup' 
        AND column_name = 'user_id'
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.subscriptions_backup 
        ALTER COLUMN user_id TYPE bigint;
        RAISE NOTICE 'Тип subscriptions_backup.user_id изменен на bigint';
    ELSE
        RAISE NOTICE 'subscriptions_backup.user_id уже имеет правильный тип';
    END IF;
END $$;

-- Финальное сообщение
DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'ЭТАП 2 ЗАВЕРШЕН: Все типы user_id изменены на bigint';
    RAISE NOTICE 'Теперь выполните ЭТАП 3 миграции...';
    RAISE NOTICE '============================================================================';
END $$;

COMMIT; 