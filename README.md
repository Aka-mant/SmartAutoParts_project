# SmartAutoParts

SmartAutoParts — Django-сервис для поиска автомобильных деталей, работы с
OEM-номерами, получения проверенных ремонтных инструкций и рекомендаций
инструментов, пошагового сопровождения ремонта, анализа фотографий и общения
в автомобильном сообществе.

Проект объединяет серверный HTML-интерфейс, REST API, административную
модерацию и интеграцию с OpenAI. Обычные пользователи получают AI-возможности
в пределах активного тарифа, модераторы проверяют созданные материалы, а
суперпользователь имеет полный и безлимитный доступ.

## Содержание

1. [Возможности](#возможности)
2. [Архитектура](#архитектура)
3. [Роли и правила доступа](#роли-и-правила-доступа)
4. [Локальная установка](#локальная-установка)
5. [Запуск в Docker](#запуск-в-docker)
6. [OpenAI и модерация](#openai-и-модерация)
7. [Статические и загружаемые файлы](#статические-и-загружаемые-файлы)
8. [Fixtures](#fixtures)
9. [Маршруты и API](#маршруты-и-api)
10. [Тестирование и качество](#тестирование-и-качество)
11. [Эксплуатация и безопасность](#эксплуатация-и-безопасность)

## Возможности

### Поиск и каталог деталей

- поиск по основному и дополнительным OEM-номерам;
- поиск по названию, части названия, производителю, категории, описанию,
  совместимости и другим атрибутам детали;
- нормализация OEM-номеров перед сравнением;
- сохранение истории запросов и повторный переход к результатам;
- отдельные карточки деталей и инструментов;
- единая адаптивная галерея с полноэкранным просмотром изображений;
- безопасный placeholder, если путь существует в базе, но файла нет.

Неавторизованный посетитель может искать данные в каталоге, но не открывает
закрытую карточку детали. Авторизованному пользователю без действующего тарифа
также недоступны платные карточки и инструкции.

### Инструкции и пошаговый ремонт

Инструкция содержит описание, сложность, расчётное время, последовательность
шагов, фотографии и перечень инструментов. Публикация AI-инструкции происходит
только после проверки модератором.

`RepairHistory` сохраняет текущий шаг и состояние ремонта. Пользователь может:

- перейти к предыдущему или следующему шагу;
- продолжить незавершённый ремонт;
- добавить заметки;
- завершить ремонт.

При обновлении инструкции прежнее содержимое сохраняется в
`InstructionVersion`. Годовой TTL определяет момент повторной AI-генерации;
новая версия снова направляется на модерацию.

### Инструменты

Каталог инструментов включает категории, основные и дополнительные фотографии,
размер, описание и внешнюю ссылку. Связь `PartTool` определяет, какой инструмент
нужен конкретной детали. Связь `InstructionTool` хранит инструменты отдельной
ремонтной инструкции.

AI-рекомендация инструмента сначала сохраняется как модерируемый материал.
После одобрения она отображается в каталожном блоке пользователя и не изменяет
общий каталог автоматически.

### AI-чат

- сообщения длиной до 500 символов;
- поиск связанной детали в локальном каталоге до обращения к OpenAI;
- работа без связи с деталью, если совпадение не найдено;
- извлечение указанных пользователем OEM-номеров из сообщения;
- локальная и провайдерская модерация;
- сохранение запроса, ответа, модели и количества токенов;
- тарифные ограничения и защита от частых запросов;
- отображение причины отклонения непосредственно в чате.

### Анализ изображений

Пользователь загружает JPEG, PNG, WEBP или статический GIF размером не более
5 МБ и подтверждает наличие автомобильной детали или инструмента. Сервис:

1. проверяет авторизацию, роль, соглашение и тариф;
2. валидирует размер и формат;
3. сжимает изображение для хранения;
4. выполняет автоматическую модерацию;
5. отклоняет изображения без детали или инструмента;
6. получает структурированный результат OpenAI;
7. сопоставляет результат с локальным каталогом;
8. при уверенности выше 70% возвращает предполагаемый OEM-номер;
9. сохраняет результат в `AIImageAnalysis`.

### Приобретённый контент и тарифы

Тариф задаёт срок действия и отдельные лимиты для AI-чата, инструкций и анализа
изображений. Первичная выдача инструкции, рекомендации инструмента или ответа
считается приобретением и фиксируется в `AIContentPurchase`, независимо от
того, был материал найден в базе или сгенерирован заново.

При смене или продлении тарифа приобретённый контент остаётся доступным.
Суперпользователь видит все материалы без списаний и подтверждений. Модератор
не получает безлимитный пользовательский AI-доступ.

### Чат сообщества

Всем зарегистрированным пользователям доступны открытые комнаты. Закрытая
комната содержит список участников, управляемый её владельцем. Сообщения
проходят автоматическую модерацию, ограничены 500 символами и защищены общим
rate limit через Django cache/Redis.

### Пользовательское соглашение и аналитика

Факт принятия актуальной версии соглашения сохраняется в
`UserAgreementAcceptance`. Администраторы и суперпользователи освобождены от
обязательного подтверждения. Аналитические страницы и API предназначены только
для суперпользователя.

## Архитектура

```text
SmartAutoParts_project/
├── apps/
│   ├── AI/               # OpenAI, покупки контента и модерация
│   ├── analytics/        # события, поисковые логи и популярность
│   ├── chat/             # комнаты, участники и сообщения
│   ├── instructions/     # инструкции, версии, шаги и изображения
│   ├── parts/            # детали, OEM, совместимость и фотографии
│   ├── subscriptions/    # тарифы, подписки, платежи и лимиты
│   └── tools/            # каталог и связи инструментов с деталями
├── config/               # настройки, корневые URL, WSGI и ASGI
├── docker/               # entrypoint и конфигурация Gunicorn
├── fixtures/             # общий комплект тестовых данных
├── media/                # пользовательские файлы
├── requirements/         # зависимости Python
├── static/               # исходная статика
├── staticfiles/          # результат collectstatic
├── templates/            # Django-шаблоны
├── users/                # пользователи, профиль, история и соглашение
├── Dockerfile
├── Dockerfile.dev
├── docker-compose.yml
├── manage.py
└── README.md
```

### Основные модели

| Приложение | Модели |
|---|---|
| `users` | `User`, `Profile`, `UserAgreementAcceptance`, `SearchHistory`, `RepairHistory` |
| `parts` | `PartCategory`, `Part`, `OEMNumber`, `Compatibility`, `PartImage` |
| `instructions` | `Instruction`, `InstructionVersion`, `InstructionStep`, `InstructionImage`, `InstructionTool` |
| `tools` | `ToolCategory`, `Tool`, `ToolImage`, `PartTool` |
| `subscriptions` | `SubscriptionPlan`, `UserSubscription`, `SubscriptionPayment` |
| `AI` | `AIRequest`, `AIGeneratedInstruction`, `AIToolRecommendation`, `AIImageAnalysis`, `AIContentPurchase` |
| `chat` | `ChatRoom`, `ChatParticipant`, `ChatMessage` |
| `analytics` | `UserActivity`, `SearchLog`, `PopularPart` |

Бизнес-логика OpenAI сосредоточена в `apps/AI/services.py`, а системные
шаблоны запросов — в `apps/AI/prompts.py`. HTTP/API и HTML-представления
приложения объединены в существующих `views.py` и `urls.py`; отдельные файлы с
дублирующим назначением не создаются.

## Роли и правила доступа

| Роль | Основные возможности |
|---|---|
| Гость | Поиск по открытой базе без просмотра закрытой карточки |
| Пользователь | Профиль, история и чат сообщества; AI только с активным тарифом |
| Модератор | Проверка AI-инструкций и инструментов без пользовательских AI-запросов |
| Администратор | Управление разрешёнными сущностями через Django Admin |
| Суперпользователь | Полный доступ, аналитика и безлимитный AI |

Доступ к платным функциям определяется активной `UserSubscription`, сроком её
действия, возможностями плана и остатком соответствующего лимита.

## Локальная установка

### Требования

- Windows 10/11;
- Python 3.14;
- Git;
- Docker Desktop — только для контейнерного запуска.

### 1. Создание окружения

```bash
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install coverage flake8
```

Если PowerShell запрещает активацию:

```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Переменные окружения

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
REDIS_URL=
OPENAI_API_KEY=
OPENAI_AI_MODEL=gpt-5.6-sol
```

Не задавайте локально `MEDIA_ROOT=/app/media`: этот путь относится к Docker.

### 3. База и служебные файлы

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Проверить выбранную базу:

```bash
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default'])"
```
a
### 4. Тестовые данные и запуск

```bash
python manage.py ccu --min-count 20 --max-count 50
python manage.py runserver
```

Команда `ccu` создаёт связанные записи всех приложений. Не запускайте её
повторно на рабочей базе без резервной копии.

Основные адреса:

- сайт — `http://127.0.0.1:8000/`;
- Django Admin — `http://127.0.0.1:8000/admin/`;
- Swagger — `http://127.0.0.1:8000/swagger/`;
- ReDoc — `http://127.0.0.1:8000/redoc/`.

## Запуск в Docker

Убедитесь, что Docker Desktop и Linux Engine запущены:

```bash
docker version
docker info
docker context use desktop-linux
```

Настройте `.env`:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=0
SERVE_MEDIA_FILES=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
POSTGRES_DB=smartautoparts
POSTGRES_USER=smartautoparts
POSTGRES_PASSWORD=replace-database-password
REDIS_URL=redis://redis:6379/1
OPENAI_API_KEY=
OPENAI_AI_MODEL=gpt-5.6-sol
```

Запуск и обслуживание:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f web
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec redis redis-cli ping
docker compose restart web
docker compose down
```

`docker compose down -v` дополнительно удаляет том PostgreSQL и сохранённые
данные. Используйте эту команду только при намеренном полном сбросе.

## OpenAI и модерация

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_AI_MODEL=gpt-5.6-sol
OPENAI_MODERATION_MODEL=omni-moderation-latest
OPENAI_TOOL_REASONING_EFFORT=low
OPENAI_TOOL_MAX_OUTPUT_TOKENS=3000
OPENAI_TOOL_VERBOSITY=medium
AI_INSTRUCTION_CACHE_TTL_DAYS=365
AI_IMAGE_MAX_BYTES=5242880
```

Ключ OpenAI хранится только на сервере. Его нельзя помещать в шаблоны,
JavaScript, fixtures, Git или Docker-образ.

Очереди модерации доступны в Django Admin:

- `/admin/AI/aigeneratedinstruction/` — инструкции;
- `/admin/AI/aitoolrecommendation/` — рекомендации инструментов;
- `/admin/AI/aiimageanalysis/` — результаты анализа изображений.

Одобрение инструкции создаёт или обновляет опубликованный материал. При
обновлении старая редакция сохраняется как версия. Отклонение требует причину.

## Статические и загружаемые файлы

```text
STATIC_URL=/static/
STATIC_ROOT=<project>/staticfiles
MEDIA_URL=/media/
MEDIA_ROOT=<project>/media
```

Исходные CSS и JavaScript изменяются в `static`. Папка `staticfiles` создаётся
командой `collectstatic` и не должна редактироваться вручную:

```bash
python manage.py collectstatic --clear --noinput
```

При `DEBUG=0` локальная раздача media включается только явной настройкой:

```dotenv
SERVE_MEDIA_FILES=1
```

Основные каталоги загрузок:

- `media/avatars` — аватары;
- `media/parts/images` — фотографии деталей;
- `media/tools/images` — фотографии инструментов;
- `media/instructions/images` — изображения инструкций;
- `media/ai/image_analysis` — изображения AI-анализа.

Docker подключает `./media:/app/media`, поэтому файлы не исчезают при
пересоздании контейнера `web`.

## Fixtures

Загрузка общего комплекта выполняется в порядке зависимостей:

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

Обновление общей резервной fixture:

```bash
py -Xutf8 manage.py dumpdata `
  --exclude contenttypes.contenttype `
  --exclude auth.permission `
  --exclude admin.logentry `
  --exclude sessions.session `
  --indent 4 `
  --output fixtures/all_data.json
```

Fixtures могут содержать персональные или служебные данные. Перед публикацией
проверяйте их содержимое и никогда не сохраняйте API-ключи и пароли.

## Маршруты и API

### HTML

| Адрес | Назначение |
|---|---|
| `/` | Главная страница |
| `/users/register/`, `/users/login/` | Регистрация и вход |
| `/users/dashboard/` | Панель управления |
| `/users/profile/` | Профиль |
| `/users/search/` | Поиск деталей |
| `/users/search-history/` | История поиска |
| `/users/repair-history/` | История ремонтов |
| `/parts/<slug>/` | Карточка детали |
| `/parts/image-analysis/` | Анализ фотографии |
| `/instructions/` | Каталог инструкций |
| `/instructions/<slug>/` | Полная инструкция |
| `/subscriptions/` | Тарифы |
| `/ai/chat/` | AI-помощник |
| `/chat/` | Чат сообщества |
| `/admin/` | Администрирование |

### REST API

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

Актуальные операции и схемы доступны в `/swagger/` и `/redoc/`.

## Тестирование и качество

Настройки coverage находятся в `.coveragerc`. Из расчёта исключены миграции,
тестовые модули, WSGI и ASGI. Минимально допустимое итоговое покрытие — 98%.

Правильный порядок полной проверки:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run

coverage erase
coverage run manage.py test
coverage report -m

flake8 apps users config docker manage.py
```

Важно: `coverage report` выполняется после `coverage run`. Команда
`coverage erase` перед отчётом удалит только что собранные данные.

Трассировки `AIProviderError` в тестовом выводе допустимы, когда тест специально
проверяет обработку недоступного провайдера. Итоговый статус такого набора всё
равно должен быть `OK`.

## Эксплуатация и безопасность

- используйте уникальный `DJANGO_SECRET_KEY`;
- держите `DJANGO_DEBUG=0` в production;
- ограничивайте `DJANGO_ALLOWED_HOSTS` и доверенные CSRF origins;
- запускайте приложение через HTTPS и reverse proxy;
- храните PostgreSQL и Redis в закрытой сети;
- регулярно обновляйте зависимости и проверяйте миграции;
- создавайте резервные копии PostgreSQL и папки `media`;
- не публикуйте `.env`, `db.sqlite3`, `.coverage`, `htmlcov`, логи и секреты;
- не рассматривайте AI-ответ как замену заводской документации и проверке
  специалистом.

Перед каждым релизом выполняйте полный набор проверок из раздела
[«Тестирование и качество»](#тестирование-и-качество), создавайте резервную
копию данных, затем применяйте миграции и собирайте статику.
