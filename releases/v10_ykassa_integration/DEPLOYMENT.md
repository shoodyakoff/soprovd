# 🚀 Deploy Instructions - Release v10.0

> **Пошаговая инструкция для развертывания релиза v10.0 с интеграцией ЮKassa**

## 📋 Pre-deploy Checklist

### ✅ **Проверки перед деплоем:**
- [x] Все задачи релиза выполнены
- [x] Код-ревью завершено
- [x] Тесты пройдены (unit + integration)
- [x] Миграции протестированы на staging
- [x] Backup базы данных создан
- [x] Rollback план подготовлен

### 📊 **Метрики до деплоя:**
- Uptime: 99.9%
- Response time: 500ms
- Error rate: 0.1%
- Active users: 100+

## 🔄 Database Migrations

### **1. Создание backup**
```bash
# Создать backup БД
pg_dump $DATABASE_URL > backup_pre_v10.0_$(date +%Y%m%d_%H%M).sql

# Проверить размер backup
ls -lh backup_pre_v10.0_*.sql
```

### **2. Применение миграций**
```bash
# Применить миграцию ЮKassa
psql $DATABASE_URL -f releases/v10_ykassa_integration/migrations/v10.1_add_yookassa_payments.sql

# Применить миграцию исправления constraint
psql $DATABASE_URL -f releases/v10_ykassa_integration/migrations/v10.1.1_fix_payment_constraints.sql

# Проверить результат
psql $DATABASE_URL -c "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 5;"
```

### **3. Проверка данных**
```bash
# Проверить целостность критических таблиц
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM subscriptions;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM payments;"

# Проверить новые поля
psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'payments' AND column_name IN ('payment_method', 'confirmation_url', 'metadata');"
```

## 🚀 Application Deployment

### **Railway Deployment:**

#### **1. Pre-deploy steps**
```bash
# Убедиться что на main ветке
git checkout main
git pull origin main

# Проверить что все изменения закоммичены
git status

# Убедиться что Railway CLI настроен
railway login
railway environment production
```

#### **2. Environment Variables**
```bash
# Добавить переменные ЮKassa в Railway
railway variables set YOOKASSA_SHOP_ID=ваш_shop_id
railway variables set YOOKASSA_SECRET_KEY=ваш_secret_key
railway variables set YOOKASSA_ENABLED=true
railway variables set WEBHOOK_HOST=0.0.0.0
railway variables set WEBHOOK_PORT=8000
railway variables set WEBHOOK_PATH=/webhook/yookassa

# Проверить переменные
railway variables
```

#### **3. Deploy**
```bash
# Деплой происходит автоматически при push в main
git push origin main

# Или форсированный деплой
railway deploy

# Мониторить логи
railway logs --follow
```

#### **4. Post-deploy проверки**
```bash
# Проверить что приложение запустилось
curl -f https://your-app.railway.app/health

# Проверить webhook endpoint
curl -X GET https://your-app.railway.app/webhook/health

# Проверить основные endpoints
curl -X POST https://your-app.railway.app/webhook/yookassa \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

## 🔍 Monitoring & Verification

### **1. Health Checks**
```bash
# Проверить статус приложения
railway status

# Проверить метрики
railway metrics

# Проверить логи на ошибки
railway logs | grep -i error
```

### **2. Functional Testing**
- [ ] Telegram бот отвечает на `/start`
- [ ] Генерация письма работает
- [ ] Система подписок функционирует
- [ ] Premium функции доступны
- [ ] Rate limiting работает
- [ ] ЮKassa интеграция работает

### **3. Payment Testing**
```bash
# Тест создания платежа
# В боте: Premium → "Получить Premium" → должна появиться ссылка на оплату

# Тест webhook
curl -X POST https://your-app.railway.app/webhook/yookassa \
  -H "Content-Type: application/json" \
  -d '{"event":"payment.succeeded","object":{"id":"test_payment","status":"succeeded"}}'

# Тест команды /subscription
# В боте: /subscription → должна показать статус подписки
```

## 📊 Post-deploy Metrics

### **Целевые метрики:**
- Uptime: 99.9%+
- Response time: < 500ms
- Error rate: < 0.1%
- Database connections: < 80% pool
- Payment success rate: > 95%

### **Мониторинг в течение 24 часов:**
- [ ] Нет критических ошибок в логах
- [ ] Метрики в пределах нормы
- [ ] Пользователи не жалуются
- [ ] Все новые функции работают
- [ ] Webhook'и обрабатываются корректно

## 🚨 Rollback Plan

### **Если что-то пошло не так:**

#### **1. Быстрый откат кода**
```bash
# Откат к предыдущему коммиту
git revert HEAD --no-edit
git push origin main

# Railway автоматически задеплоит предыдущую версию
```

#### **2. Откат миграций БД**
```bash
# Восстановить из backup
psql $DATABASE_URL < backup_pre_v10.0_YYYYMMDD_HHMM.sql

# Или ручной rollback миграций
psql $DATABASE_URL -f rollback_v10.0.sql
```

#### **3. Проверка после отката**
```bash
# Проверить что приложение работает
curl https://your-app.railway.app/health

# Проверить основные функции
# Уведомить команду об откате
```

## 📞 Emergency Contacts

- **Lead Developer:** @shoodyakoff (Telegram: @shoodyakoff)
- **DevOps:** @shoodyakoff (Telegram: @shoodyakoff)
- **Product Owner:** @shoodyakoff
- **Railway Support:** support@railway.app

## 📝 Post-Deploy Notes

### **Что делать после успешного деплоя:**
1. Обновить CHANGELOG.md
2. Создать Release Notes
3. Уведомить команду о завершении
4. Мониторить метрики 24 часа
5. Перейти к следующему релизу

### **Lessons Learned:**
- Что прошло хорошо
- Что можно улучшить в следующий раз
- Время выполнения каждого этапа

## 🟢 Post-deploy проверки (v10.1.1)
- [x] Проверить, что при повторной оплате Premium подписка продлевается (дата окончания увеличивается на 30 дней)
- [x] Проверить, что при оплате после истечения подписки дата окончания = сегодня + 30 дней
- [x] Проверить, что пользователь получает уведомление о продлении
- [x] Проверить, что лимиты сбрасываются при продлении
- [x] Проверить, что исправлены ошибки event loop, constraint, UX, тестового endpoint, отправки уведомлений
- [x] Подробнее: см. TZ_NUANCES_REPORT_v3.md
- [x] После успешной оплаты экран оплаты исчезает
- [x] На экране активации Premium только одна кнопка "✍️ Написать сопроводительное"
- [x] Нет дублирующихся letter_session
- [x] Логика продления подписки работает корректно
- [x] Цена в ссылке на оплату — 1₽ (UI и тексты без изменений)
- [x] Команда `/subscription` работает корректно и показывает актуальный статус подписки

---

**Deploy Date:** 30 июня 2025  
**Deploy Author:** @shoodyakoff  
**Duration:** 2 часа  
**Status:** ✅ Success 