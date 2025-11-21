from django.contrib import admin
from .models import UserPlan, UserUsage

@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'created_at']
    list_filter = ['plan']
    search_fields = ['user__username']

@admin.register(UserUsage)
class UserUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'tokens_used', 'actions_performed']
    list_filter = ['date']
    search_fields = ['user__username']
