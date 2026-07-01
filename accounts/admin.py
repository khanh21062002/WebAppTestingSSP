from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'get_full_name', 'email', 'role', 'class_name', 'student_id', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'class_name']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'student_id']
    ordering = ['-date_joined']
    list_per_page = 30

    fieldsets = UserAdmin.fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('role', 'phone', 'avatar', 'student_id', 'class_name')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('role', 'first_name', 'last_name', 'email', 'student_id', 'class_name')
        }),
    )
