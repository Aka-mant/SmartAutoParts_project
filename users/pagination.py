from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """
    Стандартная пагинация
    для API.

    Использует постраничный
    вывод результатов.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"


class SmallPagination(PageNumberPagination):
    """
    Компактная пагинация
    для небольших списков.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

