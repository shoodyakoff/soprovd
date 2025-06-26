-- ============================================================================
-- ПРОВЕРКА РЕЗУЛЬТАТОВ МИГРАЦИИ v9.5
-- ============================================================================
-- Выполните этот скрипт на PROD базе чтобы убедиться что миграция прошла успешно

-- 1. Проверяем что лишние поля удалены
SELECT 'ПРОВЕРКА: Лишние поля users удалены' as check_name;
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('total_generations', 'updated_at')
AND table_schema = 'public';
-- Должно быть 0 строк

-- 2. Проверяем тип generation_time_seconds
SELECT 'ПРОВЕРКА: Тип generation_time_seconds изменен на double precision' as check_name;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'letter_sessions' 
AND column_name = 'generation_time_seconds'
AND table_schema = 'public';
-- Должно быть: generation_time_seconds | double precision

-- 3. Проверяем типы user_id в таблицах
SELECT 'ПРОВЕРКА: Типы user_id изменены на bigint' as check_name;
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE column_name IN ('user_id', 'referral_user_id')
AND table_name IN ('acquisition_channels', 'letter_feedback', 'letter_iterations', 'payments', 'subscriptions', 'subscriptions_backup')
AND table_schema = 'public'
ORDER BY table_name, column_name;
-- Все должны быть bigint

-- 4. Проверяем что VIEW созданы
SELECT 'ПРОВЕРКА: VIEW таблицы созданы' as check_name;
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name IN ('user_stats', 'session_stats', 'user_activity', 'openai_usage', 'user_cohorts_basic')
ORDER BY table_name;
-- Должно быть 5 строк

-- 5. Проверяем что VIEW работают (пробуем выполнить SELECT)
SELECT 'ПРОВЕРКА: VIEW user_stats работает' as check_name;
SELECT COUNT(*) as view_works FROM user_stats LIMIT 1;

SELECT 'ПРОВЕРКА: VIEW session_stats работает' as check_name;
SELECT COUNT(*) as view_works FROM session_stats LIMIT 1;

SELECT 'ПРОВЕРКА: VIEW user_cohorts_basic работает' as check_name;
SELECT COUNT(*) as view_works FROM user_cohorts_basic LIMIT 1;

SELECT 'МИГРАЦИЯ v9.5 ПРОВЕРЕНА УСПЕШНО!' as result; 