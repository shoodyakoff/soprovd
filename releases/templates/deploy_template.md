# 🚀 Deploy Instructions - Release vX.X

> **Пошаговая инструкция для развертывания релиза vX.X**

## 📋 Pre-deploy Checklist

### ✅ **Проверки перед деплоем:**
- [ ] Все задачи релиза выполнены
- [ ] Код-ревью завершено
- [ ] Тесты пройдены (unit + integration)
- [ ] Миграции протестированы на staging
- [ ] Backup базы данных создан
- [ ] Rollback план подготовлен

### 📊 **Метрики до деплоя:**
- Uptime: XX%
- Response time: XX ms
- Error rate: XX%
- Active users: XXXX

## 🔄 Database Migrations

### **1. Создание backup**
```bash
# Создать backup БД
pg_dump $DATABASE_URL > backup_pre_vX.X_$(date +%Y%m%d_%H%M).sql

# Проверить размер backup
ls -lh backup_pre_vX.X_*.sql
```

### **2. Применение миграций**
```bash
# Применить миграции в порядке:
psql $DATABASE_URL -f releases/vX_feature_name/migrations/vX.1_migration.sql
psql $DATABASE_URL -f releases/vX_feature_name/migrations/vX.2_migration.sql

# Проверить результат
psql $DATABASE_URL -c "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 5;"
```

### **3. Проверка данных**
```bash
# Проверить целостность критических таблиц
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM subscriptions;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM letter_sessions;"
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
# Обновить переменные окружения в Railway если нужно
railway variables set FEATURE_FLAG_X=true
railway variables set NEW_CONFIG_VALUE=value

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

# Проверить основные endpoints
curl -X POST https://your-app.railway.app/webhook \
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

### **3. Performance Testing**
```bash
# Проверить время ответа
time curl -s https://your-app.railway.app/health

# Нагрузочное тестирование (если нужно)
# ab -n 100 -c 10 https://your-app.railway.app/health
```

## 📊 Post-deploy Metrics

### **Целевые метрики:**
- Uptime: 99.9%+
- Response time: < 500ms
- Error rate: < 0.1%
- Database connections: < 80% pool

### **Мониторинг в течение 24 часов:**
- [ ] Нет критических ошибок в логах
- [ ] Метрики в пределах нормы
- [ ] Пользователи не жалуются
- [ ] Все новые функции работают

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
psql $DATABASE_URL < backup_pre_vX.X_YYYYMMDD_HHMM.sql

# Или ручной rollback миграций
psql $DATABASE_URL -f rollback_vX.X.sql
```

#### **3. Проверка после отката**
```bash
# Проверить что приложение работает
curl https://your-app.railway.app/health

# Проверить основные функции
# Уведомить команду об откате
```

## 📞 Emergency Contacts

- **Lead Developer:** @username (Telegram: @handle)
- **DevOps:** @username (Phone: +X-XXX-XXX-XXXX)
- **Product Owner:** @username
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

---

**Deploy Date:** YYYY-MM-DD HH:MM UTC  
**Deploy Author:** @username  
**Duration:** X minutes  
**Status:** ✅ Success / ❌ Failed / 🔄 Rolled back 