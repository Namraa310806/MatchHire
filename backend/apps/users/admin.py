from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model with email-based authentication.
    
    Configures the admin interface to work with email as the USERNAME_FIELD
    instead of username. Password field is handled by Django's built-in
    password management and is not exposed as an editable field.
    """
    inlines = (UserProfileInline,)
    list_display = ('email', 'username', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('email', 'username')
    
    # Configure field ordering for email-based authentication
    ordering = ('email',)
    
    # Override fieldsets to remove password from editable fields
    # Password is managed through Django's built-in password change mechanism
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'username')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Configure add_user fieldsets for email-based authentication
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


admin.site.register(User, UserAdmin)
