from django.contrib import admin

from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,  {'fields': ['email']}),
        (None,  {'fields': ['username']}),
        (None,  {'fields': ['first_name']}),
        (None,  {'fields': ['last_name']}),
        (None,  {'fields': ['credits']})
    ]
    list_display = ('email', 'username', 'first_name', 'last_name', 'credits')
    search_fields = ['first_name', 'last_name', 'email']


admin.site.register(CustomUser, CustomUserAdmin)
