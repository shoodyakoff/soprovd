#!/usr/bin/env python3
"""
Тестовый скрипт для проверки webhook обработки
"""
import asyncio
import sys
import os
import json

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.payment_service import payment_service

async def test_webhook_processing():
    """Тестирует обработку webhook с реальными данными"""
    try:
        # Данные реального платежа из БД
        payment_id = "2ff3391e-000f-5001-8000-1ea01f6603f9"
        user_id = 5
        telegram_id = 678674926
        
        print(f"🧪 Тестирую webhook обработку для платежа: {payment_id}")
        
        # Создаем тестовые webhook данные
        test_webhook_data = {
            "event": "payment.succeeded",
            "object": {
                "id": payment_id,
                "status": "succeeded",
                "amount": {
                    "value": "1.00",
                    "currency": "RUB"
                },
                "metadata": {
                    "user_id": str(user_id),
                    "telegram_id": str(telegram_id),
                    "subscription_type": "premium"
                }
            }
        }
        
        print(f"📋 Тестовые webhook данные:")
        print(json.dumps(test_webhook_data, indent=2))
        
        # Обрабатываем webhook
        print(f"\n🔄 Обрабатываю webhook...")
        success = await payment_service.process_webhook(test_webhook_data)
        
        if success:
            print(f"✅ Webhook обработан успешно!")
            
            # Проверяем статус платежа после обработки
            status = await payment_service.get_payment_status(payment_id)
            print(f"📊 Статус платежа после обработки: {status}")
            
        else:
            print(f"❌ Webhook обработка не удалась!")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании webhook: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Основная функция"""
    await test_webhook_processing()

if __name__ == "__main__":
    asyncio.run(main()) 