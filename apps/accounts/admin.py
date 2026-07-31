from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'role', 'is_verified', 'is_active', 'created_at')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Role & Verification', {'fields': ('role', 'phone_number', 'is_verified')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Role & Verification', {'fields': ('role', 'phone_number', 'is_verified')}),
    )

    actions = ['verify_selected_accounts']

    @admin.action(description='Verify selected accounts')
    def verify_selected_accounts(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} account(s) verified.')