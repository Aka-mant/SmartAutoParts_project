# Подключение AI-сервиса SmartAutoParts

## 1. Установите зависимости

```bash
pip install -r requirements/base.txt
```

## 2. Добавьте переменные окружения

```dotenv
OPENAI_API_KEY=sk-...
```

Основные настройки можно переопределить в `config/settings.py`:

```python
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_AI_MODEL = "gpt-5.6-sol"
OPENAI_MODERATION_MODEL = "omni-moderation-latest"

OPENAI_CHAT_REASONING_EFFORT = "low"
OPENAI_INSTRUCTION_REASONING_EFFORT = "medium"
OPENAI_MODERATION_REASONING_EFFORT = "low"

OPENAI_CHAT_MAX_OUTPUT_TOKENS = 2_500
OPENAI_TOOL_MAX_OUTPUT_TOKENS = 3_000
OPENAI_INSTRUCTION_MAX_OUTPUT_TOKENS = 12_000
OPENAI_MODERATION_MAX_OUTPUT_TOKENS = 700
OPENAI_IMAGE_MAX_OUTPUT_TOKENS = 2_500

OPENAI_CHAT_VERBOSITY = "medium"
OPENAI_TOOL_VERBOSITY = "medium"
OPENAI_TOOL_REASONING_EFFORT = "low"
OPENAI_INSTRUCTION_VERBOSITY = "high"
OPENAI_IMAGE_VERBOSITY = "medium"
OPENAI_IMAGE_REASONING_EFFORT = "low"
OPENAI_IMAGE_DETAIL = "high"
OPENAI_TIMEOUT_SECONDS = 90
OPENAI_MAX_RETRIES = 2

AI_MAX_PROMPT_LENGTH = 8_000
AI_ENABLE_DOMAIN_MODERATION = True
AI_IMAGE_MAX_BYTES = 10 * 1024 * 1024
AI_IMAGE_MAX_PIXELS = 40_000_000
AI_IMAGE_MIN_SIDE = 64
AI_IMAGE_CATALOG_LIMIT = 250
AI_IMAGE_MIN_MATCH_CONFIDENCE = 65

# По умолчанию max_ai_requests=0 запрещает AI-запросы.
# Включите только если в вашем тарифе 0 означает «без ограничений».
AI_ZERO_QUOTA_IS_UNLIMITED = False
```

API-ключ должен находиться только на сервере. Не передавайте его в JavaScript
и не сохраняйте в репозитории.

## 3. Ответ в AI-чате

```python
from apps.AI.services import (
    AIAccessDenied,
    AIProviderError,
    AIRequestRejected,
    SmartAutoPartsAIService,
)

service = SmartAutoPartsAIService()

try:
    result = service.answer_chat(
        user=request.user,
        message=request.data["message"],
        part=part,       # необязательно
        room=chat_room, # необязательно
    )
except AIRequestRejected as exc:
    # HTTP 400: exc.decision.reason
    ...
except AIAccessDenied as exc:
    # HTTP 403
    ...
except AIProviderError as exc:
    # HTTP 503
    ...
else:
    answer = result.answer
    ai_request_id = result.ai_request.pk
```

## 4. Генерация ремонтной инструкции

```python
result = service.generate_repair_instruction(
    user=request.user,
    part=part,
    goal=request.data["goal"],
    instruction=approved_instruction,  # необязательная редакционная основа
)

markdown = result.generated_instruction.generated_content
structured_payload = result.payload
```

Результат сохраняется в `AIRequest` и `AIGeneratedInstruction`, но намеренно
не публикуется автоматически в `Instruction`. Перед публикацией инструкцию
должен проверить технический редактор или модератор.

Карточка детали формирует запрос только из данных проекта. Новая версия
сохраняется со статусом `pending` и публикуется только после проверки в:

```text
/admin/AI/aigeneratedinstruction/
```

## 5. Подбор и модерация инструментов

```python
result = service.recommend_part_tools(
    user=request.user,
    part=part,
    goal=server_goal,
)
```

Ответ сохраняется как `AIToolRecommendation` со статусом `pending`.
Непроверенный текст не выдаётся пользователю. Модерация доступна в:

```text
/admin/AI/aitoolrecommendation/
```

Одобрение открывает результат пользователю, а отклонение требует причину.
Каталог `Tool` и связи `PartTool` автоматически не изменяются.

## 6. Анализ фотографии запчасти

```python
result = service.analyze_part_image(
    user=request.user,
    image=request.FILES["image"],
    note=request.data.get("note", ""),
)

analysis_id = result.image_analysis.pk
detected_part = result.detected_part
confidence = result.image_analysis.confidence_score
payload = result.payload
```

Метод проверяет `SubscriptionPlan.has_image_analysis` и общий лимит
`max_ai_requests`. Перед анализом выполняются локальная проверка файла,
текстовая модерация и мультимодальная модерация OpenAI. Поддерживаются JPEG,
PNG, WEBP и статический GIF.

Успешный результат сохраняется одновременно в `AIRequest` и
`AIImageAnalysis`. Изображение, заблокированное модерацией, в хранилище
проекта не записывается.

HTML-загрузка:

```text
/parts/image-analysis/
```

API-загрузка:

```text
POST /api/AI/image-analyses/create/
Content-Type: multipart/form-data
image=<file>
```

Оба интерфейса используют один поток: тарифный лимит, локальную валидацию,
автоматическую мультимодальную модерацию `omni-moderation-latest`,
структурированное распознавание и сопоставление с каталогом. Успешная запись
содержит модель, время и результат автоматической модерации.

## 7. Проверка

```bash
python manage.py check
python manage.py test apps.AI.tests.SmartAutoPartsAIServiceTests
```
