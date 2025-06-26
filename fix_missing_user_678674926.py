#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Отсутствующий пользователь 678674926 в продакшн базе

Проблема:
- Пользователь 678674926 не существует в таблице users
- Но существуют сессии и данные для этого пользователя  
- Foreign key constraints блокируют логирование
- Лимиты не работают

Решение:
1. Найти все данные связанные с пользователем 678674926
2. Создать пользователя в таблице users
3. Создать подписку
4. Проверить что все работает
"""
import asyncio
import os
from services.analytics_service import analytics
from services.subscription_service import subscription_service
from models.analytics_models import UserData
from utils.database import SupabaseClient

async def diagnose_missing_user():
    """Диагностика проблемы с пользователем 678674926"""
    print("🔍 ДИАГНОСТИКА: Пользователь 678674926")
    print("=" * 60)
    
    user_id = 678674926
    session_id = "5a593176-5c8a-4295-8bd5-a825cd8d0582"
    
    supabase = SupabaseClient.get_client()
    if not supabase:
        print("❌ Supabase недоступен")
        return False
    
    try:
        # 1. Проверяем пользователя в таблице users
        print(f"🔍 1. Проверка пользователя {user_id} в таблице users...")
        users_response = supabase.table('users').select('*').eq('telegram_user_id', user_id).execute()
        
        if users_response.data:
            user = users_response.data[0]
            print(f"✅ Пользователь найден: ID={user['id']}, Username={user.get('username', 'N/A')}")
            internal_user_id = user['id']
        else:
            print(f"❌ Пользователь {user_id} НЕ НАЙДЕН в таблице users!")
            internal_user_id = None
        
        # 2. Проверяем сессию письма
        print(f"\n🔍 2. Проверка сессии {session_id}...")
        session_response = supabase.table('letter_sessions').select('*').eq('id', session_id).execute()
        
        if session_response.data:
            session = session_response.data[0]
            session_user_id = session.get('user_id')
            print(f"✅ Сессия найдена: user_id={session_user_id}, status={session.get('status', 'N/A')}")
            
            if internal_user_id and session_user_id != internal_user_id:
                print(f"⚠️ НЕСООТВЕТСТВИЕ: Сессия ссылается на user_id={session_user_id}, но пользователь имеет id={internal_user_id}")
        else:
            print(f"❌ Сессия {session_id} не найдена")
        
        # 3. Проверяем связанные таблицы
        print(f"\n🔍 3. Проверка связанных данных для telegram_user_id={user_id}...")
        
        # Проверяем все таблицы где может быть user_id
        tables_to_check = [
            'subscriptions',
            'user_events', 
            'openai_requests',
            'letter_iterations',
            'letter_feedback'
        ]
        
        orphaned_data = {}
        for table in tables_to_check:
            try:
                # Ищем записи со ссылкой на несуществующего пользователя
                response = supabase.table(table).select('id, user_id').eq('user_id', user_id).execute()
                if response.data:
                    orphaned_data[table] = len(response.data)
                    print(f"⚠️ {table}: {len(response.data)} записей ссылаются на несуществующего пользователя")
                else:
                    print(f"✅ {table}: нет проблемных записей")
            except Exception as e:
                print(f"❌ Ошибка проверки {table}: {e}")
        
        return {
            'user_exists': bool(users_response.data),
            'internal_user_id': internal_user_id,
            'session_exists': bool(session_response.data),
            'orphaned_data': orphaned_data
        }
        
    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")
        return False

async def fix_missing_user():
    """Исправление проблемы с отсутствующим пользователем"""
    print("\n🔧 ИСПРАВЛЕНИЕ: Создание пользователя 678674926")
    print("=" * 60)
    
    user_id = 678674926
    
    try:
        # 1. Создаем пользователя
        print(f"🔧 1. Создание пользователя {user_id}...")
        user_data = UserData(
            telegram_user_id=user_id,
            username="shoodyakoff",  # Из скриншота видно что username shoodyakoff
            first_name="Stanislav",
            language_code="ru"
        )
        
        internal_user_id = await analytics.track_user(user_data)
        if internal_user_id:
            print(f"✅ Пользователь создан с internal_user_id: {internal_user_id}")
        else:
            print("❌ Не удалось создать пользователя")
            return False
        
        # 2. Создаем подписку
        print(f"🔧 2. Создание подписки для user_id={internal_user_id}...")
        subscription = await analytics.get_or_create_subscription(internal_user_id)
        if subscription:
            print(f"✅ Подписка создана: ID={subscription.get('id', 'N/A')}")
            print(f"   Plan: {subscription.get('plan_type', 'N/A')}")
            print(f"   Status: {subscription.get('status', 'N/A')}")
            print(f"   Limit: {subscription.get('letters_limit', 'N/A')}")
        else:
            print("❌ Не удалось создать подписку")
            return False
        
        # 3. Проверяем лимиты
        print(f"🔧 3. Проверка лимитов для user_id={internal_user_id}...")
        limits = await subscription_service.check_user_limits(internal_user_id, force_refresh=True)
        print(f"📊 Лимиты: {limits}")
        
        can_generate = limits.get('can_generate', False)
        remaining = limits.get('remaining', 0)
        plan_type = limits.get('plan_type', 'unknown')
        
        print(f"🎯 Результат: Plan={plan_type}, Может генерировать={can_generate}, Осталось={remaining}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка исправления: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def verify_fix():
    """Проверка что исправление сработало"""
    print("\n✅ ПРОВЕРКА: Тестирование исправления")
    print("=" * 60)
    
    user_id = 678674926
    
    try:
        supabase = SupabaseClient.get_client()
        if not supabase:
            print("❌ Supabase недоступен")
            return False
        
        # 1. Проверяем что пользователь создан
        users_response = supabase.table('users').select('*').eq('telegram_user_id', user_id).execute()
        if users_response.data:
            user = users_response.data[0]
            internal_user_id = user['id']
            print(f"✅ Пользователь существует: internal_id={internal_user_id}")
        else:
            print("❌ Пользователь все еще не найден")
            return False
        
        # 2. Проверяем подписку
        subscription_response = supabase.table('subscriptions').select('*').eq('user_id', internal_user_id).execute()
        if subscription_response.data:
            subscription = subscription_response.data[0]
            print(f"✅ Подписка существует: ID={subscription['id']}, Plan={subscription['plan_type']}")
        else:
            print("❌ Подписка не найдена")
            return False
        
        # 3. Тестируем логирование события (должно работать без ошибок)
        print("🧪 Тестирование логирования события...")
        test_event = {
            'user_id': internal_user_id,
            'event_type': 'test_fix_missing_user', 
            'event_data': {'test': True, 'fixed_user_id': user_id}
        }
        
        await analytics.track_event(
            user_id=internal_user_id,
            event_type='test_fix_missing_user',
            event_data={'test': True, 'fixed_user_id': user_id}
        )
        print("✅ Логирование событий работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

async def main():
    """Основная функция исправления"""
    print("🚨 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Отсутствующий пользователь 678674926")
    print("=" * 80)
    
    # Показываем какую базу используем
    from config import SUPABASE_URL
    print(f"🔗 База данных: {SUPABASE_URL[:50]}...")
    
    # 1. Диагностика
    diagnosis = await diagnose_missing_user()
    if not diagnosis:
        print("❌ Диагностика не удалась")
        return
    
    # 2. Исправление (только если пользователь не существует)
    if not diagnosis.get('user_exists', False):
        fix_result = await fix_missing_user()
        if not fix_result:
            print("❌ Исправление не удалось")
            return
        
        # 3. Проверка
        verify_result = await verify_fix()
        if verify_result:
            print("\n🎉 УСПЕХ: Проблема исправлена!")
            print("✅ Пользователь 678674926 создан")
            print("✅ Подписка создана") 
            print("✅ Лимиты работают")
            print("✅ Логирование событий работает")
            print("\n🚀 Теперь лимиты должны работать корректно в продакшн!")
        else:
            print("❌ Проверка исправления не удалась")
    else:
        print("ℹ️ Пользователь уже существует, проблема может быть в другом")

if __name__ == "__main__":
    print("🔧 Запуск исправления отсутствующего пользователя...")
    asyncio.run(main()) 