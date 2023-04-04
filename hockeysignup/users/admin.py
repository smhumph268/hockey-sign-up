from django.contrib import admin

from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,  {'fields': ['email']}),
        (None,  {'fields': ['username']}),
        (None,  {'fields': ['first_name']}),
        (None,  {'fields': ['last_name']})
    ]
    list_display = ('email', 'username', 'first_name', 'last_name')


admin.site.register(CustomUser, CustomUserAdmin)
