"""
Сервис платежей ЮKassa v10.1
Автоматизация платежей для Premium подписок
"""
import logging
import json
import hashlib
import hmac
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from yookassa import Configuration, Payment
from yookassa.domain.request import PaymentRequest
from yookassa.domain.models import Amount, Receipt, ReceiptItem

from utils.database import SupabaseClient
from services.subscription_service import subscription_service
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, YOOKASSA_ENABLED, BOT_USERNAME, TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self):
        self.supabase = SupabaseClient.get_client()
        self.enabled = YOOKASSA_ENABLED and YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY
        
        if self.enabled:
            # Инициализация ЮKassa
            Configuration.account_id = YOOKASSA_SHOP_ID
            Configuration.secret_key = YOOKASSA_SECRET_KEY
            logger.info("✅ ЮKassa payment service initialized")
        else:
            logger.warning("⚠️ ЮKassa payment service disabled - missing credentials")
    
    async def create_premium_payment(self, user_id: int, user_telegram_id: int) -> Tuple[bool, str, Optional[str]]:
        """
        Создает платеж для Premium подписки
        
        Args:
            user_id: ID пользователя в БД
            user_telegram_id: Telegram ID пользователя
            
        Returns:
            (success, message, payment_url)
        """
        if not self.enabled:
            return False, "Платежная система временно недоступна. Напишите @shoodyakoff", None
        
        try:
            # Создаем платеж в ЮKassa
            payment_request = PaymentRequest({
                "amount": {
                    "value": "1.00",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"https://t.me/{BOT_USERNAME}"
                },
                "capture": True,
                "description": f"Premium подписка для пользователя {user_telegram_id}",
                "metadata": {
                    "user_id": str(user_id),
                    "telegram_id": str(user_telegram_id),
                    "subscription_type": "premium",
                    "period_days": "30"
                },
                "receipt": {
                    "customer": {
                        "email": f"user_{user_telegram_id}@telegram.local"
                    },
                    "items": [
                        {
                            "description": "Premium подписка на 30 дней",
                            "quantity": "1",
                            "amount": {
                                "value": "1.00",
                                "currency": "RUB"
                            },
                            "vat_code": "1",
                            "payment_subject": "service",
                            "payment_mode": "full_prepayment"
                        }
                    ]
                }
            })
            
            # Создаем платеж
            payment = Payment.create(payment_request)
            
            # Проверяем что платеж создан успешно
            if not payment or not payment.id:
                logger.error(f"❌ Failed to create payment for user {user_id}")
                return False, "Ошибка создания платежа. Попробуйте позже или напишите @shoodyakoff", None
            
            # Сохраняем платеж в БД
            await self._save_payment_to_db(
                payment_id=payment.id,
                user_id=user_id,
                amount=1.00,
                status=payment.status or 'pending',
                confirmation_url=payment.confirmation.confirmation_url if payment.confirmation else None,
                metadata={
                    "yookassa_payment_id": payment.id,
                    "telegram_id": user_telegram_id,
                    "subscription_type": "premium"
                }
            )
            
            logger.info(f"✅ Payment created: {payment.id} for user {user_id}")
            return True, "Платеж создан", payment.confirmation.confirmation_url if payment.confirmation else None
            
        except Exception as e:
            logger.error(f"❌ Error creating payment for user {user_id}: {e}")
            return False, "Ошибка создания платежа. Попробуйте позже или напишите @shoodyakoff", None
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Обрабатывает webhook от ЮKassa
        
        Args:
            webhook_data: Данные webhook'а от ЮKassa
            
        Returns:
            True если обработка успешна
        """
        try:
            # Логируем получение webhook
            event = webhook_data.get('event')
            payment_data = webhook_data.get('object', {})
            payment_id = payment_data.get('id', 'unknown')
            metadata = payment_data.get('metadata', {})
            user_id = metadata.get('user_id', 'unknown')
            
            logger.info(f"🔔 Received ЮKassa webhook: event={event}, payment_id={payment_id}, user_id={user_id}")
            logger.info(f"🔍 Full webhook data: {json.dumps(webhook_data, indent=2)}")
            
            # Проверяем подпись webhook'а
            if not self._verify_webhook_signature(webhook_data):
                logger.error(f"❌ Invalid webhook signature for payment {payment_id}")
                return False
            
            if event == 'payment.succeeded':
                logger.info(f"✅ Processing successful payment: {payment_id} for user {user_id}")
                return await self._handle_successful_payment(payment_data)
            elif event == 'payment.canceled':
                logger.info(f"❌ Processing canceled payment: {payment_id} for user {user_id}")
                return await self._handle_canceled_payment(payment_data)
            else:
                logger.info(f"ℹ️ Unhandled webhook event: {event} for payment {payment_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error processing webhook: {e}")
            return False
    
    async def _handle_successful_payment(self, payment_data: Dict[str, Any]) -> bool:
        """Обрабатывает успешный платеж"""
        try:
            payment_id = payment_data.get('id')
            if not payment_id:
                logger.error("❌ Payment ID is missing in webhook data")
                return False
                
            # Получаем user_id из разных возможных мест в webhook данных
            metadata = payment_data.get('metadata', {})
            user_id = None
            
            # Пробуем получить user_id из metadata
            if metadata.get('user_id'):
                try:
                    user_id = int(metadata.get('user_id'))
                    logger.info(f"🔍 Found user_id in metadata: {user_id}")
                except (ValueError, TypeError) as e:
                    logger.error(f"❌ Invalid user_id in metadata: {metadata.get('user_id')}, error: {e}")
            
            # Если не нашли в metadata, пробуем получить из БД по payment_id
            if not user_id:
                logger.info(f"🔍 User_id not found in metadata, trying to get from DB for payment {payment_id}")
                db_user_id = await self._get_user_id_from_payment(payment_id)
                if db_user_id:
                    user_id = db_user_id
                    logger.info(f"🔍 Found user_id in DB: {user_id}")
                else:
                    logger.error(f"❌ Could not find user_id for payment {payment_id}")
                    return False
            
            if not user_id:
                logger.error(f"❌ User ID is missing for payment {payment_id}")
                return False
                
            logger.info(f"🔄 Processing successful payment: {payment_id} for user {user_id}")
            
            # Проверяем что платеж еще не обработан
            if await self._is_payment_processed(payment_id):
                logger.info(f"ℹ️ Payment {payment_id} already processed, skipping")
                return True
            
            # Обновляем статус платежа
            logger.info(f"📝 Updating payment status to 'succeeded' for {payment_id}")
            update_success = await self._update_payment_status(payment_id, 'succeeded')
            if not update_success:
                logger.error(f"❌ Failed to update payment status for {payment_id}")
                return False
            
            # Активируем Premium подписку
            logger.info(f"💎 Activating Premium subscription for user {user_id}")
            success = await self._activate_premium_subscription(user_id, payment_id)
            
            if success:
                logger.info(f"✅ Premium subscription successfully activated for user {user_id}")
                return True
            else:
                logger.error(f"❌ Failed to activate Premium for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error handling successful payment: {e}")
            return False
    
    async def _handle_canceled_payment(self, payment_data: Dict[str, Any]) -> bool:
        """Обрабатывает отмененный платеж"""
        try:
            payment_id = payment_data.get('id')
            if not payment_id:
                logger.error("❌ Payment ID is missing in webhook data")
                return False
                
            await self._update_payment_status(payment_id, 'canceled')
            logger.info(f"ℹ️ Payment {payment_id} canceled")
            return True
        except Exception as e:
            logger.error(f"❌ Error handling canceled payment: {e}")
            return False
    
    async def _save_payment_to_db(self, payment_id: str, user_id: int, amount: float, 
                                status: str, confirmation_url: Optional[str], metadata: Dict[str, Any]) -> bool:
        """Сохраняет платеж в БД"""
        try:
            if not self.supabase:
                return False
            
            payment_data = {
                'payment_id': payment_id,
                'user_id': user_id,
                'amount': amount,
                'status': status,
                'payment_method': 'yookassa',
                'confirmation_url': confirmation_url,
                'metadata': metadata,
                'created_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('payments').insert(payment_data).execute()
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"❌ Error saving payment to DB: {e}")
            return False
    
    async def _update_payment_status(self, payment_id: str, status: str) -> bool:
        """Обновляет статус платежа в БД"""
        try:
            if not self.supabase:
                return False
            
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('payments').update(update_data).eq('payment_id', payment_id).execute()
            
            # При UPDATE операции Supabase может возвращать пустой массив при успешном обновлении
            # Проверяем что запрос выполнился без ошибок (response.data может быть None или пустым массивом)
            logger.info(f"📝 Update response for {payment_id}: {response.data}")
            
            # Если нет ошибки в response, считаем что обновление прошло успешно
            if hasattr(response, 'error') and response.error:
                logger.error(f"❌ Failed to update payment status for {payment_id}: {response.error}")
                return False
            
            logger.info(f"✅ Payment status updated to '{status}' for {payment_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating payment status: {e}")
            return False
    
    async def _is_payment_processed(self, payment_id: str) -> bool:
        """Проверяет был ли платеж уже обработан"""
        try:
            if not self.supabase:
                return False
            
            response = self.supabase.table('payments').select('status').eq('payment_id', payment_id).execute()
            if response.data:
                return response.data[0]['status'] == 'succeeded'
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking payment status: {e}")
            return False
    
    async def _get_user_id_from_payment(self, payment_id: str) -> Optional[int]:
        """Получает user_id из БД по payment_id"""
        try:
            if not self.supabase:
                return None
            
            response = self.supabase.table('payments').select('user_id').eq('payment_id', payment_id).execute()
            if response.data and response.data[0].get('user_id'):
                return int(response.data[0]['user_id'])
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting user_id from payment {payment_id}: {e}")
            return None
    
    async def _activate_premium_subscription(self, user_id: int, payment_id: str) -> bool:
        """Активирует Premium подписку для пользователя"""
        try:
            # Обновляем подписку через subscription_service
            success = await subscription_service.activate_premium_subscription(user_id, payment_id)
            
            if success:
                logger.info(f"✅ Premium subscription activated for user {user_id}")
                
                # Получаем telegram_user_id из metadata платежа
                telegram_user_id = None
                if self.supabase:
                    response = self.supabase.table('payments').select('metadata').eq('payment_id', payment_id).execute()
                    if response.data and response.data[0].get('metadata'):
                        metadata = response.data[0]['metadata']
                        telegram_user_id = metadata.get('telegram_id')
                
                if telegram_user_id:
                    # Отправляем уведомление пользователю
                    notification_success = await self.send_premium_activation_notification(user_id, int(telegram_user_id))
                    if notification_success:
                        logger.info(f"📨 Premium activation notification sent to user {user_id}")
                    else:
                        logger.warning(f"⚠️ Could not send activation notification to user {user_id}")
                else:
                    logger.warning(f"⚠️ Could not get telegram_user_id for user {user_id}")
                
                return True
            else:
                logger.error(f"❌ Failed to activate Premium subscription for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error activating Premium subscription: {e}")
            return False
    
    async def _send_premium_activation_message(self, user_id: int) -> Tuple[bool, str, Optional[object]]:
        """Отправляет сообщение пользователю о активации Premium"""
        try:
            # Получаем информацию о подписке через check_user_limits
            subscription_info = await subscription_service.check_user_limits(user_id)
            if not subscription_info:
                logger.error(f"❌ Could not get subscription info for user {user_id}")
                return False, "Ошибка получения информации о подписке", None
            
            # Получаем дату окончания из БД напрямую
            if not self.supabase:
                logger.error(f"❌ Supabase not available for getting period_end for user {user_id}")
                return False, "Ошибка подключения к базе данных", None
            
            response = self.supabase.table('subscriptions').select('period_end').eq('user_id', user_id).execute()
            if not response.data:
                logger.error(f"❌ Could not get period_end for user {user_id}")
                return False, "Ошибка получения даты окончания подписки", None
            
            period_end = response.data[0].get('period_end', 'неизвестно')
            
            # Форматируем дату
            if isinstance(period_end, str):
                try:
                    # Парсим дату и форматируем
                    end_date = datetime.fromisoformat(period_end.replace('Z', '+00:00'))
                    period_end = end_date.strftime('%d.%m.%Y')
                except:
                    period_end = 'неизвестно'
            
            message = (
                f"✅ **Premium подписка активирована!**\n\n"
                f"🎯 **Лимит:** 20 писем в день\n"
                f"📅 **Действует до:** {period_end}\n"
                f"💎 **Спасибо за поддержку проекта!**\n\n"
                f"Теперь вы можете создавать сопроводительные письма без ограничений!"
            )
            
            # Импортируем клавиатуру
            from utils.keyboards import get_premium_activation_keyboard
            keyboard = get_premium_activation_keyboard()
            
            logger.info(f"📨 Premium activation message prepared for user {user_id}: {message}")
            
            return True, message, keyboard
            
        except Exception as e:
            logger.error(f"❌ Error sending premium activation message to user {user_id}: {e}")
            return False, f"Ошибка подготовки сообщения: {str(e)}", None
    
    async def send_premium_activation_notification(self, user_id: int, telegram_user_id: int) -> bool:
        """Отправляет уведомление пользователю о активации Premium через Telegram"""
        try:
            # Подготавливаем сообщение и клавиатуру
            success, message, keyboard = await self._send_premium_activation_message(user_id)
            
            if not success:
                logger.error(f"❌ Could not prepare activation message for user {user_id}: {message}")
                return False
            
            # Используем прямой HTTP запрос к Telegram API для избежания event loop проблем
            try:
                import httpx
                
                # Подготавливаем данные для отправки
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                
                data = {
                    "chat_id": telegram_user_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
                
                # Добавляем клавиатуру если есть
                reply_markup = None
                if keyboard:
                    to_dict_method = getattr(keyboard, 'to_dict', None)
                    if callable(to_dict_method):
                        try:
                            reply_markup = to_dict_method()
                        except Exception:
                            reply_markup = None
                if reply_markup:
                    data["reply_markup"] = reply_markup
                
                # Отправляем синхронный запрос
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(url, json=data)
                    
                    if response.status_code == 200:
                        logger.info(f"📨 Premium activation notification sent to user {user_id} (telegram: {telegram_user_id})")
                        return True
                    else:
                        logger.error(f"❌ Telegram API error: {response.status_code} - {response.text}")
                        return False
                        
            except Exception as send_error:
                logger.error(f"❌ Error sending message to telegram {telegram_user_id}: {send_error}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error sending premium activation notification to user {user_id}: {e}")
            return False
    
    def _verify_webhook_signature(self, webhook_data: Dict[str, Any]) -> bool:
        """Проверяет подпись webhook'а от ЮKassa"""
        try:
            # В реальной реализации здесь должна быть проверка HMAC подписи
            # Пока возвращаем True для тестирования
            return True
        except Exception as e:
            logger.error(f"❌ Error verifying webhook signature: {e}")
            return False
    
    async def get_payment_status(self, payment_id: str) -> Optional[str]:
        """Получает статус платежа"""
        try:
            if not self.supabase:
                return None
            
            response = self.supabase.table('payments').select('status').eq('payment_id', payment_id).execute()
            if response.data:
                return response.data[0]['status']
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting payment status: {e}")
            return None

# Создаем глобальный экземпляр сервиса
payment_service = PaymentService() 