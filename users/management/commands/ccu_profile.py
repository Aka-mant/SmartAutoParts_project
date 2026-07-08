from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from users.models import Profile, UserRole


User = get_user_model()


class Command(BaseCommand):
    """
    Создание профилей для пользователей,
    если они отсутствуют.
    """

    help = "Создание профилей пользователей"


    def handle(self, *args, **options):

        profiles = {
            UserRole.GUEST: {
                "country": "",
                "city": "",
                "preferred_language": "Russian",
                "car_brand": "",
                "car_model": "",
                "car_year": None,
                "bio": "Гость системы.",
            },
            UserRole.USER: {
                "country": "Russia",
                "city": "Moscow",
                "preferred_language": "Russian",
                "car_brand": "Toyota",
                "car_model": "Corolla",
                "car_year": 2020,
                "bio": "Обычный пользователь.",
            },
            UserRole.PREMIUM: {
                "country": "Germany",
                "city": "Berlin",
                "preferred_language": "Russian",
                "car_brand": "BMW",
                "car_model": "X5",
                "car_year": 2023,
                "bio": "Премиум-пользователь.",
            },
            UserRole.MODERATOR: {
                "country": "Poland",
                "city": "Warsaw",
                "preferred_language": "Russian",
                "car_brand": "Skoda",
                "car_model": "Octavia",
                "car_year": 2022,
                "bio": "Модератор системы.",
            },
            UserRole.SUPERUSER: {
                "country": "USA",
                "city": "New York",
                "preferred_language": "English",
                "car_brand": "Tesla",
                "car_model": "Model S",
                "car_year": 2024,
                "bio": "Суперпользователь системы.",
            },
        }

        created_count = 0
        skipped_count = 0

        for user in User.objects.all():

            profile_data = profiles.get(user.role)

            if profile_data is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"Не найдены данные профиля для роли '{user.role}'."
                    )
                )
                continue

            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults=profile_data,
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔ Профиль создан для {user.email}"
                    )
                )
            else:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"• Профиль уже существует для {user.email}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Создано профилей: {created_count}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Пропущено: {skipped_count}"
            )
        )
