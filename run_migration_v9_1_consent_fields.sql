-- МИГРАЦИЯ v9.1: Добавление полей согласия для ФЗ-152
-- Выполнить в Supabase SQL Editor

-- 1. Добавляем поля согласия
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_given BOOLEAN DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_timestamp TIMESTAMP DEFAULT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_version VARCHAR(10) DEFAULT 'v1.0';
ALTER TABLE users ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN DEFAULT FALSE;

-- 2. Проставляем согласие существующим пользователям (implied consent)
UPDATE users 
SET consent_given = TRUE, 
    consent_timestamp = NOW(), 
    consent_version = 'v1.0',
    marketing_consent = FALSE
WHERE id IS NOT NULL 
  AND consent_given IS NULL;

-- 3. Создаем индексы
CREATE INDEX IF NOT EXISTS idx_users_consent ON users(consent_given, consent_timestamp);

-- 4. Проверка результата
SELECT 
  consent_given,
  consent_version,
  COUNT(*) as user_count
FROM users 
WHERE id IS NOT NULL
GROUP BY consent_given, consent_version; 