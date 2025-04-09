from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'api_key', 'usage_limit', 'email_verified', 'usage_count')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('usage_count',)

    fieldsets = UserAdmin.fieldsets + (
        ('API Information', {'fields': ('api_key', 'usage_limit', 'usage_count')}),
        ('Account Status', {'fields': ('email_verified', 'verification_code')}),
    )


admin.site.register(User, CustomUserAdmin)