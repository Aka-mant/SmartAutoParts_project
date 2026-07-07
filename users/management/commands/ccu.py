import os

from django.core.management.base import BaseCommand

from users.models import User, UserRole


class Command(BaseCommand):
    """
    Создание пользователей всех ролей по умолчанию.
    """

    help = "Создание пользователей всех ролей"


    def handle(self, *args, **options):

        users = [
            {
                "email": "guest@example.com",
                "password": os.getenv(
                    "GUEST_PASSWORD",
                    "12345678",
                ),
                "username": "guest",
                "first_name": "Guest",
                "last_name": "User",
                "role": UserRole.GUEST,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "user@example.com",
                "password": os.getenv(
                    "USER_PASSWORD",
                    "12345678",
                ),
                "username": "user",
                "first_name": "Regular",
                "last_name": "User",
                "role": UserRole.USER,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "premium@example.com",
                "password": os.getenv(
                    "PREMIUM_PASSWORD",
                    "12345678",
                ),
                "username": "premium",
                "first_name": "Premium",
                "last_name": "User",
                "role": UserRole.PREMIUM,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "moderator@example.com",
                "password": os.getenv(
                    "MODERATOR_PASSWORD",
                    "12345678",
                ),
                "username": "moderator",
                "first_name": "Moderator",
                "last_name": "User",
                "role": UserRole.MODERATOR,
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "admin@example.com",
                "password": os.getenv(
                    "ADMIN_PASSWORD",
                    "12345678",
                ),
                "username": "admin",
                "first_name": "Super",
                "last_name": "Admin",
                "role": UserRole.SUPERUSER,
                "is_staff": True,
                "is_superuser": True,
            },
        ]


        for user_data in users:

            email = user_data["email"]

            if User.objects.filter(email=email).exists():

                self.stdout.write(
                    self.style.WARNING(
                        f'Пользователь "{email}" уже существует.'
                    )
                )

                continue


            if user_data["is_superuser"]:

                user = User.objects.create_superuser(
                    email=email,
                    username=user_data["username"],
                    password=user_data["password"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data["role"],
                )

            else:

                user = User.objects.create_user(
                    email=email,
                    username=user_data["username"],
                    password=user_data["password"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data["role"],
                    is_staff=user_data["is_staff"],
                    is_active=True,
                )


            self.stdout.write(
                self.style.SUCCESS(
                    f'Создан пользователь: {user.email} '
                    f'({user.get_role_display()})'
                )
            )