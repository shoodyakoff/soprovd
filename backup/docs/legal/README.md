# 📋 Юридические документы

Папка содержит документы для соответствия российскому законодательству.

## 📑 Документы

- `privacy_policy.md` - Политика конфиденциальности (ФЗ-152)
- `terms_of_service.md` - Пользовательское соглашение

## 🎯 Статус

**Релиз v9.0:** В разработке
**Приоритет:** CRITICAL для соответствия ФЗ-152 

## Размещение документов для пользователей

### 🌐 Рекомендуемый вариант: Веб-страницы

**Создать простой статический сайт:**
```
soprovod-bot.ru/
├── privacy/          # Политика конфиденциальности
├── terms/           # Пользовательское соглашение  
└── contact/         # Контакты для обращений
```

**Преимущества:**
- ✅ Профессиональный вид
- ✅ SEO и индексация поисковиками  
- ✅ Легко обновлять документы
- ✅ Можно добавить форму обратной связи
- ✅ Соответствует требованиям ФЗ-152

**Технические решения:**
- **GitHub Pages** (бесплатно)
- **Netlify** (бесплатно) 
- **Vercel** (бесплатно)
- **Railway** (где уже размещен бот)

---

### 📱 Альтернативный вариант: Telegram команды

**Уже реализовано в боте:**
- `/privacy` - показ политики конфиденциальности
- `/terms` - показ пользовательского соглашения

**Ограничения:**
- ❌ Telegram лимит 4096 символов на сообщение
- ❌ Неудобно для длинных документов
- ❌ Нет постоянных ссылок для внешних ресурсов

---

### 🔗 Гибридный подход (ЛУЧШИЙ)

**Комбинация веб + Telegram:**

1. **Основные документы** → веб-страницы:
   - `https://soprovod-bot.ru/privacy`
   - `https://soprovod-bot.ru/terms`

2. **Быстрый доступ** → Telegram команды:
   - `/privacy` → краткая версия + ссылка на полную
   - `/terms` → краткая версия + ссылка на полную

3. **В согласии пользователя** → ссылки на веб:
   ```
   📋 Для продолжения необходимо согласие:
   
   📖 Политика конфиденциальности: https://soprovod-bot.ru/privacy
   📋 Пользовательское соглашение: https://soprovod-bot.ru/terms
   
   ✅ Согласен с условиями и продолжить
   ❌ Отказаться
   ```

---

## 🚀 План реализации веб-страниц

### Шаг 1: Создать статический сайт
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Политика конфиденциальности - AI Сопроводительные письма</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system,BlinkMacSystemFont,sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1, h2, h3 { color: #2c3e50; }
        .container { line-height: 1.6; }
        .back-btn { background: #0088cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Содержимое privacy_policy.md в HTML -->
        <a href="https://t.me/your_bot_name" class="back-btn">🤖 Вернуться к боту</a>
    </div>
</body>
</html>
```

### Шаг 2: Автоматическая конвертация MD → HTML
```python
# Скрипт для конвертации документов
import markdown
import os

def convert_md_to_html(md_file, template_file, output_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    html_content = markdown.markdown(md_content)
    
    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()
    
    final_html = template.replace('{{CONTENT}}', html_content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)

# Конвертация
convert_md_to_html('privacy_policy.md', 'template.html', 'privacy.html')
convert_md_to_html('terms_of_service.md', 'template.html', 'terms.html')
```

### Шаг 3: Деплой на GitHub Pages
```yaml
# .github/workflows/deploy.yml
name: Deploy Legal Docs
on:
  push:
    branches: [ main ]
    paths: [ 'docs/legal/**' ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Convert MD to HTML
        run: python convert_docs.py
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
```

---

## 📋 Следующие шаги

1. **Выберите вариант размещения:**
   - Веб-страницы (рекомендуется)
   - Только Telegram команды  
   - Гибридный подход

2. **Если веб-страницы:**
   - Зарегистрируйте домен (например, soprovod-bot.ru)
   - Создайте статический сайт
   - Настройте автоматическое обновление из GitHub

3. **Обновите ссылки в боте:**
   - В форме согласия
   - В командах `/privacy`, `/terms`
   - В политике конфиденциальности

4. **Протестируйте:**
   - Ссылки работают корректно
   - Документы читаемы на мобильных
   - Быстрая загрузка страниц

**Какой вариант размещения предпочитаете?** Могу помочь с реализацией любого из них. 