import random
import uuid
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from PIL import Image

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.AI.models import (
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIRequest,
)
from apps.analytics.models import (
    PopularPart,
    SearchLog,
    UserActivity,
)
from apps.chat.models import (
    ChatMessage,
    ChatParticipant,
    ChatRoom,
)
from apps.instructions.models import (
    Instruction,
    InstructionImage,
    InstructionStep,
    InstructionTool,
    InstructionVersion,
)
from apps.parts.models import (
    Compatibility,
    OEMNumber,
    Part,
    PartCategory,
    PartImage,
)
from apps.subscriptions.models import (
    SubscriptionPayment,
    SubscriptionPlan,
    UserSubscription,
)
from apps.tools.models import (
    PartTool,
    Tool,
    ToolCategory,
)
from users.models import (
    Profile,
    RepairHistory,
    SearchHistory,
    UserRole,
)


User = get_user_model()


class Command(BaseCommand):
    """
    Создание тестовых данных для всех приложений проекта.

    Команда формирует связанные тестовые записи для:

    - пользователей;
    - профилей;
    - истории поиска и ремонта;
    - категорий и автомобильных запчастей;
    - OEM-номеров;
    - совместимости автомобилей;
    - изображений запчастей;
    - инструментов;
    - инструкций;
    - подписок и платежей;
    - чатов и сообщений;
    - аналитики;
    - AI-запросов и результатов анализа.

    Для каждой основной модели создается случайное количество
    записей в диапазоне от 20 до 50.
    """

    help = (
        "Создает от 20 до 50 связанных тестовых записей "
        "для моделей всех приложений проекта."
    )

    MIN_OBJECTS = 20
    MAX_OBJECTS = 50

    FIRST_NAMES = (
        "Александр",
        "Дмитрий",
        "Михаил",
        "Алексей",
        "Сергей",
        "Иван",
        "Анна",
        "Мария",
        "Елена",
        "Ольга",
        "Наталья",
        "Ирина",
    )

    LAST_NAMES = (
        "Иванов",
        "Петров",
        "Сидоров",
        "Смирнов",
        "Кузнецов",
        "Попов",
        "Васильев",
        "Соколов",
        "Михайлов",
        "Новиков",
    )

    COUNTRIES = (
        "Россия",
        "Германия",
        "Нидерланды",
        "Франция",
        "Италия",
        "Испания",
        "Польша",
        "Чехия",
    )

    CITIES = (
        "Москва",
        "Санкт-Петербург",
        "Берлин",
        "Амстердам",
        "Роттердам",
        "Париж",
        "Милан",
        "Варшава",
        "Прага",
    )

    CAR_BRANDS = (
        "Toyota",
        "BMW",
        "Mercedes-Benz",
        "Audi",
        "Volkswagen",
        "Ford",
        "Honda",
        "Nissan",
        "Volvo",
        "Skoda",
        "Renault",
        "Peugeot",
    )

    CAR_MODELS = {
        "Toyota": ("Corolla", "Camry", "RAV4", "Yaris"),
        "BMW": ("3 Series", "5 Series", "X3", "X5"),
        "Mercedes-Benz": ("C-Class", "E-Class", "GLC", "GLE"),
        "Audi": ("A3", "A4", "A6", "Q5"),
        "Volkswagen": ("Golf", "Passat", "Tiguan", "Polo"),
        "Ford": ("Focus", "Mondeo", "Kuga", "Fiesta"),
        "Honda": ("Civic", "Accord", "CR-V", "Jazz"),
        "Nissan": ("Qashqai", "X-Trail", "Juke", "Micra"),
        "Volvo": ("S60", "S90", "XC60", "XC90"),
        "Skoda": ("Octavia", "Superb", "Kodiaq", "Fabia"),
        "Renault": ("Megane", "Clio", "Duster", "Captur"),
        "Peugeot": ("208", "308", "3008", "5008"),
    }

    PART_NAMES = (
        "Масляный фильтр",
        "Воздушный фильтр",
        "Тормозной диск",
        "Тормозные колодки",
        "Свеча зажигания",
        "Ремень ГРМ",
        "Радиатор",
        "Генератор",
        "Стартер",
        "Топливный насос",
        "Амортизатор",
        "Шаровая опора",
        "Ступичный подшипник",
        "Датчик кислорода",
        "Катушка зажигания",
        "Фара",
        "Задний фонарь",
        "Сцепление",
        "Водяной насос",
        "Термостат",
    )

    PART_MANUFACTURERS = (
        "Bosch",
        "Febi",
        "Mann-Filter",
        "Mahle",
        "Sachs",
        "Valeo",
        "Denso",
        "NGK",
        "Brembo",
        "SKF",
        "Gates",
        "Contitech",
    )

    TOOL_NAMES = (
        "Торцевой ключ",
        "Динамометрический ключ",
        "Отвертка",
        "Пассатижи",
        "Домкрат",
        "Съемник подшипников",
        "Набор головок",
        "Трещотка",
        "Мультиметр",
        "Диагностический сканер",
        "Молоток",
        "Монтажная лопатка",
        "Шестигранный ключ",
        "Ключ для масляного фильтра",
        "Компрессометр",
    )

    ACTIONS = (
        "user_login",
        "user_logout",
        "part_search",
        "part_view",
        "instruction_view",
        "instruction_started",
        "instruction_completed",
        "chat_message_sent",
        "subscription_created",
        "ai_request_created",
        "image_analysis_started",
    )

    AI_REQUEST_TYPES = (
        "part_search",
        "repair_question",
        "instruction_generation",
        "image_analysis",
        "compatibility_check",
    )

    PAYMENT_PROVIDERS = (
        "Stripe",
        "PayPal",
        "CloudPayments",
        "YooKassa",
        "Adyen",
    )

    PAYMENT_STATUSES = (
        "pending",
        "paid",
        "failed",
        "refunded",
    )

    def add_arguments(self, parser):
        """
        Добавляет аргументы management-команды.
        """

        parser.add_argument(
            "--min-count",
            type=int,
            default=self.MIN_OBJECTS,
            help="Минимальное количество создаваемых объектов.",
        )

        parser.add_argument(
            "--max-count",
            type=int,
            default=self.MAX_OBJECTS,
            help="Максимальное количество создаваемых объектов.",
        )

        parser.add_argument(
            "--password",
            type=str,
            default="Test12345!",
            help="Пароль для создаваемых тестовых пользователей.",
        )

    def handle(self, *args, **options):
        """
        Последовательно создает все тестовые сущности.
        """

        self.min_count = options["min_count"]
        self.max_count = options["max_count"]
        self.default_password = options["password"]

        if self.min_count < 1:
            self.stderr.write(
                self.style.ERROR(
                    "Параметр --min-count должен быть больше нуля."
                )
            )
            return

        if self.max_count < self.min_count:
            self.stderr.write(
                self.style.ERROR(
                    "--max-count не может быть меньше --min-count."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                "Начато создание тестовых данных..."
            )
        )

        with transaction.atomic():
            users = self.create_users()
            self.create_profiles(users)

            part_categories = self.create_part_categories()
            parts = self.create_parts(part_categories)
            self.create_oem_numbers(parts)
            self.create_compatibilities(parts)
            self.create_part_images(parts)

            tool_categories = self.create_tool_categories()
            tools = self.create_tools(tool_categories)
            self.create_part_tools(parts, tools)

            instructions = self.create_instructions(parts, users)
            self.create_instruction_versions(instructions)
            self.create_instruction_steps(instructions)
            self.create_instruction_images(instructions)
            self.create_instruction_tools(instructions, tools)

            self.create_search_history(users, parts)
            self.create_repair_history(users, instructions)

            plans = self.create_subscription_plans()
            subscriptions = self.create_user_subscriptions(
                users,
                plans,
            )
            self.create_subscription_payments(
                users,
                subscriptions,
            )

            rooms = self.create_chat_rooms(users)
            self.create_chat_participants(rooms, users)
            self.create_chat_messages(rooms, users)

            self.create_user_activities(users, parts)
            self.create_search_logs(users, parts)
            self.create_popular_parts(parts)

            ai_requests = self.create_ai_requests(users, parts)
            self.create_ai_generated_instructions(
                ai_requests,
                instructions,
            )
            self.create_ai_image_analyses(users, parts)

        self.stdout.write(
            self.style.SUCCESS(
                "Все тестовые данные успешно созданы."
            )
        )

    def get_count(self) -> int:
        """
        Возвращает случайное количество объектов.
        """

        return random.randint(
            self.min_count,
            self.max_count,
        )

    @staticmethod
    def unique_suffix() -> str:
        """
        Возвращает короткий уникальный идентификатор.
        """

        return uuid.uuid4().hex[:12]

    def unique_slug(self, value: str) -> str:
        """
        Создает уникальный slug.
        """

        base_slug = slugify(
            value,
            allow_unicode=True,
        )

        return f"{base_slug}-{self.unique_suffix()}"

    @staticmethod
    def random_datetime(
        days_back: int = 365,
    ):
        """
        Возвращает случайную дату в прошлом.
        """

        return timezone.now() - timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

    @staticmethod
    def random_decimal(
        minimum: float,
        maximum: float,
    ) -> Decimal:
        """
        Возвращает случайное Decimal-значение.
        """

        return Decimal(
            str(
                round(
                    random.uniform(minimum, maximum),
                    2,
                )
            )
        )

    def print_created(
        self,
        model_name: str,
        count: int,
    ) -> None:
        """
        Выводит количество созданных объектов.
        """

        self.stdout.write(
            self.style.SUCCESS(
                f"{model_name}: создано {count}"
            )
        )
    def create_users(self) -> list[User]:
        """
        Создает тестовых пользователей.
        """

        users = []
        count = self.get_count()

        roles = (
            UserRole.GUEST,
            UserRole.USER,
            UserRole.PREMIUM,
            UserRole.MODERATOR,
        )

        for index in range(1, count + 1):
            suffix = self.unique_suffix()
            first_name = random.choice(self.FIRST_NAMES)
            last_name = random.choice(self.LAST_NAMES)

            email = f"user_{suffix}@example.com"
            username = f"user_{suffix}"

            user = User.objects.create_user(
                email=email,
                username=username,
                password=self.default_password,
                first_name=first_name,
                last_name=last_name,
                phone=f"+31{random.randint(600000000, 699999999)}",
                role=random.choice(roles),
                is_active=True,
            )

            users.append(user)

        self.print_created(
            "User",
            len(users),
        )

        return users

    def create_profiles(
        self,
        users: list[User],
    ) -> list[Profile]:
        """
        Создает профиль для каждого тестового пользователя.
        """

        profiles = []

        for user in users:
            brand = random.choice(self.CAR_BRANDS)
            car_model = random.choice(
                self.CAR_MODELS[brand]
            )

            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    "country": random.choice(self.COUNTRIES),
                    "city": random.choice(self.CITIES),
                    "preferred_language": random.choice(
                        (
                            "Russian",
                            "English",
                            "German",
                            "Dutch",
                        )
                    ),
                    "car_brand": brand,
                    "car_model": car_model,
                    "car_year": random.randint(1995, 2026),
                    "bio": (
                        f"Тестовый профиль пользователя "
                        f"{user.first_name} {user.last_name}."
                    ),
                },
            )

            if created:
                profiles.append(profile)

        self.print_created(
            "Profile",
            len(profiles),
        )

        return profiles

    def create_search_history(
        self,
        users: list[User],
        parts: list[Part],
    ) -> list[SearchHistory]:
        """
        Создает историю поисковых запросов пользователей.
        """

        search_history = []
        count = self.get_count()

        for _ in range(count):
            part = random.choice(parts)
            user = random.choice(users)

            search = SearchHistory.objects.create(
                user=user,
                original_number=part.original_number,
                search_query=random.choice(
                    (
                        part.name,
                        part.original_number,
                        f"{part.name} {part.manufacturer}",
                        f"OEM {part.original_number}",
                    )
                ),
                result_found=random.choice(
                    (
                        True,
                        True,
                        True,
                        False,
                    )
                ),
            )

            SearchHistory.objects.filter(
                pk=search.pk
            ).update(
                searched_at=self.random_datetime(
                    days_back=180,
                )
            )

            search.refresh_from_db()
            search_history.append(search)

        self.print_created(
            "SearchHistory",
            len(search_history),
        )

        return search_history

    def create_repair_history(
        self,
        users: list[User],
        instructions: list[Instruction],
    ) -> list[RepairHistory]:
        """
        Создает историю выполнения ремонтов.
        """

        repair_history = []
        count = self.get_count()

        used_pairs = set()

        while len(repair_history) < count:
            user = random.choice(users)
            instruction = random.choice(instructions)

            pair = (
                user.pk,
                instruction.pk,
            )

            if pair in used_pairs:
                continue

            used_pairs.add(pair)

            completed = random.choice(
                (
                    True,
                    False,
                )
            )

            repair = RepairHistory.objects.create(
                user=user,
                instruction=instruction,
                completed=completed,
                notes=(
                    "Ремонт успешно завершен."
                    if completed
                    else "Работы еще выполняются."
                ),
            )

            RepairHistory.objects.filter(
                pk=repair.pk
            ).update(
                created_at=self.random_datetime(
                    days_back=365,
                )
            )

            repair.refresh_from_db()
            repair_history.append(repair)

        self.print_created(
            "RepairHistory",
            len(repair_history),
        )

        return repair_history

    def create_part_categories(
        self,
    ) -> list[PartCategory]:
        """
        Создает категории автомобильных запчастей.
        """

        category_names = (
            "Двигатель",
            "Тормозная система",
            "Подвеска",
            "Рулевое управление",
            "Трансмиссия",
            "Система охлаждения",
            "Электрооборудование",
            "Система зажигания",
            "Топливная система",
            "Фильтры",
            "Кузов",
            "Освещение",
            "Система выпуска",
            "Кондиционирование",
            "Стеклоочистители",
            "Подшипники",
            "Ремни и ролики",
            "Сцепление",
            "Датчики",
            "Расходные материалы",
            "Колесная система",
            "Система отопления",
            "Автомобильная оптика",
            "Элементы крепления",
            "Моторные масла",
        )

        categories = []
        count = min(
            self.get_count(),
            len(category_names),
        )

        selected_names = random.sample(
            category_names,
            count,
        )

        for name in selected_names:
            category = PartCategory.objects.create(
                name=name,
                slug=self.unique_slug(name),
                description=(
                    f"Тестовая категория автомобильных "
                    f"запчастей: {name}."
                ),
            )

            categories.append(category)

        self.print_created(
            "PartCategory",
            len(categories),
        )

        return categories

    def create_parts(
        self,
        categories: list[PartCategory],
    ) -> list[Part]:
        """
        Создает автомобильные запчасти.
        """

        parts = []
        count = self.get_count()

        for index in range(1, count + 1):
            part_name = random.choice(self.PART_NAMES)
            manufacturer = random.choice(
                self.PART_MANUFACTURERS
            )
            suffix = self.unique_suffix().upper()

            full_name = (
                f"{part_name} {manufacturer} "
                f"{index}"
            )

            original_number = (
                f"{manufacturer[:3].upper()}-"
                f"{random.randint(10000, 99999)}-"
                f"{suffix[:5]}"
            )

            length = random.randint(50, 800)
            width = random.randint(30, 500)
            height = random.randint(20, 400)

            part = Part.objects.create(
                category=random.choice(categories),
                name=full_name,
                slug=self.unique_slug(full_name),
                original_number=original_number,
                manufacturer=manufacturer,
                description=(
                    f"Тестовая автомобильная запчасть "
                    f"{full_name}. Подходит для ремонта "
                    f"и технического обслуживания автомобиля."
                ),
                seo_title=(
                    f"Купить {full_name} по OEM-номеру"
                ),
                seo_description=(
                    f"Описание, совместимость и инструкции "
                    f"для запчасти {full_name}."
                ),
                seo_keywords=(
                    f"{part_name}, {manufacturer}, "
                    f"{original_number}, автозапчасть"
                ),
                weight=self.random_decimal(
                    0.05,
                    50.0,
                ),
                dimensions={
                    "length_mm": length,
                    "width_mm": width,
                    "height_mm": height,
                },
                is_active=random.choice(
                    (
                        True,
                        True,
                        True,
                        False,
                    )
                ),
            )

            parts.append(part)

        self.print_created(
            "Part",
            len(parts),
        )

        return parts

    def create_oem_numbers(
        self,
        parts: list[Part],
    ) -> list[OEMNumber]:
        """
        Создает дополнительные OEM-номера запчастей.
        """

        oem_numbers = []
        count = self.get_count()

        for index in range(1, count + 1):
            part = random.choice(parts)
            manufacturer = random.choice(
                self.PART_MANUFACTURERS
            )

            number = (
                f"OEM-{manufacturer[:3].upper()}-"
                f"{random.randint(100000, 999999)}-"
                f"{self.unique_suffix()[:4].upper()}"
            )

            oem_number = OEMNumber.objects.create(
                part=part,
                number=number,
                manufacturer=manufacturer,
            )

            oem_numbers.append(oem_number)

        self.print_created(
            "OEMNumber",
            len(oem_numbers),
        )

        return oem_numbers

    def create_compatibilities(
        self,
        parts: list[Part],
    ) -> list[Compatibility]:
        """
        Создает записи совместимости запчастей с автомобилями.
        """

        compatibilities = []
        count = self.get_count()

        generations = (
            "I",
            "II",
            "III",
            "IV",
            "V",
            "VI",
            "Mk1",
            "Mk2",
            "Mk3",
            "F30",
            "F10",
            "E90",
            "W204",
            "W213",
        )

        engines = (
            "1.2 бензин",
            "1.4 бензин",
            "1.6 бензин",
            "2.0 бензин",
            "2.5 бензин",
            "1.5 дизель",
            "1.6 дизель",
            "2.0 дизель",
            "2.2 дизель",
            "Гибрид",
            "Электрический",
        )

        for _ in range(count):
            part = random.choice(parts)
            brand = random.choice(self.CAR_BRANDS)
            car_model = random.choice(
                self.CAR_MODELS[brand]
            )

            year_from = random.randint(
                1995,
                2022,
            )
            year_to = random.randint(
                year_from,
                2026,
            )

            compatibility = Compatibility.objects.create(
                part=part,
                brand=brand,
                model=car_model,
                generation=random.choice(generations),
                engine=random.choice(engines),
                year_from=year_from,
                year_to=year_to,
            )

            compatibilities.append(compatibility)

        self.print_created(
            "Compatibility",
            len(compatibilities),
        )

        return compatibilities

    def create_part_images(
        self,
        parts: list[Part],
    ) -> list[PartImage]:
        """
        Создает тестовые изображения запчастей.

        Вместо реальных изображений создаются небольшие
        текстовые файлы с расширением .jpg. Для полноценного
        тестирования ImageField желательно заменить их
        реальными изображениями.
        """

        part_images = []
        count = self.get_count()
        parts_with_main_image = set()

        for index in range(1, count + 1):
            part = random.choice(parts)

            is_main = part.pk not in parts_with_main_image

            if is_main:
                parts_with_main_image.add(part.pk)

            image_content = self.create_test_image(
                filename=(
                    f"part_{part.pk}_"
                    f"{self.unique_suffix()}.png"
                ),
                width=1000,
                height=750,
            )

            part_image = PartImage.objects.create(
                part=part,
                image=image_content,
                alt_text=(
                    f"Изображение запчасти {part.name}"
                ),
                is_main=is_main,
            )

            part_images.append(part_image)

        self.print_created(
            "PartImage",
            len(part_images),
        )

        return part_images

    def create_tool_categories(
        self,
    ) -> list[ToolCategory]:
        """
        Создает категории инструментов.
        """

        category_names = (
            "Гаечные ключи",
            "Торцевые головки",
            "Отвертки",
            "Пассатижи и клещи",
            "Съемники",
            "Диагностическое оборудование",
            "Электроинструменты",
            "Измерительные инструменты",
            "Домкраты и опоры",
            "Инструменты для двигателя",
            "Инструменты для тормозной системы",
            "Инструменты для подвески",
            "Инструменты для электрики",
            "Инструменты для кузовного ремонта",
            "Монтажные инструменты",
            "Режущие инструменты",
            "Ударные инструменты",
            "Инструменты для замены масла",
            "Специальные ключи",
            "Оборудование для шиномонтажа",
        )

        categories = []
        count = self.get_count()

        for index in range(1, count + 1):
            base_name = random.choice(category_names)
            name = f"{base_name} {index}"

            category = ToolCategory.objects.create(
                name=name,
                slug=self.unique_slug(name),
            )

            categories.append(category)

        self.print_created(
            "ToolCategory",
            len(categories),
        )

        return categories

    def create_tools(
        self,
        categories: list[ToolCategory],
    ) -> list[Tool]:
        """
        Создает тестовые инструменты.
        """

        tools = []
        count = self.get_count()

        sizes = (
            "6 мм",
            "8 мм",
            "10 мм",
            "12 мм",
            "13 мм",
            "14 мм",
            "17 мм",
            "19 мм",
            "21 мм",
            "22 мм",
            "24 мм",
            "1/4 дюйма",
            "3/8 дюйма",
            "1/2 дюйма",
            "Универсальный",
        )

        for index in range(1, count + 1):
            base_name = random.choice(self.TOOL_NAMES)
            size = random.choice(sizes)
            name = f"{base_name} {size} #{index}"

            tool = Tool.objects.create(
                category=random.choice(categories),
                name=name,
                description=(
                    f"Тестовый инструмент «{name}». "
                    f"Используется при ремонте и техническом "
                    f"обслуживании автомобиля."
                ),
                size=size,
                amazon_url=(
                    "https://www.amazon.com/s?"
                    f"k={slugify(base_name)}"
                ),
            )

            tools.append(tool)

        self.print_created(
            "Tool",
            len(tools),
        )

        return tools

    def create_part_tools(
        self,
        parts: list[Part],
        tools: list[Tool],
    ) -> list[PartTool]:
        """
        Создает связи между запчастями и инструментами.
        """

        part_tools = []
        target_count = self.get_count()
        used_pairs = set()

        max_combinations = len(parts) * len(tools)
        target_count = min(
            target_count,
            max_combinations,
        )

        attempts = 0
        max_attempts = target_count * 20

        while (
            len(part_tools) < target_count
            and attempts < max_attempts
        ):
            attempts += 1

            part = random.choice(parts)
            tool = random.choice(tools)

            pair = (
                part.pk,
                tool.pk,
            )

            if pair in used_pairs:
                continue

            used_pairs.add(pair)

            part_tool = PartTool.objects.create(
                part=part,
                tool=tool,
                required=random.choice(
                    (
                        True,
                        True,
                        True,
                        False,
                    )
                ),
            )

            part_tools.append(part_tool)

        self.print_created(
            "PartTool",
            len(part_tools),
        )

        return part_tools

    def create_instructions(
        self,
        parts: list[Part],
        users: list[User],
    ) -> list[Instruction]:
        """
        Создает инструкции по ремонту.
        """

        instructions = []
        count = self.get_count()

        difficulties = (
            "Легко",
            "Средне",
            "Сложно",
            "Для специалистов",
        )

        instruction_actions = (
            "Замена",
            "Установка",
            "Диагностика",
            "Ремонт",
            "Обслуживание",
            "Проверка",
            "Очистка",
            "Регулировка",
        )

        for index in range(1, count + 1):
            part = random.choice(parts)
            action = random.choice(instruction_actions)

            title = (
                f"{action}: {part.name} "
                f"#{index}"
            )

            content = (
                f"Инструкция по выполнению операции "
                f"«{action.lower()}» для запчасти "
                f"«{part.name}».\n\n"
                f"Перед началом работ установите автомобиль "
                f"на ровную поверхность, выключите двигатель "
                f"и соблюдайте правила техники безопасности.\n\n"
                f"Подготовьте необходимые инструменты, "
                f"проверьте состояние запчасти и убедитесь, "
                f"что новая деталь совместима с автомобилем.\n\n"
                f"Выполняйте работы последовательно, "
                f"не превышая рекомендуемые моменты затяжки."
            )

            instruction = Instruction.objects.create(
                part=part,
                title=title,
                slug=self.unique_slug(title),
                short_description=(
                    f"Пошаговая инструкция: "
                    f"{action.lower()} детали {part.name}."
                ),
                content=content,
                difficulty=random.choice(difficulties),
                estimated_time=random.randint(15, 360),
                premium_only=random.choice(
                    (
                        False,
                        False,
                        False,
                        True,
                    )
                ),
                version=1,
                created_by=random.choice(users),
            )

            instructions.append(instruction)

        self.print_created(
            "Instruction",
            len(instructions),
        )

        return instructions

    def create_instruction_versions(
        self,
        instructions: list[Instruction],
    ) -> list[InstructionVersion]:
        """
        Создает версии инструкций.
        """

        versions = []
        target_count = self.get_count()
        used_pairs = set()

        while len(versions) < target_count:
            instruction = random.choice(instructions)
            version_number = random.randint(1, 10)

            pair = (
                instruction.pk,
                version_number,
            )

            if pair in used_pairs:
                continue

            used_pairs.add(pair)

            version = InstructionVersion.objects.create(
                instruction=instruction,
                version_number=version_number,
                content=(
                    f"Версия {version_number} инструкции "
                    f"«{instruction.title}».\n\n"
                    f"Обновленное тестовое содержание инструкции. "
                    f"Добавлены рекомендации по технике безопасности, "
                    f"порядку выполнения работ и проверке результата."
                ),
                changelog=(
                    f"Изменения версии {version_number}: "
                    f"обновлено описание, уточнены этапы ремонта "
                    f"и добавлены дополнительные рекомендации."
                ),
            )

            versions.append(version)

        self.print_created(
            "InstructionVersion",
            len(versions),
        )

        return versions

    def create_instruction_steps(
        self,
        instructions: list[Instruction],
    ) -> list[InstructionStep]:
        """
        Создает шаги инструкций.
        """

        steps = []
        target_count = self.get_count()
        used_pairs = set()

        step_titles = (
            "Подготовка автомобиля",
            "Подготовка инструментов",
            "Отключение аккумулятора",
            "Получение доступа к детали",
            "Снятие защитных элементов",
            "Ослабление креплений",
            "Демонтаж старой детали",
            "Очистка посадочного места",
            "Проверка новой детали",
            "Установка новой детали",
            "Затяжка креплений",
            "Подключение разъемов",
            "Сборка элементов",
            "Проверка работы",
            "Контрольный осмотр",
        )

        while len(steps) < target_count:
            instruction = random.choice(instructions)
            step_number = random.randint(1, 20)

            pair = (
                instruction.pk,
                step_number,
            )

            if pair in used_pairs:
                continue

            used_pairs.add(pair)

            title = random.choice(step_titles)
            has_warning = random.choice(
                (
                    False,
                    False,
                    True,
                )
            )

            step = InstructionStep.objects.create(
                instruction=instruction,
                step_number=step_number,
                title=title,
                description=(
                    f"{title}. Выполните этот этап аккуратно "
                    f"и последовательно. Используйте подходящие "
                    f"инструменты и контролируйте состояние "
                    f"крепежных элементов."
                ),
                warning=(
                    "Перед выполнением этапа убедитесь, "
                    "что двигатель выключен, автомобиль надежно "
                    "зафиксирован, а горячие элементы остыли."
                    if has_warning
                    else ""
                ),
                estimated_minutes=random.randint(2, 45),
            )

            steps.append(step)

        self.print_created(
            "InstructionStep",
            len(steps),
        )

        return steps

    def create_instruction_images(
        self,
        instructions: list[Instruction],
    ) -> list[InstructionImage]:
        """
        Создает изображения для инструкций.

        В текущем варианте сохраняются тестовые файлы.
        """

        instruction_images = []
        count = self.get_count()

        for index in range(1, count + 1):
            instruction = random.choice(instructions)

            image_content = self.create_test_image(
                filename=(
                    f"instruction_{instruction.pk}_"
                    f"{self.unique_suffix()}.png"
                ),
                width=1200,
                height=800,
            )

            instruction_image = InstructionImage.objects.create(
                instruction=instruction,
                image=image_content,
                description=(
                    f"Тестовое изображение #{index} "
                    f"для инструкции «{instruction.title}»."
                ),
            )

            instruction_images.append(
                instruction_image
            )

        self.print_created(
            "InstructionImage",
            len(instruction_images),
        )

        return instruction_images

    def create_instruction_tools(
        self,
        instructions: list[Instruction],
        tools: list[Tool],
    ) -> list[InstructionTool]:
        """
        Создает связи инструкций с инструментами.
        """

        instruction_tools = []
        target_count = self.get_count()
        used_pairs = set()

        max_combinations = (
            len(instructions) * len(tools)
        )

        target_count = min(
            target_count,
            max_combinations,
        )

        attempts = 0
        max_attempts = target_count * 20

        while (
            len(instruction_tools) < target_count
            and attempts < max_attempts
        ):
            attempts += 1

            instruction = random.choice(instructions)
            tool = random.choice(tools)

            pair = (
                instruction.pk,
                tool.pk,
            )

            if pair in used_pairs:
                continue

            used_pairs.add(pair)

            instruction_tool = (
                InstructionTool.objects.create(
                    instruction=instruction,
                    tool=tool,
                    usage_description=(
                        f"Инструмент «{tool.name}» используется "
                        f"при выполнении инструкции "
                        f"«{instruction.title}» для демонтажа, "
                        f"установки или затяжки элементов."
                    ),
                )
            )

            instruction_tools.append(
                instruction_tool
            )

        self.print_created(
            "InstructionTool",
            len(instruction_tools),
        )

        return instruction_tools

    def create_subscription_plans(
        self,
    ) -> list[SubscriptionPlan]:
        """
        Создает тарифные планы подписки.
        """

        plans = []
        count = self.get_count()

        plan_names = (
            "Start",
            "Basic",
            "Standard",
            "Premium",
            "Pro",
            "Expert",
            "Garage",
            "Workshop",
            "Mechanic",
            "Diagnostic",
        )

        for index in range(1, count + 1):
            base_name = random.choice(plan_names)
            name = f"{base_name} {index}"

            price = self.random_decimal(
                4.99,
                99.99,
            )

            plan = SubscriptionPlan.objects.create(
                name=name,
                description=(
                    f"Тестовый тарифный план «{name}». "
                    f"Предоставляет доступ к дополнительным "
                    f"функциям сервиса SmartAutoParts."
                ),
                price=price,
                duration_days=random.choice(
                    (
                        7,
                        14,
                        30,
                        90,
                        180,
                        365,
                    )
                ),
                max_ai_requests=random.randint(
                    10,
                    1000,
                ),
                has_chat_access=random.choice(
                    (
                        True,
                        True,
                        False,
                    )
                ),
                has_image_analysis=random.choice(
                    (
                        True,
                        False,
                    )
                ),
            )

            plans.append(plan)

        self.print_created(
            "SubscriptionPlan",
            len(plans),
        )

        return plans

    def create_user_subscriptions(
        self,
        users: list[User],
        plans: list[SubscriptionPlan],
    ) -> list[UserSubscription]:
        """
        Создает подписки пользователей.
        """

        subscriptions = []
        count = self.get_count()

        for _ in range(count):
            user = random.choice(users)
            plan = random.choice(plans)

            start_date = self.random_datetime(
                days_back=365,
            )
            end_date = start_date + timedelta(
                days=plan.duration_days,
            )

            is_active = (
                end_date > timezone.now()
                and random.choice(
                    (
                        True,
                        True,
                        False,
                    )
                )
            )

            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
                auto_renew=random.choice(
                    (
                        True,
                        False,
                    )
                ),
            )

            subscriptions.append(subscription)

        self.print_created(
            "UserSubscription",
            len(subscriptions),
        )

        return subscriptions

    def create_subscription_payments(
        self,
        users: list[User],
        subscriptions: list[UserSubscription],
    ) -> list[SubscriptionPayment]:
        """
        Создает платежи за подписки.
        """

        payments = []
        count = self.get_count()

        currencies = (
            "USD",
            "EUR",
            "RUB",
            "GBP",
        )

        for _ in range(count):
            subscription = random.choice(subscriptions)
            user = subscription.user

            status = random.choice(
                self.PAYMENT_STATUSES
            )

            paid_at = None

            if status in (
                "paid",
                "refunded",
            ):
                paid_at = self.random_datetime(
                    days_back=365,
                )

            payment = SubscriptionPayment.objects.create(
                user=user,
                subscription=subscription,
                provider=random.choice(
                    self.PAYMENT_PROVIDERS
                ),
                external_payment_id=(
                    f"pay_{self.unique_suffix()}"
                ),
                amount=subscription.plan.price,
                currency=random.choice(currencies),
                status=status,
                paid_at=paid_at,
            )

            payments.append(payment)

        self.print_created(
            "SubscriptionPayment",
            len(payments),
        )

        return payments

    def create_chat_rooms(
        self,
        users: list[User],
    ) -> list[ChatRoom]:
        """
        Создает комнаты чата.
        """

        rooms = []
        count = self.get_count()

        room_topics = (
            "Общий чат",
            "Поиск запчастей",
            "Ремонт двигателя",
            "Тормозная система",
            "Подвеска автомобиля",
            "Автоэлектрика",
            "Диагностика",
            "Советы механиков",
            "Премиум-поддержка",
            "Обсуждение инструкций",
            "Инструменты",
            "OEM-номера",
        )

        for index in range(1, count + 1):
            topic = random.choice(room_topics)
            name = f"{topic} #{index}"

            room = ChatRoom.objects.create(
                name=name,
                is_private=random.choice(
                    (
                        False,
                        False,
                        False,
                        True,
                    )
                ),
                created_by=random.choice(users),
            )

            rooms.append(room)

        self.print_created(
            "ChatRoom",
            len(rooms),
        )

        return rooms

    def create_chat_participants(
        self,
        rooms: list[ChatRoom],
        users: list[User],
    ) -> list[ChatParticipant]:
        """
        Создает участников комнат чата.
        """

        participants = []
        target_count = self.get_count()
        used_pairs = set()

        max_combinations = (
            len(rooms) * len(users)
        )

        target_count = min(
            target_count,
            max_combinations,
        )

        attempts = 0
        max_attempts = target_count * 30

        while (
            len(participants) < target_count
            and attempts < max_attempts
        ):
            attempts += 1

            room = random.choice(rooms)
            user = random.choice(users)

            pair = (
                room.pk,
                user.pk,
            )

            if pair in used_pairs:
                continue

            used_pairs.add(pair)

            participant = ChatParticipant.objects.create(
                room=room,
                user=user,
            )

            ChatParticipant.objects.filter(
                pk=participant.pk
            ).update(
                joined_at=self.random_datetime(
                    days_back=180,
                )
            )

            participant.refresh_from_db()
            participants.append(participant)

        self.print_created(
            "ChatParticipant",
            len(participants),
        )

        return participants

    def create_chat_messages(
        self,
        rooms: list[ChatRoom],
        users: list[User],
    ) -> list[ChatMessage]:
        """
        Создает сообщения в комнатах чата.

        Сообщения создаются только от пользователей,
        являющихся участниками соответствующей комнаты.
        """

        messages = []
        count = self.get_count()

        message_templates = (
            "Подскажите, где найти подходящую запчасть?",
            "Кто-нибудь использовал эту инструкцию?",
            "Какой инструмент лучше подойдет для ремонта?",
            "У меня не совпадает OEM-номер.",
            "Спасибо, проблема решена.",
            "Есть ли инструкция для этой модели автомобиля?",
            "Подойдет ли эта запчасть для моего двигателя?",
            "Как проверить совместимость?",
            "Сколько времени занимает такой ремонт?",
            "Нужен ли специальный съемник?",
            "После замены появилась ошибка на панели.",
            "Где посмотреть список необходимых инструментов?",
            "Можно ли выполнить этот ремонт самостоятельно?",
            "Подскажите момент затяжки болтов.",
            "Есть ли более подробное изображение шага?",
        )

        rooms_with_participants = []

        for room in rooms:
            participant_ids = list(
                room.participants.values_list(
                    "user_id",
                    flat=True,
                )
            )

            if participant_ids:
                rooms_with_participants.append(
                    (
                        room,
                        participant_ids,
                    )
                )

        if not rooms_with_participants:
            self.print_created(
                "ChatMessage",
                0,
            )
            return messages

        for _ in range(count):
            room, participant_ids = random.choice(
                rooms_with_participants
            )

            user_id = random.choice(
                participant_ids
            )

            message = ChatMessage.objects.create(
                room=room,
                user_id=user_id,
                message=random.choice(
                    message_templates
                ),
                is_edited=random.choice(
                    (
                        False,
                        False,
                        False,
                        True,
                    )
                ),
            )

            ChatMessage.objects.filter(
                pk=message.pk
            ).update(
                created_at=self.random_datetime(
                    days_back=90,
                )
            )

            message.refresh_from_db()
            messages.append(message)

        self.print_created(
            "ChatMessage",
            len(messages),
        )

        return messages

    def create_test_image(
        self,
        filename: str,
        width: int = 800,
        height: int = 600,
    ) -> ContentFile:
        """
        Создает корректное тестовое PNG-изображение.

        Изображение можно безопасно использовать в ImageField,
        включая проекты, в которых Pillow проверяет содержимое
        загружаемого файла.
        """

        image = Image.new(
            mode="RGB",
            size=(width, height),
            color=(
                random.randint(100, 230),
                random.randint(100, 230),
                random.randint(100, 230),
            ),
        )

        buffer = BytesIO()

        image.save(
            buffer,
            format="PNG",
        )

        buffer.seek(0)

        if not filename.lower().endswith(".png"):
            filename = f"{filename}.png"

        return ContentFile(
            buffer.read(),
            name=filename,
        )

    def create_user_activities(
        self,
        users: list[User],
        parts: list[Part],
    ) -> list[UserActivity]:
        """
        Создает записи активности пользователей.
        """

        activities = []
        count = self.get_count()

        for _ in range(count):
            user = random.choice(users)
            action = random.choice(self.ACTIONS)

            part = random.choice(parts)

            metadata = {
                "source": random.choice(
                    (
                        "web",
                        "mobile",
                        "api",
                        "admin",
                    )
                ),
                "part_id": part.pk,
                "part_name": part.name,
                "original_number": part.original_number,
                "session_id": self.unique_suffix(),
            }

            activity = UserActivity.objects.create(
                user=user,
                action=action,
                metadata=metadata,
            )

            UserActivity.objects.filter(
                pk=activity.pk
            ).update(
                created_at=self.random_datetime(
                    days_back=180,
                )
            )

            activity.refresh_from_db()
            activities.append(activity)

        self.print_created(
            "UserActivity",
            len(activities),
        )

        return activities

    def create_search_logs(
        self,
        users: list[User],
        parts: list[Part],
    ) -> list[SearchLog]:
        """
        Создает аналитические журналы поисковых запросов.
        """

        search_logs = []
        count = self.get_count()

        for _ in range(count):
            part = random.choice(parts)

            query = random.choice(
                (
                    part.name,
                    part.original_number,
                    f"{part.manufacturer} {part.name}",
                    f"OEM {part.original_number}",
                    f"{part.name} для автомобиля",
                )
            )

            user = random.choice(
                users + [None]
            )

            search_log = SearchLog.objects.create(
                user=user,
                query=query,
                results_count=random.randint(0, 30),
                ip_address=(
                    f"192.168."
                    f"{random.randint(0, 255)}."
                    f"{random.randint(1, 254)}"
                ),
            )

            SearchLog.objects.filter(
                pk=search_log.pk
            ).update(
                created_at=self.random_datetime(
                    days_back=180,
                )
            )

            search_log.refresh_from_db()
            search_logs.append(search_log)

        self.print_created(
            "SearchLog",
            len(search_logs),
        )

        return search_logs

    def create_popular_parts(
        self,
        parts: list[Part],
    ) -> list[PopularPart]:
        """
        Создает статистику популярных запчастей.

        Для одной запчасти создается не более одной записи
        в рамках текущего запуска команды.
        """

        popular_parts = []

        target_count = min(
            self.get_count(),
            len(parts),
        )

        selected_parts = random.sample(
            parts,
            target_count,
        )

        for part in selected_parts:
            searches_count = random.randint(
                0,
                10_000,
            )

            views_count = random.randint(
                searches_count,
                searches_count + 20_000,
            )

            popular_part = PopularPart.objects.create(
                part=part,
                searches_count=searches_count,
                views_count=views_count,
            )

            popular_parts.append(popular_part)

        self.print_created(
            "PopularPart",
            len(popular_parts),
        )

        return popular_parts

    def create_ai_requests(
        self,
        users: list[User],
        parts: list[Part],
    ) -> list[AIRequest]:
        """
        Создает обращения пользователей к AI-сервису.
        """

        ai_requests = []
        count = self.get_count()

        prompt_templates = (
            "Как заменить деталь {part}?",
            "Подходит ли {part} для автомобиля {brand}?",
            "Какие инструменты нужны для замены {part}?",
            "Определи возможные причины неисправности {part}.",
            "Создай пошаговую инструкцию для ремонта {part}.",
            "Как проверить работоспособность детали {part}?",
            "Какие признаки износа имеет {part}?",
            "Найди совместимые аналоги для {part}.",
            "Сколько времени занимает замена {part}?",
            "Можно ли выполнить ремонт {part} самостоятельно?",
        )

        response_templates = (
            (
                "Для выполнения ремонта подготовьте автомобиль, "
                "необходимые инструменты и новую запчасть. "
                "Перед началом работ отключите аккумулятор "
                "и соблюдайте требования безопасности."
            ),
            (
                "Совместимость необходимо проверять по OEM-номеру, "
                "марке автомобиля, модели, году выпуска и типу двигателя."
            ),
            (
                "Для точной диагностики рекомендуется проверить "
                "ошибки электронных блоков, состояние проводки "
                "и механические повреждения детали."
            ),
            (
                "Пошаговый ремонт включает подготовку автомобиля, "
                "демонтаж старой детали, очистку посадочного места, "
                "установку новой детали и контрольную проверку."
            ),
        )

        for _ in range(count):
            user = random.choice(users)
            part = random.choice(parts)
            brand = random.choice(self.CAR_BRANDS)

            prompt_template = random.choice(
                prompt_templates
            )

            ai_request = AIRequest.objects.create(
                user=user,
                part=random.choice(
                    (
                        part,
                        part,
                        part,
                        None,
                    )
                ),
                prompt=prompt_template.format(
                    part=part.name,
                    brand=brand,
                ),
                response=random.choice(
                    response_templates
                ),
                tokens_used=random.randint(
                    50,
                    4000,
                ),
                request_type=random.choice(
                    self.AI_REQUEST_TYPES
                ),
            )

            AIRequest.objects.filter(
                pk=ai_request.pk
            ).update(
                created_at=self.random_datetime(
                    days_back=120,
                )
            )

            ai_request.refresh_from_db()
            ai_requests.append(ai_request)

        self.print_created(
            "AIRequest",
            len(ai_requests),
        )

        return ai_requests

    def create_ai_generated_instructions(
        self,
        ai_requests: list[AIRequest],
        instructions: list[Instruction],
    ) -> list[AIGeneratedInstruction]:
        """
        Создает инструкции, сгенерированные AI.

        Поскольку связь с AIRequest имеет тип OneToOneField,
        каждый AI-запрос используется не более одного раза.
        """

        generated_instructions = []

        available_requests = list(ai_requests)

        target_count = min(
            self.get_count(),
            len(available_requests),
        )

        selected_requests = random.sample(
            available_requests,
            target_count,
        )

        for ai_request in selected_requests:
            instruction = random.choice(
                instructions + [None]
            )

            generated_content = (
                f"Сгенерированная инструкция на основе запроса:\n"
                f"«{ai_request.prompt}»\n\n"
                f"1. Установите автомобиль на ровной поверхности.\n"
                f"2. Выключите двигатель и зафиксируйте автомобиль.\n"
                f"3. Подготовьте необходимые инструменты.\n"
                f"4. Получите доступ к ремонтируемой детали.\n"
                f"5. Демонтируйте поврежденную запчасть.\n"
                f"6. Очистите и осмотрите посадочное место.\n"
                f"7. Установите новую деталь.\n"
                f"8. Затяните крепления с рекомендуемым усилием.\n"
                f"9. Выполните сборку в обратном порядке.\n"
                f"10. Проверьте работу автомобиля.\n\n"
                f"Материал создан автоматически и должен быть "
                f"проверен специалистом перед использованием."
            )

            generated_instruction = (
                AIGeneratedInstruction.objects.create(
                    ai_request=ai_request,
                    instruction=instruction,
                    generated_content=generated_content,
                )
            )

            AIGeneratedInstruction.objects.filter(
                pk=generated_instruction.pk
            ).update(
                created_at=self.random_datetime(
                    days_back=120,
                )
            )

            generated_instruction.refresh_from_db()
            generated_instructions.append(
                generated_instruction
            )

        self.print_created(
            "AIGeneratedInstruction",
            len(generated_instructions),
        )

        return generated_instructions

    def create_ai_image_analyses(
        self,
        users: list[User],
        parts: list[Part],
    ) -> list[AIImageAnalysis]:
        """
        Создает тестовые результаты AI-анализа изображений.
        """

        analyses = []
        count = self.get_count()

        possible_conditions = (
            "new",
            "good",
            "used",
            "worn",
            "damaged",
            "unknown",
        )

        for index in range(1, count + 1):
            user = random.choice(users)

            detected_part = random.choice(
                parts + [None]
            )

            confidence_score = None

            if detected_part is not None:
                confidence_score = self.random_decimal(
                    50.00,
                    99.99,
                )

            image = self.create_test_image(
                filename=f"{self.unique_suffix()}.png",
                width=800,
                height=600,
            )

            analysis_result = {
                "detected": detected_part is not None,
                "part_id": (
                    detected_part.pk
                    if detected_part
                    else None
                ),
                "part_name": (
                    detected_part.name
                    if detected_part
                    else None
                ),
                "confidence": (
                    str(confidence_score)
                    if confidence_score is not None
                    else None
                ),
                "condition": random.choice(
                    possible_conditions
                ),
                "possible_damage": random.choice(
                    (
                        None,
                        "Коррозия",
                        "Механический износ",
                        "Трещина",
                        "Деформация",
                        "Загрязнение",
                    )
                ),
                "recommendation": (
                    "Выполнить дополнительную проверку детали "
                    "и сверить OEM-номер."
                ),
                "model_version": "test-model-1.0",
            }

            analysis = AIImageAnalysis.objects.create(
                user=user,
                image=image,
                detected_part=detected_part,
                confidence_score=confidence_score,
                analysis_result=analysis_result,
            )

            AIImageAnalysis.objects.filter(
                pk=analysis.pk
            ).update(
                created_at=self.random_datetime(
                    days_back=120,
                )
            )

            analysis.refresh_from_db()
            analyses.append(analysis)

        self.print_created(
            "AIImageAnalysis",
            len(analyses),
        )

        return analyses