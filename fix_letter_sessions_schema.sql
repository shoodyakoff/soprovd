-- ===================================================
-- ИСПРАВЛЕНИЕ СХЕМЫ ТАБЛИЦЫ letter_sessions
-- Добавляем недостающие колонки для аналитики
-- ===================================================

-- Добавляем недостающие колонки
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS mode VARCHAR(20);
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS job_description_length INTEGER;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS resume_length INTEGER;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS selected_style VARCHAR(50);
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS detected_profession VARCHAR(100);
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS detected_level VARCHAR(50);
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS confidence_score FLOAT;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS suggested_style VARCHAR(50);
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS generated_letter_length INTEGER;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS openai_model_used VARCHAR(50);
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS openai_tokens_used INTEGER;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS user_regenerated BOOLEAN DEFAULT FALSE;
ALTER TABLE letter_sessions ADD COLUMN IF NOT EXISTS user_rating INTEGER;

-- Проверяем текущую структуру таблицы
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'letter_sessions' 
ORDER BY ordinal_position; 