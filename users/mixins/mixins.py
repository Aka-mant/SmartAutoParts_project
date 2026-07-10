class UserOwnedQuerySetMixin:
    """
    Миксин для ограничения доступа
    к объектам пользователя.

    Суперпользователь получает доступ
    ко всем объектам.

    Остальные пользователи получают
    доступ только к собственным объектам.
    """

    user_field = "user"

    def get_queryset(self):
        """
        Возвращает queryset с учетом
        прав текущего пользователя.
        """
        queryset = super().get_queryset()

        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(
            **{self.user_field: self.request.user}
        )

