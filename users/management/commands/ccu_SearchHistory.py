
from django.core.management.base import BaseCommand

from users.models import SearchHistory, User


class Command(BaseCommand):
    """
    Создание тестовой истории поиска пользователей.
    """

    help = "Создание тестовой истории поиска"

    def handle(self, *args, **options):

        searches = [
            {
                "original_number": "90915-YZZJ1",
                "search_query": "Toyota Corolla oil filter",
                "result_found": True,
            },
            {
                "original_number": "A001989680313",
                "search_query": "Mercedes engine oil",
                "result_found": True,
            },
            {
                "original_number": "123456789",
                "search_query": "Unknown part",
                "result_found": False,
            },
        ]

        created_count = 0
        skipped_count = 0

        for user in User.objects.all():
            for search in searches:
                history, created = SearchHistory.objects.get_or_create(
                    user=user,
                    original_number=search["original_number"],
                    search_query=search["search_query"],
                    defaults={
                        "result_found": search["result_found"],
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✔ История создана для {user.email}"
                        )
                    )
                else:
                    skipped_count += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Создано записей: {created_count}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Пропущено: {skipped_count}"
            )
        )