# 🚗 SmartAutoParts Project

## Веб-приложение для поиска инструкций и видеоматериалов по автозапчастям

---

# 📌 Описание проекта

**SmartAutoParts Project** — это многофункциональное веб-приложение для поиска инструкций, схем, инструментов и видеоматериалов по оригинальному номеру автозапчасти.

Пользователь вводит OEM-номер детали и получает:

* инструкции по установке;
* технические схемы;
* список необходимых инструментов;
* видеоматериалы с YouTube;
* AI-рекомендации по ремонту;
* анализ изображений запчастей.

Проект объединяет различные источники данных в едином интерфейсе и упрощает самостоятельный ремонт автомобилей.

---

# 🎯 Цель проекта

Создать единую платформу для быстрого получения информации по установке и обслуживанию автозапчастей без необходимости поиска данных по разным сайтам и сервисам.

---

# ⚙️ Основной функционал

## 🔎 Поиск автозапчастей

* Поиск по оригинальному номеру (OEM)
* Поиск инструкций
* Поиск видеоматериалов
* Поиск схем установки
* Поиск инструментов для ремонта

---

## 📘 Инструкции

* Пошаговые инструкции
* Версионность инструкций
* Premium-инструкции
* AI-генерация инструкций
* Изображения и схемы

---

## 🎥 Видео

* Интеграция с YouTube API
* Кеширование видео
* Модерация видеоматериалов
* Привязка видео к запчастям

---

## 🧰 Инструменты

* Список необходимых инструментов
* Категории инструментов
* Связь инструментов с инструкциями

---

## 🤖 AI-функции

* Генерация инструкций через ChatGPT
* Анализ изображений запчастей
* Формирование списка инструментов
* AI-рекомендации

---

## 💬 Внутренний чат

* WebSocket-чат
* Django Channels
* Комнаты для подписчиков
* Обмен сообщениями в реальном времени

---

## 💳 Подписки и платежи

* Подписочные тарифы
* Stripe / ЮKassa
* Автопродление подписок
* Ограничение доступа по ролям

---

# 👥 Роли пользователей

## 👤 Гость

* Просмотр главной страницы
* Поиск по OEM-номеру
* Ограниченный доступ к инструкциям
* Просмотр превью схем

---

## 👨 Зарегистрированный пользователь

* Полный доступ к базовым инструкциям
* Просмотр видео
* Список инструментов
* История поиска
* История ремонтов

---

## ⭐ Подписчик

* Premium-инструкции
* AI-генерация инструкций
* Анализ изображений
* Внутренний чат
* Расширенный список инструментов

---

## 🛠 Администратор

* Управление пользователями
* Управление подписками
* Модерация контента
* Управление видео
* Мониторинг системы
* Аналитика

---

# 🏗 Архитектура проекта

## Backend

* Python
* Django
* Django REST Framework
* Django Channels
* PostgreSQL
* Redis
* Celery

---

## Frontend

* HTML5
* CSS3
* JavaScript
* Django Templates

---

## Внешние сервисы

* YouTube API
* OpenAI API (ChatGPT)
* Stripe
* ЮKassa

---

# 📂 Структура проекта

```bash
SmartAutoParts_project/
│
├── config/
│
├── apps/
│   ├── users/
│   ├── parts/
│   ├── instructions/
│   ├── tools/
│   ├── videos/
│   ├── subscriptions/
│   ├── search/
│   ├── chat/
│   ├── ai/
│   ├── payments/
│   └── analytics/
│
├── templates/
├── static/
├── media/
└── requirements/
```

---

# 🚀 Локальный запуск

Для запуска нужен Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

После запуска откройте `http://127.0.0.1:8000/`.

Главная страница реализована обычными Django HTML-шаблонами. Поисковая
форма отправляет GET-запрос в существующий маршрут `/users/search/`,
поэтому серверная логика поиска, авторизация, кабинет и история
пользователя работают без отдельного React/Next.js-приложения.

---

# 🐳 Запуск проекта в Docker

Docker Compose поднимает четыре части инфраструктуры:

* Django под Gunicorn;
* PostgreSQL 17;
* Redis 7.4 для общего кэша и ограничения частоты запросов;
* постоянные тома PostgreSQL, Redis, загруженных файлов и статики.

Создайте локальный файл переменных окружения:

```powershell
Copy-Item .env.example .env
```

Перед первым запуском замените в `.env` значения
`DJANGO_SECRET_KEY` и `POSTGRES_PASSWORD`. При использовании AI добавьте
`OPENAI_API_KEY`.

Соберите и запустите проект:

```powershell
docker compose up --build -d
docker compose ps
docker compose logs -f web
```

Сайт будет доступен по адресу `http://127.0.0.1:8000/`.
Миграции и сборка статики выполняются автоматически при запуске
контейнера `web`.

Создание суперпользователя:

```powershell
docker compose exec web python manage.py createsuperuser
```

Запуск тестов:

```powershell
docker compose exec web python manage.py test
```

Проверка Redis:

```powershell
docker compose exec redis redis-cli ping
```

Остановка контейнеров без удаления данных:

```powershell
docker compose down
```

Полное удаление контейнеров и постоянных данных:

```powershell
docker compose down -v
```

Последняя команда удаляет базу PostgreSQL, кэш Redis, собранную статику
и загруженные в Docker файлы.

Для разработки с автоматической перезагрузкой можно собрать отдельный
образ:

```powershell
docker build -f Dockerfile.dev -t smartautoparts-dev .
```

---

# 📦 Описание приложений

---

## 📦 apps/users

### Возможности

* Кастомная модель пользователя
* Профиль пользователя
* История поиска
* История ремонтов
* Авторизация и регистрация

### Основные модели

* User
* Profile
* SearchHistory
* RepairHistory

---

## 📦 apps/parts

### Возможности

* Хранение информации о запчастях
* Совместимость деталей
* SEO-поля
* OEM-номера

### Основные модели

* Part
* Compatibility
* OEMNumber
* PartImage
* PartCategory
* PartTool

---

## 📦 apps/instructions

### Возможности

* Инструкции по ремонту
* Версионность
* Premium-доступ
* Пошаговые действия

### Основные модели

* Instruction
* InstructionVersion
* InstructionStep
* InstructionImage
* InstructionTool

---

## 📦 apps/tools

### Возможности

* Список инструментов
* Категории инструментов
* Использование в инструкциях

### Основные модели

* Tool
* ToolCategory
* ToolUsage

---

## 📦 apps/videos

### Возможности

* Интеграция с YouTube
* Кеширование
* Модерация

### Основные модели

* Video
* VideoCache
* VideoModeration

---

## 📦 apps/subscriptions

### Возможности

* Подписочные планы
* Проверка доступа
* Middleware ограничений

### Основные модели

* SubscriptionPlan
* UserSubscription
* SubscriptionPayment

---

## 📦 apps/ai

### Возможности

* AI-запросы
* Генерация инструкций
* Анализ изображений

### Основные модели

* AIRequest
* AIImageAnalysis
* AIGeneratedInstruction

---

## 📦 apps/chat

### Возможности

* WebSocket-чат
* Комнаты
* Сообщения

### Основные модели

* ChatRoom
* ChatParticipant
* ChatMessage

---

## 📦 apps/payments

### Возможности

* Stripe
* ЮKassa
* Webhooks
* Автопродление

---

## 📦 apps/search

### Возможности

* Поиск по OEM
* Кеширование
* Логирование запросов

---

## 📦 apps/analytics

### Возможности

* Аналитика поиска
* Популярные запчасти
* Активность пользователей

### Основные модели

* SearchLog
* UserActivity
* PopularPart

---

# 🗄 Архитектура базы данных

## Основные модули БД

```text
Users
 ├── Profiles
 ├── SearchHistory
 └── RepairHistory

Parts
 ├── Compatibility
 ├── PartImage
 ├── PartCategory
 ├── OEMNumber
 └── PartTool

Instructions
 ├── InstructionVersion
 ├── InstructionStep
 ├── InstructionImage
 └── InstructionTool

Videos
 ├── VideoCache
 └── VideoModeration

Tools
 ├── ToolCategory
 └── ToolUsage

Subscriptions
 ├── SubscriptionPlan
 ├── UserSubscription
 └── SubscriptionPayment

AI
 ├── AIRequest
 ├── AIImageAnalysis
 └── AIGeneratedInstruction

Chat
 ├── ChatRoom
 ├── ChatParticipant
 └── ChatMessage

Analytics
 ├── SearchLog
 ├── UserActivity
 └── PopularPart
```

---

# 🔐 Система подписок

## Free

* Ограниченные инструкции
* Ограниченный просмотр видео
* Базовый поиск

---

## Premium

* Полные инструкции
* AI-функции
* Чат
* Расширенные инструменты
* Анализ изображений

---

# 🔄 Поток работы системы

1. Пользователь вводит OEM-номер
2. Система ищет запчасть в базе
3. Загружаются инструкции
4. Выполняется поиск видео через YouTube API
5. Загружается список инструментов
6. При наличии Premium:

   * AI генерирует инструкцию
   * Выполняется анализ изображения
7. Результат отображается пользователю

---

# 🚀 Перспективы развития

* Поддержка VIN-поиска
* Подбор аналогов
* Интеграция с каталогами автозапчастей
* Мобильное приложение
* Микросервисная архитектура
* Масштабирование под высокую нагрузку
* ML-рекомендации
* Система рейтингов и комментариев

---

# ⚠ Ограничения проекта

* Зависимость от YouTube API
* Ограничения OpenAI API
* Возможные ошибки AI
* Не гарантируется полная совместимость деталей
* Ответственность за ремонт лежит на пользователе

---



# 🧪 Технологический стек

| Технология | Назначение        |
| ---------- | ----------------- |
| Python     | Backend           |
| Django     | Web Framework     |
| DRF        | REST API          |
| PostgreSQL | База данных       |
| Redis      | Кеширование       |
| Celery     | Фоновые задачи    |
| Channels   | WebSocket         |
| Docker     | Контейнеризация   |
| Nginx      | Reverse Proxy     |
| Gunicorn   | Production Server |

---

# 📈 Масштабирование

Проект изначально проектируется с учетом дальнейшего перехода:

* на микросервисную архитектуру;
* горизонтальное масштабирование;
* выделенные AI-сервисы;
* CDN для медиа;
* очередь задач Celery + Redis;
* Kubernetes/Docker инфраструктуру.

---

# 📄 Лицензия

MIT License

---

# 👨‍💻 Автор

SmartAutoParts Project Team
