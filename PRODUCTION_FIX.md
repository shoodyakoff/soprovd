-- Исправление функции increment_user_letters
DROP FUNCTION IF EXISTS increment_user_letters(BIGINT);

CREATE OR REPLACE FUNCTION increment_user_letters(user_id_param BIGINT)
RETURNS TABLE(new_count INTEGER, can_generate BOOLEAN, plan_type VARCHAR(20)) AS $$
DECLARE
    subscription_row RECORD;
BEGIN
    UPDATE subscriptions 
    SET letters_used = subscriptions.letters_used + 1,
        updated_at = NOW()
    WHERE subscriptions.user_id = user_id_param
    RETURNING subscriptions.letters_used, subscriptions.letters_limit, subscriptions.plan_type, subscriptions.status
    INTO subscription_row;
    
    IF NOT FOUND THEN
        INSERT INTO subscriptions (
            user_id, letters_used, letters_limit, plan_type, status,
            period_start, period_end, created_at, updated_at
        )
        VALUES (
            user_id_param, 1, 3, 'free', 'active',
            CURRENT_DATE, (CURRENT_DATE + INTERVAL '1 month')::DATE, NOW(), NOW()
        )
        RETURNING subscriptions.letters_used, subscriptions.letters_limit, subscriptions.plan_type, subscriptions.status
        INTO subscription_row;
    END IF;
    
    RETURN QUERY SELECT 
        subscription_row.letters_used,
        (subscription_row.status = 'active' AND 
         (subscription_row.letters_used < subscription_row.letters_limit OR 
          subscription_row.plan_type = 'premium')),
        subscription_row.plan_type;
END;
$$ LANGUAGE plpgsql;

SELECT 'increment_user_letters function fixed successfully' as status; 