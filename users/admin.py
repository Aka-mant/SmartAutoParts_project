from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'role')
    list_filter = ('is_staff', 'is_active', 'role')
    search_fields = ('username', 'email')
