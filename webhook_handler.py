"""
Webhook Handler для ЮKassa v10.1
FastAPI сервер для обработки уведомлений от платежной системы
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
import uvicorn
import os

from services.payment_service import payment_service
from config import WEBHOOK_HOST, WEBHOOK_PATH, YOOKASSA_ENABLED

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения bot instance
bot_instance = None

def set_bot_instance(bot):
    """Устанавливает bot instance для отправки сообщений пользователям"""
    global bot_instance
    bot_instance = bot
    logger.info("🤖 Bot instance set for webhook handler")

def get_bot_instance():
    """Получает bot instance"""
    return bot_instance

# Создаем FastAPI приложение
app = FastAPI(
    title="ЮKassa Webhook Handler",
    description="Обработчик webhook'ов для платежей Premium подписок",
    version="10.1.0"
)

# Middleware для проверки IP-адресов (ВРЕМЕННО ОТКЛЮЧЕНА ДЛЯ ДИАГНОСТИКИ НА ПРОДЕ)
# @app.middleware("http")
# async def ip_check_middleware(request: Request, call_next):
#     """Проверяет, что IP-адрес входит в доверенные подсети ЮKassa."""
#     # ... существующий код middleware ...
#     client_ip = request.client.host
#
#     # Список доверенных IP-адресов и подсетей ЮKassa
#     # https://yookassa.ru/developers/using-api/webhooks#ip-addresses
#     trusted_ips = [
#         "185.71.76.0/27",
#         "185.71.77.0/27",
#         "77.75.153.0/25",
#         "77.75.154.128/25",
#         "2a02:5180:0:1::/64",
#         "2a02:5180:0:2::/64",
#         "2a02:5180:0:3::/64",
#         "2a02:5180:0:4::/64"
#     ]
#
#     ip_is_trusted = any(ip_address(client_ip) in ip_network(net) for net in trusted_ips)
#
#     if not ip_is_trusted:
#         logger.warning(f"🚫 Denied access from untrusted IP: {client_ip}")
#         return JSONResponse(
#             status_code=403,
#             content={"detail": "Forbidden: IP address not trusted"}
#         )
#
#     logger.info(f"✅ Granted access from trusted IP: {client_ip}")
#     response = await call_next(request)
#     return response

@app.get("/health")
async def health_check():
    """Простая конечная точка для проверки работоспособности сервиса."""
    logger.info("✅ Health check endpoint was hit!")
    return {"status": "OK"}

@app.post(WEBHOOK_PATH)
async def handle_yookassa_webhook(request: Request):
    """
    Обрабатывает webhook от ЮKassa
    
    Поддерживаемые события:
    - payment.succeeded - успешная оплата
    - payment.canceled - отмена платежа
    - refund.succeeded - возврат средств
    """
    try:
        # Получаем тело запроса
        body = await request.body()
        webhook_data = json.loads(body.decode('utf-8'))
        
        # Логируем входящий webhook
        event = webhook_data.get('event', 'unknown')
        logger.info(f"🔔 Received ЮKassa webhook, event={event}")
        
        # Проверяем что платежи включены
        if not YOOKASSA_ENABLED:
            logger.warning("⚠️ Webhook received but payments are disabled")
            return JSONResponse(
                status_code=200,
                content={"status": "ignored", "reason": "payments_disabled"}
            )
        
        # Обрабатываем webhook
        success = await payment_service.process_webhook(webhook_data)
        
        if success:
            logger.info(f"✅ Webhook processed successfully for event: {event}")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "event": event}
            )
        else:
            logger.error(f"❌ Failed to process webhook for event: {event}")
            return JSONResponse(
                status_code=400,
                content={"status": "error", "event": event, "reason": "processing_failed"}
            )
            
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/webhook/test")
async def test_webhook():
    """Тестовый endpoint для проверки webhook обработки"""
    test_data = {
        "event": "payment.succeeded",
        "object": {
            "id": "test_payment_123",
            "status": "succeeded",
            "metadata": {
                "user_id": "1",
                "telegram_id": "123456789",
                "subscription_type": "premium"
            }
        }
    }
    
    try:
        success = await payment_service.process_webhook(test_data)
        return {
            "status": "success" if success else "error",
            "test_data": test_data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "test_data": test_data
        }

@app.post("/webhook/yookassa/test")
async def test_yookassa_webhook(user_id: int = 5):
    """
    Тестовый endpoint для проверки webhook с указанным пользователем
    
    Args:
        user_id: ID пользователя для тестирования (по умолчанию 5)
    """
    payment_id = f"test_payment_{user_id}_{int(asyncio.get_event_loop().time())}"
    
    # Используем реальный Telegram ID для тестирования (ваш ID)
    real_telegram_id = 678674926  # Замените на ваш реальный Telegram ID
    
    test_data = {
        "event": "payment.succeeded",
        "object": {
            "id": payment_id,
            "status": "succeeded",
            "amount": {
                "value": "199.00",
                "currency": "RUB"
            },
            "metadata": {
                "user_id": str(user_id),
                "telegram_id": str(real_telegram_id),
                "subscription_type": "premium"
            }
        }
    }
    
    try:
        logger.info(f"🧪 Testing webhook for user {user_id} with telegram_id {real_telegram_id}")
        
        # Сначала сохраняем тестовый платеж в БД
        save_success = await payment_service._save_payment_to_db(
            payment_id=payment_id,
            user_id=user_id,
            amount=199.00,
            status="pending",
            confirmation_url="https://test.yookassa.ru/payment",
            metadata=test_data["object"]["metadata"]
        )
        
        if not save_success:
            logger.error(f"❌ Failed to save test payment {payment_id} to DB")
            return {
                "status": "error",
                "message": f"Failed to save test payment to DB",
                "test_data": test_data,
                "timestamp": asyncio.get_event_loop().time()
            }
        
        logger.info(f"✅ Test payment {payment_id} saved to DB")
        
        # Теперь обрабатываем webhook
        success = await payment_service.process_webhook(test_data)
        
        if success:
            logger.info(f"✅ Test webhook successful for user {user_id}")
            return {
                "status": "success",
                "message": f"Test webhook processed successfully for user {user_id}",
                "test_data": test_data,
                "timestamp": asyncio.get_event_loop().time()
            }
        else:
            logger.error(f"❌ Test webhook failed for user {user_id}")
            return {
                "status": "error",
                "message": f"Test webhook processing failed for user {user_id}",
                "test_data": test_data,
                "timestamp": asyncio.get_event_loop().time()
            }
            
    except Exception as e:
        logger.error(f"❌ Test webhook exception for user {user_id}: {e}")
        return {
            "status": "error",
            "message": f"Test webhook exception: {str(e)}",
            "test_data": test_data,
            "timestamp": asyncio.get_event_loop().time()
        }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )

def start_webhook_server(bot=None):
    """Запускает webhook сервер"""
    if bot:
        set_bot_instance(bot)
        logger.info(f"🤖 Bot instance set for webhook server")
    
    # Railway предоставляет порт через переменную PORT
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Starting webhook server on {WEBHOOK_HOST}:{port}")
    logger.info(f"🔗 Webhook endpoint: {WEBHOOK_PATH}")
    
    uvicorn.run(
        "webhook_handler:app",
        host=WEBHOOK_HOST,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    start_webhook_server() 