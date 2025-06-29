-- ============================================================================
-- Migration: vX.X_feature_name_description
-- Release: vX_feature_name  
-- Date: YYYY-MM-DD
-- Author: Developer Name
-- Description: Brief description of what this migration does
-- ============================================================================

-- ВАЖНО: Каждая миграция должна быть идемпотентной!
-- Используйте IF NOT EXISTS, IF EXISTS и другие проверки

BEGIN;

-- ============================================================================
-- 1. СОЗДАНИЕ НОВЫХ ТАБЛИЦ
-- ============================================================================

-- Пример создания таблицы
CREATE TABLE IF NOT EXISTS new_table_name (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Основные поля
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    
    -- Метаданные
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 2. ИНДЕКСЫ
-- ============================================================================

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_new_table_user_id ON new_table_name(user_id);
CREATE INDEX IF NOT EXISTS idx_new_table_status ON new_table_name(status);

-- ============================================================================
-- 3. ИЗМЕНЕНИЕ СУЩЕСТВУЮЩИХ ТАБЛИЦ
-- ============================================================================

-- Добавление новых столбцов
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'existing_table' AND column_name = 'new_column'
    ) THEN
        ALTER TABLE existing_table ADD COLUMN new_column VARCHAR(255);
    END IF;
END $$;

-- ============================================================================
-- 4. ПРЕДСТАВЛЕНИЯ (VIEWS)
-- ============================================================================

-- Создание или обновление представлений
CREATE OR REPLACE VIEW view_name AS
SELECT 
    id,
    name,
    status,
    created_at
FROM new_table_name
WHERE status = 'active';

-- ============================================================================
-- 5. ФУНКЦИИ И ТРИГГЕРЫ
-- ============================================================================

-- Создание функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггера
DROP TRIGGER IF EXISTS update_new_table_updated_at ON new_table_name;
CREATE TRIGGER update_new_table_updated_at
    BEFORE UPDATE ON new_table_name
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. ДАННЫЕ (SEEDS)
-- ============================================================================

-- Вставка начальных данных (только если их нет)
INSERT INTO new_table_name (name, status)
SELECT 'Default Name', 'active'
WHERE NOT EXISTS (
    SELECT 1 FROM new_table_name WHERE name = 'Default Name'
);

-- ============================================================================
-- 7. РАЗРЕШЕНИЯ (RLS)
-- ============================================================================

-- Включение Row Level Security если нужно
-- ALTER TABLE new_table_name ENABLE ROW LEVEL SECURITY;

-- Создание политик RLS
-- CREATE POLICY user_can_see_own_data ON new_table_name
--     FOR ALL TO authenticated
--     USING (user_id = auth.uid());

COMMIT;

-- ============================================================================
-- NOTES:
-- - Всегда тестируйте миграции на dev окружении
-- - Создавайте backup перед применением в production
-- - Документируйте все изменения в комментариях
-- - Используйте транзакции для атомарности
-- ============================================================================ 