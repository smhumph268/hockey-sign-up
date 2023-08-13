from django.contrib import admin

from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,  {'fields': ['email']}),
        (None,  {'fields': ['username']}),
        (None,  {'fields': ['first_name']}),
        (None,  {'fields': ['last_name']}),
        (None, {'fields': ['skill_level']}),
        (None, {'fields': ['preferred_position']}),
        (None,  {'fields': ['credits']}),
        (None,  {'fields': ['is_active']})
    ]
    list_display = ('email', 'is_active', 'username', 'first_name', 'last_name', 'skill_level', 'preferred_position', 'credits')
    search_fields = ['first_name', 'last_name', 'email', 'is_active']
    list_filter = ['is_active']


admin.site.register(CustomUser, CustomUserAdmin)
