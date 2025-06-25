-- =====================================================
-- СИСТЕМА ОЦЕНОК И ОБРАТНОЙ СВЯЗИ ДЛЯ ПИСЕМ V7.2
-- УПРОЩЕННАЯ ВЕРСИЯ: ТОЛЬКО ЛАЙКИ/ДИЗЛАЙКИ
-- =====================================================

-- 0. УБЕДИМСЯ ЧТО РАСШИРЕНИЕ UUID ВКЛЮЧЕНО
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. СОЗДАНИЕ УПРОЩЕННОЙ ТАБЛИЦЫ ОЦЕНОК ПИСЕМ
CREATE TABLE IF NOT EXISTS letter_feedback (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES letter_sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL DEFAULT 1,
    
    -- Только лайки и дизлайки, БЕЗ комментариев
    feedback_type VARCHAR(20) CHECK (feedback_type IN ('like', 'dislike')),
    
    -- Метаданные
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Индекс для быстрого поиска
    UNIQUE(session_id, iteration_number)
);

-- 2. МИГРАЦИЯ СУЩЕСТВУЮЩИХ ДАННЫХ (если таблица уже существует)
DO $$ 
BEGIN
    -- Проверяем, существует ли таблица с user_comment
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_feedback' AND column_name='user_comment') THEN
        -- Создаем временную таблицу с новой структурой
        CREATE TABLE letter_feedback_new (
            id SERIAL PRIMARY KEY,
            session_id UUID NOT NULL REFERENCES letter_sessions(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            iteration_number INTEGER NOT NULL DEFAULT 1,
            feedback_type VARCHAR(20) CHECK (feedback_type IN ('like', 'dislike')),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(session_id, iteration_number)
        );
        
        -- Копируем данные, исключая 'comment_only'
        INSERT INTO letter_feedback_new (session_id, user_id, iteration_number, feedback_type, created_at)
        SELECT session_id, user_id, iteration_number, feedback_type, created_at
        FROM letter_feedback 
        WHERE feedback_type IN ('like', 'dislike');
        
        -- Удаляем старую таблицу
        DROP TABLE letter_feedback CASCADE;
        
        -- Переименовываем новую таблицу
        ALTER TABLE letter_feedback_new RENAME TO letter_feedback;
        
        RAISE NOTICE 'Таблица letter_feedback упрощена: убраны комментарии и comment_only';
    END IF;
END $$;

-- 3. ОБНОВЛЕНИЕ ТАБЛИЦЫ LETTER_SESSIONS
-- Добавляем поля для отслеживания итераций
DO $$ 
BEGIN
    -- Максимальное количество итераций
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='max_iterations') THEN
        ALTER TABLE letter_sessions ADD COLUMN max_iterations INTEGER DEFAULT 3;
    END IF;
    
    -- Текущая итерация
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='current_iteration') THEN
        ALTER TABLE letter_sessions ADD COLUMN current_iteration INTEGER DEFAULT 1;
    END IF;
    
    -- Финальная оценка сессии
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='final_rating') THEN
        ALTER TABLE letter_sessions ADD COLUMN final_rating VARCHAR(20);
    END IF;
    
    -- Есть ли обратная связь
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_sessions' AND column_name='has_feedback') THEN
        ALTER TABLE letter_sessions ADD COLUMN has_feedback BOOLEAN DEFAULT false;
    END IF;
END $$;

-- 4. ОБНОВЛЕНИЕ ТАБЛИЦЫ LETTER_ITERATIONS
-- Добавляем связь с оценками
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_iterations' AND column_name='feedback_id') THEN
        ALTER TABLE letter_iterations ADD COLUMN feedback_id INTEGER REFERENCES letter_feedback(id);
    END IF;
    
    -- Тип итерации: initial, improvement
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='letter_iterations' AND column_name='iteration_type') THEN
        ALTER TABLE letter_iterations ADD COLUMN iteration_type VARCHAR(20) DEFAULT 'initial' CHECK (iteration_type IN ('initial', 'improvement'));
    END IF;
END $$;

-- 5. СОЗДАНИЕ ИНДЕКСОВ
CREATE INDEX IF NOT EXISTS idx_letter_feedback_session ON letter_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_letter_feedback_user ON letter_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_letter_feedback_type ON letter_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_letter_feedback_created ON letter_feedback(created_at);

-- 6. НАСТРОЙКА RLS ПОЛИТИК
ALTER TABLE letter_feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage letter feedback" ON letter_feedback;
CREATE POLICY "Service role can manage letter feedback" ON letter_feedback FOR ALL TO service_role USING (true);

-- 7. СОЗДАНИЕ АНАЛИТИЧЕСКИХ ПРЕДСТАВЛЕНИЙ

-- Упрощенная статистика оценок (без комментариев)
CREATE OR REPLACE VIEW feedback_stats AS
SELECT 
    feedback_type,
    COUNT(*) as count,
    ROUND(COUNT(*)::numeric * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM letter_feedback 
GROUP BY feedback_type;

-- Статистика итераций
CREATE OR REPLACE VIEW iteration_stats AS
SELECT 
    ls.current_iteration,
    COUNT(*) as sessions_count,
    COUNT(CASE WHEN lf.feedback_type = 'like' THEN 1 END) as likes,
    COUNT(CASE WHEN lf.feedback_type = 'dislike' THEN 1 END) as dislikes,
    ROUND(AVG(CASE WHEN lf.feedback_type = 'like' THEN 1 WHEN lf.feedback_type = 'dislike' THEN 0 END) * 100, 2) as satisfaction_rate
FROM letter_sessions ls
LEFT JOIN letter_feedback lf ON ls.id = lf.session_id
WHERE ls.current_iteration > 0
GROUP BY ls.current_iteration
ORDER BY ls.current_iteration;

-- Детальная обратная связь теперь только в letter_iterations
CREATE OR REPLACE VIEW detailed_feedback AS
SELECT 
    li.id,
    li.session_id,
    u.username,
    li.iteration_number,
    li.user_feedback,
    li.improvement_request,
    li.created_at,
    ls.job_description_length,
    ls.resume_length
FROM letter_iterations li
JOIN users u ON li.user_id = u.id
JOIN letter_sessions ls ON li.session_id = ls.id
WHERE li.user_feedback IS NOT NULL 
  AND LENGTH(li.user_feedback) > 10
ORDER BY li.created_at DESC;

-- 8. ФУНКЦИЯ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ СТАТИСТИКИ СЕССИЙ
CREATE OR REPLACE FUNCTION update_session_feedback_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Обновляем has_feedback в letter_sessions
    UPDATE letter_sessions 
    SET has_feedback = true
    WHERE id = NEW.session_id;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автообновления статистики
DROP TRIGGER IF EXISTS update_session_feedback_trigger ON letter_feedback;
CREATE TRIGGER update_session_feedback_trigger 
    AFTER INSERT ON letter_feedback 
    FOR EACH ROW EXECUTE FUNCTION update_session_feedback_stats();

-- 9. ИНИЦИАЛИЗАЦИЯ СУЩЕСТВУЮЩИХ СЕССИЙ
-- Устанавливаем значения по умолчанию для существующих сессий
UPDATE letter_sessions 
SET 
    max_iterations = 3,
    current_iteration = 1,
    has_feedback = false
WHERE max_iterations IS NULL;

-- 10. ФИНАЛЬНАЯ ПРОВЕРКА
DO $$
BEGIN
    RAISE NOTICE 'Упрощенная система оценок v7.2 готова!';
    RAISE NOTICE 'Таблица letter_feedback: только like/dislike БЕЗ комментариев';
    RAISE NOTICE 'Детальные комментарии: в letter_iterations через user_feedback';
    RAISE NOTICE 'Создано представлений: feedback_stats, iteration_stats, detailed_feedback';
    RAISE NOTICE 'Максимум итераций по умолчанию: 3';
END $$; 