from django.contrib import admin
from .models import JournalEntry, Tag, DailyPlanetarySnapshot
from modes.models import  Mode, DailyContent
from django.utils.html import format_html
from django.utils.timezone import now
from django.contrib import messages
from django.core.cache import cache
from .models import DailyPlanetarySnapshot

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_content', 'created_at')
    list_filter = ('user', 'label', 'created_at')
    search_fields = ('content', 'tags')
    filter_horizontal = ("tags",)

    def short_content(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    short_content.short_description = 'Content Preview'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


CACHE_KEY_PREFIX = "planet_snapshot_refresh_"


@admin.register(DailyPlanetarySnapshot)
class DailyPlanetarySnapshotAdmin(admin.ModelAdmin):
    list_display = ('date', 'timezone', 'data_preview', 'created_at', 'is_today', 'data_status')
    list_filter = ('date', 'timezone', 'created_at')
    search_fields = ('date', 'timezone')
    readonly_fields = ('created_at', 'data_summary', 'cache_status')
    ordering = ('-date', '-created_at')
    date_hierarchy = 'date'
    actions = ['refresh_planetary_data', 'export_as_json']

    fieldsets = (
        ('Basic Information', {
            'fields': ('date', 'timezone', 'created_at')
        }),
        ('Planetary Data', {
            'fields': ('planetary_data', 'data_summary'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Cache & Status', {
            'fields': ('cache_status',),
            'classes': ('collapse',),
        }),
    )

    def data_preview(self, obj):
        """Show a preview of planetary data in list view"""
        if not obj.planetary_data:
            return "No data"

        # Extract key planets for preview
        preview_data = []
        for planet in ['sun', 'moon', 'mercury', 'venus', 'mars']:
            if planet in obj.planetary_data:
                sign = obj.planetary_data[planet].get('sign', '')
                degree = obj.planetary_data[planet].get('degree', '')
                if sign:
                    preview_data.append(f"{planet[0].upper()}:{sign[:3]}")

        return ", ".join(preview_data[:4]) + ("..." if len(preview_data) > 4 else "")

    data_preview.short_description = "Key Planets"

    def is_today(self, obj):
        # """Check if this is today's snapshot"""837
        return obj.date == now().date()

    is_today.boolean = True
    is_today.short_description = "Today?"

    def data_status(self, obj):
        """Show data status with colored indicator"""
        if not obj.planetary_data:
            return format_html('<span style="color: red;">❌ Empty</span>')

        try:
            # If planetary_data is a JSON string
            import json
            if isinstance(obj.planetary_data, str):
                data = json.loads(obj.planetary_data)
            else:
                data = obj.planetary_data

            # Count planets in planetary_positions
            planet_count = len(data.get("planetary_positions", []))

            if planet_count >= 10:
                return format_html('<span style="color: green;">✅ Complete ({})</span>', planet_count)
            elif planet_count >= 5:
                return format_html('<span style="color: orange;">⚠️ Partial ({})</span>', planet_count)
            else:
                return format_html('<span style="color: red;">❌ Incomplete ({})</span>', planet_count)

        except (json.JSONDecodeError, AttributeError, KeyError):
            # If there's any error parsing, show as empty
            return format_html('<span style="color: red;">❌ Error</span>')

    data_status.short_description = "Data Status"

    def data_summary(self, obj):
        """Display formatted planetary data summary in detail view"""
        if not obj.planetary_data:
            return "No planetary data available."

        html = "<div style='font-family: monospace;'>"
        html += "<h4>Planetary Positions:</h4>"
        html += "<table style='border-collapse: collapse; width: 100%;'>"

        # Group planets
        personal_planets = ['sun', 'moon', 'mercury', 'venus', 'mars']
        social_planets = ['jupiter', 'saturn']
        outer_planets = ['uranus', 'neptune', 'pluto']

        def add_planet_group(group_name, planets):
            nonlocal html
            html += f"<tr><td colspan='3'><strong>{group_name}:</strong></td></tr>"
            for planet in planets:
                if planet in obj.planetary_data:
                    data = obj.planetary_data[planet]
                    sign = data.get('sign', 'N/A')
                    degree = data.get('degree', 'N/A')
                    html += f"<tr>"
                    html += f"<td style='padding-left: 20px;'>{planet.title()}:</td>"
                    html += f"<td>{sign}</td>"
                    html += f"<td>{degree}°</td>"
                    html += f"</tr>"

        add_planet_group("Personal Planets", personal_planets)
        add_planet_group("Social Planets", social_planets)
        add_planet_group("Outer Planets", outer_planets)

        html += "</table>"

        # Add retrograde info if available
        retrograde_planets = [
            p for p, data in obj.planetary_data.items()
            if data.get('retrograde', False)
        ]
        if retrograde_planets:
            html += f"<p><strong>Retrograde:</strong> {', '.join(retrograde_planets).title()}</p>"

        html += "</div>"
        return format_html(html)

    data_summary.short_description = "Data Summary"

    def cache_status(self, obj):
        """Show cache status for this snapshot"""
        cache_key = f"{CACHE_KEY_PREFIX}{obj.date}_{obj.timezone}"
        is_cached = cache.get(cache_key)

        if is_cached:
            return format_html(
                '<span style="color: orange;">⚠️ Data fetch in progress (cache locked)</span>'
            )
        return format_html('<span style="color: green;">✅ Cache available for refresh</span>')

    # Custom Actions
    def refresh_planetary_data(self, request, queryset):
        """Refresh planetary data for selected snapshots"""
        from deep_dive.services.mystical.astronomical_svc import AstronomicalService

        refreshed = 0
        failed = 0

        for snapshot in queryset:
            cache_key = f"{CACHE_KEY_PREFIX}{snapshot.date}_{snapshot.timezone}"

            # Prevent concurrent refreshes
            if cache.get(cache_key):
                self.message_user(
                    request,
                    f"Skipping {snapshot.date} ({snapshot.timezone}) - refresh already in progress",
                    messages.WARNING
                )
                continue

            # Set cache lock (30 seconds timeout)
            cache.set(cache_key, True, 30)

            try:
                astro_service = AstronomicalService()
                new_data = astro_service.get_daily_planetary_summary(snapshot.timezone)
                snapshot.planetary_data = new_data
                snapshot.save()
                refreshed += 1

                # Clear cache lock
                cache.delete(cache_key)

            except Exception as e:
                failed += 1
                self.message_user(
                    request,
                    f"Failed to refresh {snapshot.date} ({snapshot.timezone}): {str(e)}",
                    messages.ERROR
                )
                cache.delete(cache_key)

        if refreshed > 0:
            self.message_user(
                request,
                f"Successfully refreshed {refreshed} snapshot(s). {failed} failed.",
                messages.SUCCESS if failed == 0 else messages.WARNING
            )

    refresh_planetary_data.short_description = "Refresh planetary data from astrology service"

    def export_as_json(self, request, queryset):
        """Export selected snapshots as JSON (simplified example)"""
        import json
        from django.http import HttpResponse

        data = []
        for snapshot in queryset:
            data.append({
                'date': snapshot.date.isoformat(),
                'timezone': snapshot.timezone,
                'planetary_data': snapshot.planetary_data,
                'created_at': snapshot.created_at.isoformat(),
            })

        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="planetary_snapshots.json"'
        return response

    export_as_json.short_description = "Export selected as JSON"

    # Custom save logic
    def save_model(self, request, obj, form, change):
        """Custom save logic to ensure data integrity"""
        if not obj.planetary_data:
            from deep_dive.services.mystical.astronomical_svc import AstronomicalService

            try:
                astro_service = AstronomicalService()
                obj.planetary_data = astro_service.get_daily_planetary_summary(obj.timezone)
                self.message_user(
                    request,
                    "Planetary data fetched automatically",
                    messages.INFO
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to fetch planetary data: {str(e)}",
                    messages.ERROR
                )

        super().save_model(request, obj, form, change)

    # Admin list configuration
    list_per_page = 25
    list_max_show_all = 100

    def get_queryset(self, request):
        """Custom queryset to optimize database queries"""
        return super().get_queryset(request).select_related()


# @admin.register(JournalMode)
# class JournalModeAdmin(admin.ModelAdmin):
#     list_display = ('name', 'is_premium', 'is_active', 'created_at')
#     list_filter = ('is_premium', 'is_active')
#
#
# @admin.register(DailyContent)
# class DailyContentAdmin(admin.ModelAdmin):
#     list_display = ('mode', 'date', 'content_type', 'personalization_key', 'content_data', 'created_at' )

