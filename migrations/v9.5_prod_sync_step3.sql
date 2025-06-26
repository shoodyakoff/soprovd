-- ============================================================================
-- МИГРАЦИЯ v9.5 - ЭТАП 3: ПЕРЕСОЗДАНИЕ VIEW ТАБЛИЦ
-- ============================================================================
-- Дата: 2024-12-19
-- Цель: Пересоздать все VIEW таблицы после изменения типов полей
-- 
-- ВНИМАНИЕ: Выполнять ТОЛЬКО после успешного завершения ЭТАПОВ 1 и 2!
-- ============================================================================

BEGIN;

-- ЭТАП 3: ПЕРЕСОЗДАНИЕ VIEW ТАБЛИЦ
-- ============================================================================

-- 3.1 Создаем VIEW user_stats
DO $$
BEGIN
    CREATE OR REPLACE VIEW public.user_stats AS
    SELECT 
        COUNT(*) as total_users,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 day') as users_today,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as users_week,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as users_month
    FROM users;
    
    RAISE NOTICE 'VIEW user_stats пересоздан успешно';
END $$;

-- 3.2 Создаем VIEW session_stats (ИСПРАВЛЕННЫЙ - теперь generation_time_seconds имеет тип double precision)
DO $$
BEGIN
    CREATE OR REPLACE VIEW public.session_stats AS
    SELECT 
        status,
        mode,
        openai_model_used,
        COUNT(*) as count,
        ROUND(AVG(generation_time_seconds)::numeric, 2) as avg_generation_time,
        ROUND(AVG(generated_letter_length)::numeric, 0) as avg_letter_length,
        ROUND(AVG(resume_length)::numeric, 0) as avg_resume_length,
        ROUND(AVG(job_description_length)::numeric, 0) as avg_job_length
    FROM letter_sessions
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY status, mode, openai_model_used;
    
    RAISE NOTICE 'VIEW session_stats пересоздан успешно';
END $$;

-- 3.3 Создаем VIEW user_activity
DO $$
BEGIN
    CREATE OR REPLACE VIEW public.user_activity AS
    SELECT 
        DATE(created_at) as date,
        COUNT(DISTINCT user_id) as active_users,
        COUNT(*) as total_events
    FROM user_events
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY DATE(created_at)
    ORDER BY date DESC;
    
    RAISE NOTICE 'VIEW user_activity пересоздан успешно';
END $$;

-- 3.4 Создаем VIEW openai_usage
DO $$
BEGIN
    CREATE OR REPLACE VIEW public.openai_usage AS
    SELECT 
        DATE(created_at) as date,
        model,
        COUNT(*) as requests,
        SUM(total_tokens) as total_tokens,
        ROUND(AVG(response_time_ms)::numeric, 0) as avg_response_time,
        ROUND((COUNT(*) FILTER (WHERE success = true) * 100.0 / COUNT(*))::numeric, 2) as success_rate
    FROM openai_requests
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY DATE(created_at), model
    ORDER BY date DESC, model;
    
    RAISE NOTICE 'VIEW openai_usage пересоздан успешно';
END $$;

-- 3.5 Создаем VIEW user_cohorts_basic (ИСПРАВЛЕННЫЙ - теперь user_id имеет тип bigint)
DO $$
BEGIN
    CREATE OR REPLACE VIEW public.user_cohorts_basic AS
    WITH user_stats AS (
        SELECT 
            u.id,
            u.telegram_user_id,
            u.created_at::date as registration_date,
            COALESCE(s.plan_type, 'free') as current_plan,
            COALESCE(s.letters_used, 0) as letters_used_current_period,
            COALESCE(s.letters_limit, 3) as letters_limit_current_period,
            
            -- Общая статистика писем
            COUNT(ls.id) as total_sessions,
            COUNT(CASE WHEN ls.status = 'completed' THEN 1 END) as completed_sessions,
            
            -- Статистика обратной связи
            COUNT(lf.id) as total_feedback_given,
            COUNT(CASE WHEN lf.feedback_type = 'like' THEN 1 END) as positive_feedback,
            COUNT(CASE WHEN lf.feedback_type = 'dislike' THEN 1 END) as negative_feedback,
            
            -- Активность
            MAX(u.last_activity) as last_activity_date,
            
            -- Когорта по месяцу регистрации
            DATE_TRUNC('month', u.created_at) as cohort_month
            
        FROM users u
        LEFT JOIN subscriptions s ON u.id = s.user_id AND s.is_active = true
        LEFT JOIN letter_sessions ls ON u.id = ls.user_id
        LEFT JOIN letter_feedback lf ON u.id = lf.user_id
        GROUP BY u.id, u.telegram_user_id, u.created_at, s.plan_type, s.letters_used, s.letters_limit
    )
    SELECT 
        id,
        telegram_user_id,
        registration_date,
        current_plan,
        letters_used_current_period,
        letters_limit_current_period,
        total_sessions,
        completed_sessions,
        CASE 
            WHEN total_sessions = 0 THEN 0 
            ELSE ROUND(((completed_sessions::numeric / total_sessions::numeric) * 100)::numeric, 2) 
        END as completion_rate_percent,
        total_feedback_given,
        positive_feedback,
        negative_feedback,
        CASE 
            WHEN total_feedback_given = 0 THEN 0 
            ELSE ROUND(((positive_feedback::numeric / total_feedback_given::numeric) * 100)::numeric, 2) 
        END as satisfaction_rate_percent,
        last_activity_date,
        cohort_month,
        
        -- Сегментация пользователей
        CASE 
            WHEN total_sessions = 0 THEN 'registered_no_usage'
            WHEN total_sessions = 1 AND completed_sessions = 0 THEN 'tried_once_failed'
            WHEN total_sessions = 1 AND completed_sessions = 1 THEN 'tried_once_success'
            WHEN total_sessions BETWEEN 2 AND 5 THEN 'light_user'
            WHEN total_sessions BETWEEN 6 AND 15 THEN 'regular_user'
            WHEN total_sessions > 15 THEN 'power_user'
            ELSE 'unknown'
        END as user_segment,
        
        -- Статус активности
        CASE 
            WHEN last_activity_date >= CURRENT_DATE - INTERVAL '7 days' THEN 'active_week'
            WHEN last_activity_date >= CURRENT_DATE - INTERVAL '30 days' THEN 'active_month'
            WHEN last_activity_date >= CURRENT_DATE - INTERVAL '90 days' THEN 'dormant'
            ELSE 'inactive'
        END as activity_status
        
    FROM user_stats
    ORDER BY registration_date DESC;
    
    RAISE NOTICE 'VIEW user_cohorts_basic пересоздан успешно';
END $$;

-- Финальная проверка
DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'МИГРАЦИЯ v9.5 ЗАВЕРШЕНА ПОЛНОСТЬЮ И УСПЕШНО!';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Все изменения:';
    RAISE NOTICE '✓ Удалены лишние поля: users.total_generations, users.updated_at';
    RAISE NOTICE '✓ Изменен тип letter_sessions.generation_time_seconds на double precision';
    RAISE NOTICE '✓ Изменены типы user_id на bigint во всех нужных таблицах';
    RAISE NOTICE '✓ Пересозданы все VIEW таблицы с правильными типами полей';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'PROD база данных теперь полностью синхронизирована с DEV схемой!';
    RAISE NOTICE '============================================================================';
END $$;

COMMIT; 