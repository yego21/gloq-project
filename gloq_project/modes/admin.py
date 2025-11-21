from django.contrib import admin
from .models import Mode, DailyContent

@admin.register(Mode)
class JournalModeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_premium', 'is_active', 'created_at')
    list_filter = ('is_premium', 'is_active')


@admin.register(DailyContent)
class DailyContentAdmin(admin.ModelAdmin):
    list_display = ('mode', 'date', 'content_type', 'personalization_key', 'content_data', 'created_at' )