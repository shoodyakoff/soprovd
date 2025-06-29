-- ============================================================================
-- МИГРАЦИЯ v9.5: СИНХРОНИЗАЦИЯ PROD И DEV БАЗ ДАННЫХ (ИСПРАВЛЕННАЯ)
-- ============================================================================
-- Дата: 2024-12-19
-- Цель: Привести prod базу в соответствие с dev схемой
-- 
-- ВНИМАНИЕ: Выполнять ТОЛЬКО на PROD базе данных!
-- 
-- ИСПРАВЛЕНИЕ: Правильный порядок операций для избежания ошибки с VIEW
-- 1. Сначала удаляем VIEW которые ссылаются на изменяемые поля
-- 2. Затем изменяем типы полей
-- 3. Потом пересоздаем VIEW
-- ============================================================================

BEGIN;

-- ЭТАП 1: УДАЛЕНИЕ СУЩЕСТВУЮЩИХ VIEW (чтобы можно было изменить типы полей)
-- ============================================================================

-- Удаляем VIEW session_stats если существует (он ссылается на generation_time_seconds)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_name = 'session_stats' 
        AND table_schema = 'public'
    ) THEN
        DROP VIEW public.session_stats;
        RAISE NOTICE 'VIEW session_stats удален (будет пересоздан позже)';
    ELSE
        RAISE NOTICE 'VIEW session_stats не найден, пропускаем удаление';
    END IF;
END $$;

-- Удаляем другие VIEW которые могут мешать изменению типов
DO $$
BEGIN
    -- user_stats
    IF EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_name = 'user_stats' 
        AND table_schema = 'public'
    ) THEN
        DROP VIEW public.user_stats;
        RAISE NOTICE 'VIEW user_stats удален (будет пересоздан позже)';
    END IF;
    
    -- user_activity  
    IF EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_name = 'user_activity' 
        AND table_schema = 'public'
    ) THEN
        DROP VIEW public.user_activity;
        RAISE NOTICE 'VIEW user_activity удален (будет пересоздан позже)';
    END IF;
    
    -- openai_usage
    IF EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_name = 'openai_usage' 
        AND table_schema = 'public'
    ) THEN
        DROP VIEW public.openai_usage;
        RAISE NOTICE 'VIEW openai_usage удален (будет пересоздан позже)';
    END IF;
    
    -- user_cohorts_basic
    IF EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_name = 'user_cohorts_basic' 
        AND table_schema = 'public'
    ) THEN
        DROP VIEW public.user_cohorts_basic;
        RAISE NOTICE 'VIEW user_cohorts_basic удален (будет пересоздан позже)';
    END IF;
END $$;

-- ЭТАП 2: УДАЛЕНИЕ ЛИШНИХ ПОЛЕЙ ИЗ PROD
-- ============================================================================

-- Шаг 2.1: Удаляем поле total_generations из таблицы users (есть только в prod)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'total_generations'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.users DROP COLUMN total_generations;
        RAISE NOTICE 'Поле users.total_generations удалено';
    ELSE
        RAISE NOTICE 'Поле users.total_generations не найдено, пропускаем';
    END IF;
END $$;

-- Шаг 2.2: Удаляем поле updated_at из таблицы users (есть только в prod)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'updated_at'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.users DROP COLUMN updated_at;
        RAISE NOTICE 'Поле users.updated_at удалено';
    ELSE
        RAISE NOTICE 'Поле users.updated_at не найдено, пропускаем';
    END IF;
END $$;

-- ЭТАП 3: ИЗМЕНЕНИЕ ТИПОВ ПОЛЕЙ (теперь можно безопасно)
-- ============================================================================

-- Шаг 3.1: Изменяем тип generation_time_seconds с integer на double precision
DO $$
BEGIN
    -- Проверяем текущий тип поля
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'letter_sessions' 
        AND column_name = 'generation_time_seconds'
        AND data_type = 'integer'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.letter_sessions 
        ALTER COLUMN generation_time_seconds TYPE double precision;
        RAISE NOTICE 'Тип letter_sessions.generation_time_seconds изменен на double precision';
    ELSE
        RAISE NOTICE 'Поле letter_sessions.generation_time_seconds уже имеет правильный тип';
    END IF;
END $$;

-- Финальное сообщение
DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'ЭТАП 1 ЗАВЕРШЕН: Удалены VIEW и лишние поля, изменен тип generation_time_seconds';
    RAISE NOTICE 'Теперь выполните ЭТАП 2 миграции...';
    RAISE NOTICE '============================================================================';
END $$;

COMMIT; 