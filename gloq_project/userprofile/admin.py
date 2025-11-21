from django.contrib import admin
from .models import UserProfile, BirthProfile



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'preferred_mode', 'enable_instant_commentary', 'commentary_status', 'today_count', 'created_at'
    )
    list_filter = ('preferred_mode', 'created_at', 'enable_instant_commentary')
    search_fields = ('user__username',)
    list_editable = ('enable_instant_commentary',)  # Must be in list_display too

    # Updated fieldsets with Astrology section
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'preferred_mode', 'selected_mode', 'timezone')
        }),

        # ('Astrology Data', {
        #     'fields': (
        #         'birth_date',
        #         'birth_time',
        #         'birth_place'
        #     ),
        #     'classes': ('collapse',)  # Makes this section collapsible
        # }),

        ('AI Commentary Settings', {
            'fields': (
                'enable_instant_commentary',
                'max_daily_commentaries',
                'min_words_for_commentary',
                ('last_commentary_date', 'today_commentary_count')
            ),
            'classes': ('collapse',)  # Makes this section collapsible
        }),
    )

    # Read-only fields for tracking
    readonly_fields = ('last_commentary_date', 'today_commentary_count', 'commentary_status', 'today_count')

    # Custom methods for display
    def commentary_status(self, obj):
        """Display commentary enabled status with color coding"""
        if obj.enable_instant_commentary:
            return '✅ Enabled'
        return '❌ Disabled'

    commentary_status.short_description = 'Status'

    def today_count(self, obj):
        """Show today's count with limit indicator"""
        if obj.enable_instant_commentary:
            return f"{obj.today_commentary_count}/{obj.max_daily_commentaries}"
        return 'N/A'

    today_count.short_description = 'Today/Total'

    # Add actions for bulk operations
    actions = ['enable_commentary', 'disable_commentary', 'reset_counters']

    def enable_commentary(self, request, queryset):
        """Bulk enable commentary"""
        updated = queryset.update(enable_instant_commentary=True)
        self.message_user(request, f"Enabled AI commentary for {updated} users.")

    enable_commentary.short_description = "✅ Enable AI commentary for selected users"

    def disable_commentary(self, request, queryset):
        """Bulk disable commentary"""
        updated = queryset.update(enable_instant_commentary=False)
        self.message_user(request, f"Disabled AI commentary for {updated} users.")

    disable_commentary.short_description = "❌ Disable AI commentary for selected users"

    def reset_counters(self, request, queryset):
        """Reset daily counters"""
        for profile in queryset:
            profile.today_commentary_count = 0
            profile.last_commentary_date = None
            profile.save()
        self.message_user(request, f"Reset counters for {queryset.count()} users.")

    reset_counters.short_description = "🔄 Reset daily commentary counters"


@admin.register(BirthProfile)
class BirthProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for managing birth profiles.
    Useful for testing and debugging.
    """

    list_display = [
        'user',
        'birth_date',
        'has_birth_time',
        'birth_city',
        'chart_completeness',
        'created_at'
    ]

    list_filter = ['has_birth_time', 'created_at']

    search_fields = ['user__username', 'birth_city', 'birth_country']

    readonly_fields = [
        'has_birth_time',
        'created_at',
        'updated_at',
        'chart_completeness'
    ]

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Birth Information', {
            'fields': (
                'birth_date',
                'birth_time',
                'birth_latitude',
                'birth_longitude',
                'birth_timezone',
            )
        }),
        ('Location Details', {
            'fields': ('birth_city', 'birth_country'),
            'classes': ('collapse',)  # Collapsible section
        }),
        ('Computed Data', {
            'fields': (
                'has_birth_time',
                'chart_completeness',
                'cached_chart_data',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def chart_completeness(self, obj):
        """Display completeness as a percentage in admin list."""
        return f"{obj.chart_completeness}%"

    chart_completeness.short_description = "Profile Complete"


