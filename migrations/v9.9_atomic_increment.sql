-- Миграция v9.9: Атомарное увеличение счетчика писем
-- Дата: 2024-12-19
-- Цель: Устранение race conditions в increment_usage

-- Создание атомарной функции для увеличения счетчика писем
CREATE OR REPLACE FUNCTION increment_user_letters(user_id_param BIGINT)
RETURNS TABLE(new_count INTEGER, can_generate BOOLEAN, plan_type TEXT) AS $$
DECLARE
    subscription_row RECORD;
BEGIN
    -- Атомарно увеличиваем счетчик и получаем все данные
    UPDATE subscriptions 
    SET letters_used = letters_used + 1,
        updated_at = NOW()
    WHERE user_id = user_id_param
    RETURNING letters_used, letters_limit, plan_type, status
    INTO subscription_row;
    
    -- Если подписка не найдена, создаем новую
    IF NOT FOUND THEN
        INSERT INTO subscriptions (
            user_id, 
            letters_used, 
            letters_limit, 
            plan_type,
            status,
            period_start,
            period_end,
            created_at,
            updated_at
        )
        VALUES (
            user_id_param, 
            1, 
            3, 
            'free',
            'active',
            CURRENT_DATE,
            (CURRENT_DATE + INTERVAL '1 month')::DATE,
            NOW(),
            NOW()
        )
        RETURNING letters_used, letters_limit, plan_type, status
        INTO subscription_row;
    END IF;
    
    -- Возвращаем результат
    RETURN QUERY SELECT 
        subscription_row.letters_used,
        (
            subscription_row.status = 'active' AND 
            (
                subscription_row.letters_used < subscription_row.letters_limit OR 
                subscription_row.plan_type = 'premium'
            )
        ),
        subscription_row.plan_type;
END;
$$ LANGUAGE plpgsql;

-- Создание индекса для оптимизации (если не существует)
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);

-- Добавляем комментарий к функции
COMMENT ON FUNCTION increment_user_letters(BIGINT) IS 'Атомарно увеличивает счетчик использованных писем пользователя и возвращает актуальную информацию о лимитах';

-- Проверяем что функция создалась
SELECT 'increment_user_letters function created successfully' as status; 