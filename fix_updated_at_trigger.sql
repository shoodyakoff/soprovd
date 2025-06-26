-- ===================================================
-- ИСПРАВЛЕНИЕ: Удаление триггера updated_at для таблицы users
-- ===================================================
-- Поле updated_at было удалено из таблицы users миграцией v9.5,
-- но триггер остался и вызывает ошибку при обновлении записей

DO $$ 
BEGIN
    RAISE NOTICE '🔧 Удаляю триггер update_users_updated_at...';
END $$;

-- Удаляем триггер который пытается обновить несуществующее поле updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;

DO $$ 
BEGIN
    RAISE NOTICE '✅ Триггер update_users_updated_at успешно удален';
    RAISE NOTICE '🎯 Теперь обновления таблицы users будут работать корректно';
END $$; 