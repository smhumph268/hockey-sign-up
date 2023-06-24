from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from .models import Rink, DropIn, SignUp, Games, Stats


class RinkAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,  {'fields': ['name']}),
        (None,  {'fields': ['address']}),
    ]
    list_display = ('name', 'address')


class DropInAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['rink']}),
        (None, {'fields': ['name']}),
        ('Date Information', {'fields': ['datetime'], 'classes': ['collapse']}),
        (None, {'fields': ['paypalClientID']}),
        (None, {'fields': ['skaterFee', 'goalieFee']}),
        (None, {'fields': ['visible']})
    ]
    list_display = ('id', 'datetime', 'name', 'rink', 'visible')
    list_filter = [('datetime', DateRangeFilter), 'visible', 'name', 'rink']


class GamesAdmin(admin.ModelAdmin):
    list_display = ('id', 'dropIn', 'game_number', 'winning_team_name', 'losing_team_name', 'winning_score', 'losing_score')
    list_filter = [('dropIn__datetime', DateRangeFilter), 'game_number']


class SignUpAdmin(admin.ModelAdmin):
    list_display = ('id', 'dropIn', 'user', 'get_user_full_name', 'datetime', 'paid', 'rostered', 'isWhiteTeam', 'isGoalie')
    list_filter = [('dropIn__datetime', DateRangeFilter), 'paid', 'rostered', 'isWhiteTeam', 'isGoalie']
    search_fields = ['user__first_name', 'user__last_name']

    @admin.display(ordering='user_full_name', description='Full Name')
    def get_user_full_name(self, obj):
        return obj.user.first_name+' '+obj.user.last_name


class StatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'user', 'get_user_full_name', 'goals', 'assists')
    list_filter = [('game__dropIn__datetime', DateRangeFilter), 'game__game_number']
    search_fields = ['user__first_name', 'user__last_name']

    @admin.display(ordering='user_full_name', description='Full Name')
    def get_user_full_name(self, obj):
        return obj.user.first_name + ' ' + obj.user.last_name


admin.site.register(Rink, RinkAdmin)
admin.site.register(DropIn, DropInAdmin)
admin.site.register(SignUp, SignUpAdmin)
admin.site.register(Games, GamesAdmin)
admin.site.register(Stats, StatsAdmin)


admin.AdminSite.site_header = 'DropIn Administration'
