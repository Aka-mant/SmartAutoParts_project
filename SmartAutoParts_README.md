# SmartAutoParts

SmartAutoParts — Django-приложение для поиска автомобильных запчастей по
OEM-номеру, просмотра карточек деталей, получения проверенных ремонтных
инструкций и инструментов, пошагового сопровождения ремонта, общения в
сообществе и использования функций OpenAI.

Этот файл является единой документацией проекта. В нём описаны установка,
настройка, архитектура, роли, тарифы, пользовательские сценарии, AI,
модерация, API, Docker, Redis, работа с файлами и обслуживание проекта.

## 1. Технологии

- Python 3.14 в Docker-образе;
- Django 6.0;
- Django REST Framework;
- Simple JWT;
- django-filter;
- drf-yasg и Swagger;
- OpenAI Responses API;
- SQLite для локальной разработки;
- PostgreSQL 17 для Docker и развёртывания;
- Redis 7.4 для общего кэша и ограничения частоты запросов;
- Gunicorn;
- WhiteNoise;
- HTML, CSS, JavaScript и Django Templates;
- Docker и Docker Compose.

Проект не требует отдельного SPA-приложения. HTML-интерфейс формируется
Django-шаблонами, а API доступен параллельно с обычными страницами.

## 2. Возможности проекта

### 2.1. Поиск запчастей

Поиск доступен по основному OEM-номеру, дополнительным OEM-номерам,
названию и связанным данным детали. Результаты показывают:

- название и производителя;
- OEM-номер;
- категорию;
- изображение или безопасный placeholder;
- ссылку на карточку детали при наличии необходимого доступа.

Поисковая история сохраняет запрос, найденный результат и ссылку на
повторный поиск. Неавторизованный пользователь может выполнять поиск, но
не получает доступ к закрытой карточке детали.

### 2.2. Карточка детали

Карточка объединяет:

- основное и дополнительные изображения;
- характеристики детали;
- OEM-номера;
- совместимость с автомобилями;
- приобретённые пользователем инструкции;
- приобретённые рекомендации инструментов;
- запуск AI-запросов;
- переход к пошаговому ремонту.

Если путь к изображению записан в базе, но физический файл отсутствует,
интерфейс показывает placeholder и не формирует заведомо битый `<img>`.

### 2.3. Инструкции

Инструкция связана с деталью и может содержать:

- заголовок и описание;
- сложность;
- ориентировочное время;
- полный текст;
- упорядоченные шаги;
- изображения;
- инструменты и их количество;
- состояние публикации;
- дату последней AI-генерации;
- номер версии.

Для истории изменений используется `InstructionVersion`. При обновлении
проверенной инструкции прежнее содержимое сохраняется, а номер версии
увеличивается.

### 2.4. Пошаговый ремонт

Пользователь может начать ремонт по опубликованной инструкции. Состояние
сохраняется в `RepairHistory`:

- текущий шаг;
- завершённость;
- пользовательские заметки;
- дата начала и обновления.

На странице ремонта доступны кнопки:

- «Предыдущий шаг»;
- «Следующий шаг»;
- «Завершить ремонт».

Переход ограничен первым и последним шагами. Обычный пользователь работает
только со своей историей, а суперпользователь имеет административный доступ.

### 2.5. Инструменты

Каталог состоит из категорий, инструментов и связей `PartTool`. Для связи
можно хранить назначение, необходимость и количество. Инструменты также
могут быть связаны непосредственно с инструкциями через `InstructionTool`.

AI-рекомендация не изменяет каталог автоматически. Сначала она сохраняется
как отдельный модерируемый объект, затем проверяется специалистом.

### 2.6. AI-чат

AI-чат:

- принимает сообщения длиной до 500 символов;
- выполняет локальную и провайдерскую модерацию;
- при наличии связанной детали добавляет проектный контекст;
- умеет искать связанную деталь в локальной базе;
- сохраняет запрос и ответ;
- учитывает тарифные лимиты;
- выводит причину блокировки внутри чата;
- защищён ограничением частоты запросов.

Поле поиска связанной детали работает по существующим данным проекта.
Если деталь не найдена, запрос может быть отправлен без связи, но номера
из текста сообщения остаются частью пользовательского запроса.

### 2.7. Генерация ремонтных инструкций

Сервис формирует структурированную пошаговую инструкцию на основании:

- детали и OEM-номеров;
- совместимости;
- характеристик;
- сохранённых опубликованных инструкций;
- имеющихся инструментов;
- профиля автомобиля пользователя;
- цели запроса;
- правил безопасности.

Новая инструкция сохраняется в `AIRequest` и
`AIGeneratedInstruction` со статусом ожидания модерации. Она не становится
публичной автоматически.

До истечения годового TTL сервис может использовать актуальную сохранённую
редакцию. После TTL создаётся новая AI-версия. Проверенная старая версия
сохраняется в `InstructionVersion`, а обновление снова отправляется на
модерацию.

### 2.8. Анализ фотографии

Пользователь может загрузить фотографию детали или инструмента. Перед
отправкой требуется подтверждение, что изображение действительно содержит
автомобильную деталь или инструмент.

Алгоритм:

1. Проверяется авторизация и тариф.
2. Проверяется размер файла — не более 5 МБ.
3. Проверяется формат и геометрия изображения.
4. Изображение сжимается для хранения.
5. Выполняется автоматическая мультимодальная модерация.
6. Изображения без детали или инструмента отклоняются.
7. OpenAI возвращает структурированный результат.
8. Результат сопоставляется с каталогом проекта.
9. При достаточной уверенности возвращается предполагаемый OEM-номер.
10. Анализ сохраняется в `AIImageAnalysis`.

Поддерживаются JPEG, PNG, WEBP и статический GIF. В админке JSON результата
отображается с отступами.

### 2.9. Чат автомобилистов

Зарегистрированным пользователям доступен чат сообщества:

- комнаты;
- участники;
- сообщения;
- автоматическая модерация;
- ограничение сообщения до 500 символов;
- защита от частых и пакетных запросов;
- причины отклонения непосредственно в интерфейсе чата.

Текущая реализация использует Django HTTP/API, модели базы и периодическое
обновление интерфейса. Redis обеспечивает общий кэш rate limit между
процессами Gunicorn.

### 2.10. Тарифы и приобретённый контент

Тариф задаёт:

- общую квоту AI;
- лимит чата;
- лимит инструкций;
- лимит анализа изображений;
- доступ к AI-чату;
- доступ к генерации инструкций;
- доступ к анализу изображений;
- стоимость и продолжительность.

Первичная выдача инструкции, инструмента или ответа считается приобретением
контента и фиксируется в `AIContentPurchase`. Запись сохраняется при смене
или продлении тарифа. Пользователь видит приобретённый контент, а не все
данные, существующие в общей базе.

Суперпользователь имеет безлимитный доступ и видит все данные. Модератор
проверяет AI-материалы, но не использует AI как обычный платный пользователь.

Страница оплаты является демонстрационной: она позволяет выбрать способ
оплаты и применяет тариф без подключения реального платёжного провайдера.

### 2.11. Пользовательское соглашение

Обычный пользователь принимает актуальную версию соглашения при первом
использовании функций сервиса. Факт принятия фиксируется в
`UserAgreementAcceptance` вместе с версией и служебными данными.

Администратор и суперпользователь освобождены от обязательного принятия.

### 2.12. Аналитика

Приложение аналитики хранит:

- действия пользователей;
- поисковые события;
- популярность деталей.

Функционал аналитики предназначен для суперпользователя.

## 3. Роли и доступ

### Пользователь

- регистрация и вход;
- поиск по базе;
- профиль и история;
- чат сообщества;
- платные функции только при действующем тарифе;
- просмотр только приобретённого AI-контента.

### Премиум-пользователь

Это пользователь с действующим тарифом. Доступ определяется не только
строковым значением роли, но и активной `UserSubscription` с корректными
датами начала и окончания.

### Модератор

- доступ в административный раздел модерации;
- одобрение и отклонение AI-инструкций;
- одобрение и отклонение рекомендаций инструментов;
- просмотр материалов, необходимых для проверки;
- отсутствие обычного безлимитного AI-доступа.

### Администратор

- управление сущностями проекта;
- управление пользователями и тарифами;
- работа с каталогом;
- модерация в рамках выданных прав.

### Суперпользователь

- полный доступ ко всем данным;
- безлимитные AI-запросы;
- отсутствие фильтра приобретённого контента;
- отсутствие подтверждений списания;
- доступ к аналитике и Django Admin.

## 4. Архитектура

```text
SmartAutoParts_project/
├── apps/
│   ├── AI/
│   ├── analytics/
│   ├── chat/
│   ├── instructions/
│   ├── parts/
│   ├── subscriptions/
│   └── tools/
├── config/
├── docker/
├── fixtures/
├── media/
├── requirements/
├── static/
├── templates/
├── users/
├── .env.example
├── Dockerfile
├── Dockerfile.dev
├── docker-compose.yml
├── manage.py
└── SmartAutoParts_README.md
```

### `users`

Модели:

- `User` — учётная запись, роль, контакты и аватар;
- `Profile` — страна, город, язык и автомобиль;
- `UserAgreementAcceptance` — принятие соглашения;
- `SearchHistory` — поисковые запросы;
- `RepairHistory` — состояние пошагового ремонта.

### `apps.parts`

- `PartCategory`;
- `Part`;
- `OEMNumber`;
- `Compatibility`;
- `PartImage`.

### `apps.instructions`

- `Instruction`;
- `InstructionVersion`;
- `InstructionStep`;
- `InstructionImage`;
- `InstructionTool`.

### `apps.tools`

- `ToolCategory`;
- `Tool`;
- `PartTool`.

### `apps.subscriptions`

- `SubscriptionPlan`;
- `UserSubscription`;
- `SubscriptionPayment`.

### `apps.AI`

- `AIRequest`;
- `AIGeneratedInstruction`;
- `AIToolRecommendation`;
- `AIContentPurchase`;
- `AIImageAnalysis`.

Основная бизнес-логика находится в `apps/AI/services.py`, а шаблоны
системных промтов — в `apps/AI/prompts.py`.

### `apps.chat`

- `ChatRoom`;
- `ChatParticipant`;
- `ChatMessage`.

### `apps.analytics`

- `UserActivity`;
- `SearchLog`;
- `PopularPart`.

## 5. Локальная установка в Windows

### 5.1. Требования

Установите:

- Python 3.14;
- Git;
- при необходимости Docker Desktop.

### 5.2. Виртуальное окружение

```bash

py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Если PowerShell блокирует активацию:

```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 5.3. Переменные окружения

Создайте `.env`:

```bash
Copy-Item .env.example .env
```

Минимальная локальная конфигурация:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
DB_ENGINE=sqlite
SERVE_MEDIA_FILES=1
OPENAI_API_KEY=
OPENAI_AI_MODEL=gpt-5.6-sol
```

Не добавляйте локально:

```dotenv
MEDIA_ROOT=/app/media
```

Этот путь относится только к контейнеру. Без переопределения локальный
`MEDIA_ROOT` равен `<корень проекта>\media`.

### 5.4. SQLite

```bash
$env:DB_ENGINE = "sqlite"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Файл базы:

```text
db.sqlite3
```

Проверка активной базы:

```bash
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default'])"
```

### 5.5. Тестовые данные

Команда `ccu` создаёт связанный набор данных:

```bash
python manage.py ccu --min-count 20 --max-count 50
```

Не запускайте её повторно на рабочей базе без необходимости: она создаёт
пользователей, детали, инструкции, инструменты, подписки, чаты, AI-запросы
и аналитические записи.

### 5.6. Запуск

```bash
python manage.py runserver
```

Основные адреса:

- сайт: `http://127.0.0.1:8000/`;
- админка: `http://127.0.0.1:8000/admin/`;
- Swagger: `http://127.0.0.1:8000/swagger/`;
- ReDoc: `http://127.0.0.1:8000/redoc/`.

## 6. Docker, PostgreSQL и Redis

### 6.1. Подготовка

Запустите Docker Desktop и дождитесь запуска Linux Engine:

```bash
docker version
docker info
docker context use desktop-linux
```

`docker version` должен показывать секции `Client` и `Server`.

### 6.2. Настройка `.env`

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=0
SERVE_MEDIA_FILES=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

POSTGRES_DB=smartautoparts
POSTGRES_USER=smartautoparts
POSTGRES_PASSWORD=replace-database-password

OPENAI_API_KEY=
OPENAI_AI_MODEL=gpt-5.6-sol
```

### 6.3. Запуск

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f web
```

Compose запускает:

- `web` — Django под Gunicorn;
- `postgres` — PostgreSQL;
- `redis` — Redis.

Контейнер `web` ожидает готовность PostgreSQL, выполняет миграции и
`collectstatic`, затем запускает Gunicorn.

### 6.4. Полезные команды

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec redis redis-cli ping
docker compose logs -f web
docker compose restart web
docker compose down
```

Удаление контейнеров вместе с постоянными данными:

```bash
docker compose down -v
```

Эта команда удаляет базу PostgreSQL и данные Redis.

### 6.5. Файлы media

Compose использует bind mount:

```yaml
- ./media:/app/media
```

Поэтому локальный сервер и Docker работают с одной папкой изображений.
Аватары сохраняются в `media/avatars`, изображения деталей — в
`media/parts/images`, AI-анализы — в `media/ai/image_analysis`.

## 7. Redis

При наличии `REDIS_URL` Django использует:

```text
django.core.cache.backends.redis.RedisCache
```

Docker задаёт:

```dotenv
REDIS_URL=redis://redis:6379/1
```

Без `REDIS_URL` используется локальный `LocMemCache`. Он подходит для
одного процесса разработки, но не обеспечивает общий rate limit между
несколькими процессами.

## 8. OpenAI

### 8.1. Обязательная настройка

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_AI_MODEL=gpt-5.6-sol
OPENAI_MODERATION_MODEL=omni-moderation-latest
```

Ключ хранится только на сервере. Его нельзя добавлять в JavaScript,
шаблоны, Git или публичный Docker-образ.

### 8.2. Настройки генерации

Доступны:

```dotenv
OPENAI_TOOL_REASONING_EFFORT=low
OPENAI_TOOL_MAX_OUTPUT_TOKENS=3000
OPENAI_TOOL_VERBOSITY=medium
AI_INSTRUCTION_CACHE_TTL_DAYS=365
AI_IMAGE_MAX_BYTES=5242880
```

Дополнительные лимиты и параметры определены в `config/settings.py` и
используются сервисным слоем.

### 8.3. Модерация инструкций

Откройте:

```text
/admin/AI/aigeneratedinstruction/
```

- «Одобрить» публикует первую редакцию либо новую версию;
- «Отклонить» требует причину;
- обновление существующего материала сохраняет прежнюю версию.

### 8.4. Модерация инструментов

```text
/admin/AI/aitoolrecommendation/
```

Одобренный ответ становится доступен пользователю в соответствующем блоке
карточки детали. Каталог инструментов автоматически не изменяется.

## 9. Media и статические файлы

### 9.1. Настройки

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Для локального запуска:

```dotenv
SERVE_MEDIA_FILES=1
```

Проверка:

```bash
python manage.py shell -c "from django.conf import settings; print(settings.MEDIA_ROOT); print(settings.SERVE_MEDIA_FILES)"
```

Проверка конкретного файла:

```bash
Test-Path "media\avatars\имя-файла.png"
```

Сборка статики:

```bash
python manage.py collectstatic --noinput
```

`staticfiles` является генерируемой папкой. Изменять файлы внутри неё
вручную не следует; исходный CSS находится в `static/css`.

### 9.2. CSS

`static/css/style.css` импортирует:

- базовые правила;
- navbar и header;
- hero;
- общие секции;
- карточки;
- формы;
- личный кабинет;
- профиль;
- поиск;
- карточку детали;
- инструкции;
- AI;
- чат;
- тарифы;
- адаптивные media-файлы;
- печатные стили.

Порядок импортов важен для каскада.

## 10. Основные HTML-маршруты

| Адрес | Назначение |
|---|---|
| `/` | Главная |
| `/users/register/` | Регистрация |
| `/users/login/` | Вход |
| `/users/dashboard/` | Панель управления |
| `/users/profile/` | Профиль |
| `/users/profile/edit/` | Редактирование профиля |
| `/users/search/` | Поиск деталей |
| `/users/search-history/` | История поиска |
| `/users/repair-history/` | История ремонта |
| `/parts/<slug>/` | Карточка детали |
| `/parts/image-analysis/` | Анализ изображения |
| `/instructions/` | Инструкции |
| `/instructions/<slug>/` | Инструкция |
| `/instructions/repair/<id>/` | Пошаговый ремонт |
| `/subscriptions/` | Тарифы |
| `/ai/chat/` | AI-чат |
| `/chat/` | Чат сообщества |
| `/admin/` | Django Admin |

## 11. API

API сгруппирован по префиксам:

- `/users/api/`;
- `/api/parts/`;
- `/api/instructions/`;
- `/api/tools/`;
- `/api/subscriptions/`;
- `/api/AI/`;
- `/api/chat/`;
- `/api/analytics/`.

JWT:

```text
POST /users/api/token/
POST /users/api/token/refresh/
```

Основные группы ресурсов реализуют list, create, retrieve, update и delete
с разрешениями, соответствующими роли и владению объектом.

Интерактивная документация:

```text
/swagger/
/redoc/
```

## 12. Администрирование

После создания суперпользователя:

```bash
python manage.py createsuperuser
```

Доступно управление:

- пользователями и профилями;
- принятием соглашения;
- деталями, OEM, совместимостью и изображениями;
- инструкциями, шагами, версиями и инструментами;
- тарифами, подписками и платежами;
- чатами;
- AI-запросами и анализами;
- приобретённым AI-контентом;
- модерацией инструкций и инструментов;
- аналитикой.

## 13. Fixtures

В `fixtures` находятся JSON-файлы приложений. Загружать их нужно в порядке
зависимостей:

```bash
python manage.py loaddata fixtures/users.json
python manage.py loaddata fixtures/parts.json
python manage.py loaddata fixtures/tools.json
python manage.py loaddata fixtures/instructions.json
python manage.py loaddata fixtures/subscriptions.json
python manage.py loaddata fixtures/chat.json
python manage.py loaddata fixtures/AI.json
python manage.py loaddata fixtures/analytics.json
```

Если связи в конкретном наборе fixtures отличаются, используйте порядок из
файла `correct_loading_order`.

## 14. Проверка проекта

По отдельной команде разработчика:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
coverage erase
coverage run manage.py test
coverage report
flake8 apps users config docker manage.py
```

`.coveragerc` задаёт минимальное покрытие 98%. В тестах ошибки провайдера AI
намеренно имитируются через mock, поэтому traceback в журнале может быть
частью успешного тестового сценария. Итог определяется строкой `OK`.


## 15. Безопасность и развёртывание

Перед публикацией:

1. Замените `DJANGO_SECRET_KEY`.
2. Установите `DJANGO_DEBUG=0`.
3. Укажите реальные `DJANGO_ALLOWED_HOSTS`.
4. Укажите HTTPS-адреса в `DJANGO_CSRF_TRUSTED_ORIGINS`.
5. Используйте сложный пароль PostgreSQL.
6. Не публикуйте `.env`.
7. Не передавайте `OPENAI_API_KEY` клиенту.
8. Настройте резервное копирование PostgreSQL и `media`.
9. Для высокой нагрузки вынесите media в Nginx или объектное хранилище.
10. Ограничьте внешние порты PostgreSQL и Redis.
11. Используйте HTTPS и reverse proxy.
12. Выполните `python manage.py check --deploy`.

## 16. Резервное копирование

SQLite:

```bash
Copy-Item db.sqlite3 backup\db.sqlite3
```

PostgreSQL в Docker:

```bash
docker compose exec postgres pg_dump -U smartautoparts smartautoparts > backup.sql
```

Media:

```bash
Copy-Item media backup\media -Recurse
```

Восстановление PostgreSQL:

```bash
Get-Content backup.sql | docker compose exec -T postgres psql -U smartautoparts smartautoparts
```

## 17. Рекомендуемый рабочий процесс

1. Активировать `.venv`.
2. Получить изменения Git.
3. Установить обновлённые зависимости.
4. Проверить `.env`.
5. Выполнить миграции.
6. При изменении статики выполнить `collectstatic`.
7. Запустить сервер.
8. Проверить поиск, авторизацию, media и нужные роли.
9. Перед коммитом запустить проверки только по согласованной команде.
10. Не добавлять `.env`, базу, media и генерируемый `staticfiles` в Git.
