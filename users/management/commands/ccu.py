from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from users.models import Profile, SearchHistory, UserRole


User = get_user_model()


class Command(BaseCommand):
    """
    Создание тестовых пользователей, профилей
    и истории поиска.
    """

    help = _("Создание тестовых пользователей, профилей и истории поиска")

    def handle(self, *args, **options):
        profiles = {
            UserRole.GUEST: {
                "country": "Germany",
                "city": "Berlin",
                "preferred_language": "de",
                "car_brand": "",
                "car_model": "",
                "car_year": None,
                "bio": _("Гостевой профиль."),
            },
            UserRole.USER: {
                "country": "Ukraine",
                "city": "Kyiv",
                "preferred_language": "uk",
                "car_brand": "Toyota",
                "car_model": "Corolla",
                "car_year": 2020,
                "bio": _("Стандартный профиль пользователя."),
            },
            UserRole.PREMIUM: {
                "country": "Poland",
                "city": "Warsaw",
                "preferred_language": "pl",
                "car_brand": "BMW",
                "car_model": "X5",
                "car_year": 2022,
                "bio": _("Премиум-пользователь."),
            },
            UserRole.MODERATOR: {
                "country": "Netherlands",
                "city": "Amsterdam",
                "preferred_language": "en",
                "car_brand": "Audi",
                "car_model": "A6",
                "car_year": 2021,
                "bio": _("Профиль модератора."),
            },
        }

        users = [
            {
                "email": "guest@example.com",
                "username": "guest",
                "password": "guest12345",
                "role": UserRole.GUEST,
            },
            {
                "email": "user@example.com",
                "username": "user",
                "password": "user12345",
                "role": UserRole.USER,
            },
            {
                "email": "premium@example.com",
                "username": "premium",
                "password": "premium12345",
                "role": UserRole.PREMIUM,
            },
            {
                "email": "moderator@example.com",
                "username": "moderator",
                "password": "moderator12345",
                "role": UserRole.MODERATOR,
            },
        ]

        created_users = 0
        created_profiles = 0
        created_history = 0

        for data in users:
            user, user_created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "username": data["username"],
                    "role": data["role"],
                },
            )

            if user_created:
                user.set_password(data["password"])
                user.save()
                created_users += 1

            profile, profile_created = Profile.objects.get_or_create(
                user=user,
                defaults=profiles[user.role],
            )

            if profile_created:
                created_profiles += 1

            if not SearchHistory.objects.filter(user=user).exists():
                SearchHistory.objects.bulk_create(
                    [
                        SearchHistory(
                            user=user,
                            original_number="06A115561B",
                            search_query="06A115561B",
                            result_found=True,
                        ),
                        SearchHistory(
                            user=user,
                            original_number="8K0615301",
                            search_query="8K0615301",
                            result_found=True,
                        ),
                        SearchHistory(
                            user=user,
                            original_number="TEST-0001",
                            search_query="TEST-0001",
                            result_found=False,
                        ),
                    ]
                )
                created_history += 3

        self.stdout.write(
            self.style.SUCCESS(
                _(
                    "Создано пользователей: {}\n"
                    "Создано профилей: {}\n"
                    "Создано записей истории: {}"
                ).format(
                    created_users,
                    created_profiles,
                    created_history,
                )
            )
        )