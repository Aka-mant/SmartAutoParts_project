class UserOwnedQuerySetMixin:
    """
    Ограничивает queryset объектами
    текущего пользователя.

    Администраторы и системные
    суперпользователи получают полный queryset.
    """

    user_field = "user"

    def get_queryset(self):
        """
        Возвращает доступный текущему
        пользователю queryset.
        """

        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.can_administrate:
            return queryset

        return queryset.filter(
            **{
                self.user_field: user,
            }
        )
