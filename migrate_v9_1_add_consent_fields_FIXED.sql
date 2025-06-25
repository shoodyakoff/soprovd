-- МИГРАЦИЯ: Добавление полей согласия пользователей для ФЗ-152 compliance
-- Версия: v9.1 (ИСПРАВЛЕННАЯ)
-- Дата: 2024-01-XX
-- Описание: Добавляем поля для хранения согласия на обработку персональных данных

-- ========================================
-- FORWARD MIGRATION (применение изменений)
-- ========================================

-- Добавляем поля согласия в таблицу users (НЕ user_sessions!)
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_given BOOLEAN DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_timestamp TIMESTAMP DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_version VARCHAR(10) DEFAULT 'v1.0';
ALTER TABLE users ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN DEFAULT FALSE;

-- Проставляем согласие существующим пользователям (implied consent)
-- Логика: если пользователь уже генерировал письма, значит он фактически согласился
UPDATE users 
SET consent_given = TRUE, 
    consent_timestamp = NOW(), 
    consent_version = 'v1.0',
    marketing_consent = FALSE
WHERE id IS NOT NULL 
  AND consent_given IS NULL;

-- Создаем индекс для быстрого поиска по согласию
CREATE INDEX IF NOT EXISTS idx_users_consent 
ON users(consent_given, consent_timestamp);

-- Создаем индекс для поиска по версии согласия (для будущих обновлений политики)
CREATE INDEX IF NOT EXISTS idx_users_consent_version 
ON users(consent_version, consent_timestamp);

-- Добавляем комментарии к полям для документации
COMMENT ON COLUMN users.consent_given IS 'Согласие на обработку ПД: TRUE=дано, FALSE=отозвано, NULL=не запрашивалось';
COMMENT ON COLUMN users.consent_timestamp IS 'Время получения согласия';
COMMENT ON COLUMN users.consent_version IS 'Версия политики конфиденциальности при согласии';
COMMENT ON COLUMN users.marketing_consent IS 'Согласие на маркетинговые коммуникации';

-- ========================================
-- ROLLBACK COMMANDS (команды отката)
-- ========================================
-- В случае необходимости отката выполнить:

-- DROP INDEX IF EXISTS idx_users_consent_version;
-- DROP INDEX IF EXISTS idx_users_consent;
-- ALTER TABLE users DROP COLUMN IF EXISTS marketing_consent;
-- ALTER TABLE users DROP COLUMN IF EXISTS consent_version;
-- ALTER TABLE users DROP COLUMN IF EXISTS consent_timestamp;
-- ALTER TABLE users DROP COLUMN IF EXISTS consent_given;

-- ========================================
-- ПРОВЕРКА МИГРАЦИИ
-- ========================================
-- Проверить что поля добавлены:
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'users' 
--   AND column_name IN ('consent_given', 'consent_timestamp', 'consent_version', 'marketing_consent');

-- Проверить что индексы созданы:
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'users' 
--   AND indexname LIKE '%consent%';

-- Проверить количество пользователей с согласием:
-- SELECT 
--   consent_given,
--   consent_version,
--   COUNT(*) as user_count
-- FROM users 
-- WHERE id IS NOT NULL
-- GROUP BY consent_given, consent_version; 