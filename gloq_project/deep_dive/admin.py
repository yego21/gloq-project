# deep_dive/admin.py - ENHANCED VERSION WITH TAROT
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import date
from .models import AIReading, TarotCardDraw


@admin.register(AIReading)
class AIReadingAdmin(admin.ModelAdmin):
    # Update list display to show information for all reading types
    list_display = [
        'user',
        'reading_status',
        'total_transits',
        'latest_moon_phase',
        'is_any_reading_today',
        'last_updated',
    ]

    list_filter = [
        'daily_overview_generated_at',
        'transit_focus_generated_at',
        'element_wisdom_generated_at',
    ]

    search_fields = [
        'user__username',
        'user__email',
        'daily_overview_text',
        'transit_focus_text',
        'element_wisdom_text',
    ]

    # Fields that should be read-only in the admin
    readonly_fields = [
        'user',
        'reading_status_detailed',
        'formatted_daily_reading',
        'formatted_transit_reading',
        'formatted_element_reading',
        'all_transits_display',
        'cosmic_weather',
        'created_at',
        'updated_at',
    ]

    # Reorganize fieldsets to display all three reading types clearly
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'reading_status_detailed', 'created_at', 'updated_at')
        }),
        ('Daily Overview Reading', {
            'fields': ('formatted_daily_reading', 'daily_overview_moon_phase', 'daily_overview_generated_at'),
            'classes': ('wide',),
            'description': 'Use admin actions below to delete this specific reading type.'
        }),
        ('Transit Focus Reading', {
            'fields': ('formatted_transit_reading', 'transit_focus_moon_phase', 'transit_focus_generated_at'),
            'classes': ('wide',),
            'description': 'Use admin actions below to delete this specific reading type.'
        }),
        ('Element Wisdom Reading', {
            'fields': ('formatted_element_reading', 'element_wisdom_moon_phase', 'element_wisdom_generated_at'),
            'classes': ('wide',),
            'description': 'Use admin actions below to delete this specific reading type.'
        }),
        ('Cosmic Context', {
            'fields': ('cosmic_weather', 'all_transits_display'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize database queries by prefetching related user data."""
        return super().get_queryset(request).select_related('user')

    # ========== LIST DISPLAY METHODS ==========

    def reading_status(self, obj):
        """Show which readings are present with color-coded badges."""
        badges = []

        # Daily Overview badge
        if obj.daily_overview_text:
            badges.append(
                '<span style="background-color: #fbbf24; color: black; padding: 2px 8px; border-radius: 10px; font-size: 10px;">📅 Daily</span>')

        # Transit Focus badge
        if obj.transit_focus_text:
            badges.append(
                '<span style="background-color: #a78bfa; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px;">🔄 Transit</span>')

        # Element Wisdom badge
        if obj.element_wisdom_text:
            badges.append(
                '<span style="background-color: #60a5fa; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px;">⚛️ Element</span>')

        if not badges:
            return format_html('<span style="color: #9ca3af;">No readings</span>')

        return format_html(' '.join(badges))

    reading_status.short_description = 'Readings'

    def total_transits(self, obj):
        """Calculate total number of transits across all reading types."""
        total = (len(obj.daily_overview_transits) +
                 len(obj.transit_focus_transits) +
                 len(obj.element_wisdom_transits))

        if total > 0:
            return format_html('<span style="color: #10b981; font-weight: 600;">{}</span>', total)
        return format_html('<span style="color: #6b7280;">0</span>')

    total_transits.short_description = 'Transits'

    def latest_moon_phase(self, obj):
        """Show the most recent moon phase from any reading."""
        # Get all moon phases that exist, ordered by recency
        phases = []
        if obj.element_wisdom_generated_at and obj.element_wisdom_moon_phase:
            phases.append((obj.element_wisdom_generated_at, obj.element_wisdom_moon_phase))
        if obj.transit_focus_generated_at and obj.transit_focus_moon_phase:
            phases.append((obj.transit_focus_generated_at, obj.transit_focus_moon_phase))
        if obj.daily_overview_generated_at and obj.daily_overview_moon_phase:
            phases.append((obj.daily_overview_generated_at, obj.daily_overview_moon_phase))

        if phases:
            # Return the moon phase from the most recent reading
            latest_phase = max(phases, key=lambda x: x[0])[1]
            return format_html('<span style="font-weight: 600;">{}</span>', latest_phase)
        return format_html('<span style="color: #9ca3af;">—</span>')

    latest_moon_phase.short_description = 'Moon Phase'

    def is_any_reading_today(self, obj):
        """Check if any reading was generated today."""
        today = date.today()

        readings_today = [
            obj.daily_overview_generated_at.date() == today if obj.daily_overview_generated_at else False,
            obj.transit_focus_generated_at.date() == today if obj.transit_focus_generated_at else False,
            obj.element_wisdom_generated_at.date() == today if obj.element_wisdom_generated_at else False
        ]

        if any(readings_today):
            return format_html('<span style="color: #10b981; font-weight: 600;">✓ Today</span>')

        # Show the date of the most recent reading
        all_dates = [d for d in
                     [obj.daily_overview_generated_at, obj.transit_focus_generated_at, obj.element_wisdom_generated_at]
                     if d]
        if all_dates:
            latest = max(all_dates)
            return format_html('<span style="color: #6b7280;">{}</span>', latest.strftime('%b %d'))

        return format_html('<span style="color: #9ca3af;">—</span>')

    is_any_reading_today.short_description = 'Current'

    def last_updated(self, obj):
        """Show when any part of the record was last updated."""
        return obj.updated_at.strftime('%Y-%m-%d %H:%M')

    last_updated.short_description = 'Last Updated'

    # ========== READONLY FIELD METHODS ==========

    def reading_status_detailed(self, obj):
        """Detailed reading status for the change form."""
        status_lines = []

        # Daily Overview status
        if obj.daily_overview_text:
            date_str = obj.daily_overview_generated_at.strftime(
                '%b %d, %Y %H:%M') if obj.daily_overview_generated_at else 'Unknown'
            status_lines.append(f"📅 <strong>Daily Overview</strong>: Generated on {date_str}")
        else:
            status_lines.append("📅 <strong>Daily Overview</strong>: <span style='color: #9ca3af;'>Not generated</span>")

        # Transit Focus status
        if obj.transit_focus_text:
            date_str = obj.transit_focus_generated_at.strftime(
                '%b %d, %Y %H:%M') if obj.transit_focus_generated_at else 'Unknown'
            status_lines.append(f"🔄 <strong>Transit Focus</strong>: Generated on {date_str}")
        else:
            status_lines.append("🔄 <strong>Transit Focus</strong>: <span style='color: #9ca3af;'>Not generated</span>")

        # Element Wisdom status
        if obj.element_wisdom_text:
            date_str = obj.element_wisdom_generated_at.strftime(
                '%b %d, %Y %H:%M') if obj.element_wisdom_generated_at else 'Unknown'
            status_lines.append(f"⚛️ <strong>Element Wisdom</strong>: Generated on {date_str}")
        else:
            status_lines.append(
                "⚛️ <strong>Element Wisdom</strong>: <span style='color: #9ca3af;'>Not generated</span>")

        return format_html('<div style="line-height: 1.8;">{}</div>', '<br>'.join(status_lines))

    reading_status_detailed.short_description = 'Reading Status'

    def formatted_daily_reading(self, obj):
        """Format the daily overview reading for display."""
        return self._format_reading_text(obj.daily_overview_text, "Daily Overview")

    formatted_daily_reading.short_description = 'Daily Overview Reading'

    def formatted_transit_reading(self, obj):
        """Format the transit focus reading for display."""
        return self._format_reading_text(obj.transit_focus_text, "Transit Focus")

    formatted_transit_reading.short_description = 'Transit Focus Reading'

    def formatted_element_reading(self, obj):
        """Format the element wisdom reading for display."""
        return self._format_reading_text(obj.element_wisdom_text, "Element Wisdom")

    formatted_element_reading.short_description = 'Element Wisdom Reading'

    def _format_reading_text(self, text, title):
        """Helper method to format reading text consistently."""
        if not text:
            return format_html('<div style="color: #9ca3af; font-style: italic;">No {} reading generated yet.</div>',
                               title)

        return format_html(
            '<div style="background-color: #f3f4f6; padding: 16px; '
            'border-radius: 8px; border-left: 4px solid #6366f1; '
            'white-space: pre-wrap; line-height: 1.6; max-width: 800px;">{}</div>',
            text
        )

    def all_transits_display(self, obj):
        """Display transits from all reading types."""
        transits_data = [
            ('Daily Overview', obj.daily_overview_transits),
            ('Transit Focus', obj.transit_focus_transits),
            ('Element Wisdom', obj.element_wisdom_transits)
        ]

        html_parts = []

        for reading_type, transits in transits_data:
            if transits:
                html_parts.append(
                    f'<h4 style="margin-top: 12px; margin-bottom: 8px; color: #374151;">{reading_type} Transits</h4>')
                html_parts.append('<ul style="line-height: 1.8; list-style: none; padding: 0;">')

                for transit in transits:
                    quality_colors = {
                        'intense': '#ef4444', 'harmonious': '#10b981', 'challenging': '#f59e0b',
                        'flowing': '#3b82f6', 'dynamic': '#8b5cf6',
                    }
                    color = quality_colors.get(transit.get('quality', ''), '#6b7280')

                    html_parts.append(format_html(
                        '<li style="margin-bottom: 8px; padding: 8px; background-color: #f9fafb; '
                        'border-radius: 4px; border-left: 3px solid {};">'
                        '<strong>{}</strong> in {} '
                        '<span style="color: {}; font-weight: 600;">{}</span> '
                        '<strong>{}</strong> in {} '
                        '<span style="color: #6b7280; font-size: 0.85em;">({}° orb, strength: {})</span>'
                        '</li>',
                        color,
                        transit.get('transit_planet', 'Unknown'),
                        transit.get('transit_sign', ''),
                        color,
                        transit.get('aspect_type', ''),
                        transit.get('natal_planet', 'Unknown'),
                        transit.get('natal_sign', ''),
                        transit.get('orb', 0),
                        transit.get('strength', 0)
                    ).__str__())

                html_parts.append('</ul>')

        if not html_parts:
            return format_html('<em style="color: #9ca3af;">No transits recorded in any reading</em>')

        return format_html(''.join(html_parts))

    all_transits_display.short_description = 'All Transits'

    # ========== ADMIN PERMISSIONS ==========

    def has_add_permission(self, request):
        """Disable manual adding - readings are generated by users."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup."""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow changes so actions work, but fields are read-only."""
        return True

    # ========== CUSTOM ACTIONS ==========

    actions = [
        'delete_daily_overview_reading',
        'delete_transit_focus_reading',
        'delete_element_wisdom_reading',
        'delete_all_readings',
        'show_reading_summary',
    ]

    def delete_daily_overview_reading(self, request, queryset):
        """Delete only the Daily Overview reading type from selected records."""
        count = 0
        for reading in queryset:
            if reading.daily_overview_text:
                reading.daily_overview_text = ''
                reading.daily_overview_transits = []
                reading.daily_overview_moon_phase = ''
                reading.daily_overview_generated_at = None
                reading.save()
                count += 1

        self.message_user(
            request,
            f"Successfully deleted Daily Overview reading from {count} record(s).",
            level='success' if count > 0 else 'warning'
        )

    delete_daily_overview_reading.short_description = "🗑️ Delete Daily Overview readings"

    def delete_transit_focus_reading(self, request, queryset):
        """Delete only the Transit Focus reading type from selected records."""
        count = 0
        for reading in queryset:
            if reading.transit_focus_text:
                reading.transit_focus_text = ''
                reading.transit_focus_transits = []
                reading.transit_focus_moon_phase = ''
                reading.transit_focus_generated_at = None
                reading.save()
                count += 1

        self.message_user(
            request,
            f"Successfully deleted Transit Focus reading from {count} record(s).",
            level='success' if count > 0 else 'warning'
        )

    delete_transit_focus_reading.short_description = "🗑️ Delete Transit Focus readings"

    def delete_element_wisdom_reading(self, request, queryset):
        """Delete only the Element Wisdom reading type from selected records."""
        count = 0
        for reading in queryset:
            if reading.element_wisdom_text:
                reading.element_wisdom_text = ''
                reading.element_wisdom_transits = []
                reading.element_wisdom_moon_phase = ''
                reading.element_wisdom_generated_at = None
                reading.save()
                count += 1

        self.message_user(
            request,
            f"Successfully deleted Element Wisdom reading from {count} record(s).",
            level='success' if count > 0 else 'warning'
        )

    delete_element_wisdom_reading.short_description = "🗑️ Delete Element Wisdom readings"

    def delete_all_readings(self, request, queryset):
        """Delete all reading types from selected records (but keep the record itself)."""
        count = 0
        for reading in queryset:
            has_any = (reading.daily_overview_text or
                       reading.transit_focus_text or
                       reading.element_wisdom_text)

            if has_any:
                # Clear Daily Overview
                reading.daily_overview_text = ''
                reading.daily_overview_transits = []
                reading.daily_overview_moon_phase = ''
                reading.daily_overview_generated_at = None

                # Clear Transit Focus
                reading.transit_focus_text = ''
                reading.transit_focus_transits = []
                reading.transit_focus_moon_phase = ''
                reading.transit_focus_generated_at = None

                # Clear Element Wisdom
                reading.element_wisdom_text = ''
                reading.element_wisdom_transits = []
                reading.element_wisdom_moon_phase = ''
                reading.element_wisdom_generated_at = None

                # Clear cosmic weather
                reading.cosmic_weather = ''

                reading.save()
                count += 1

        self.message_user(
            request,
            f"Successfully cleared all readings from {count} record(s). User records remain intact.",
            level='success' if count > 0 else 'warning'
        )

    delete_all_readings.short_description = "🗑️ Delete ALL readings (keep user record)"

    def show_reading_summary(self, request, queryset):
        """Show summary of readings for selected records."""
        for reading in queryset:
            readings = []
            if reading.daily_overview_text:
                readings.append('Daily')
            if reading.transit_focus_text:
                readings.append('Transit')
            if reading.element_wisdom_text:
                readings.append('Element')

            readings_count = len(readings)
            readings_str = ', '.join(readings) if readings else 'None'

            self.message_user(
                request,
                f"📊 User: {reading.user.username} | Readings: {readings_count}/3 ({readings_str}) | "
                f"Last updated: {reading.updated_at.strftime('%b %d, %Y %H:%M')}"
            )

    show_reading_summary.short_description = "📊 Show reading summary"

    # ========== CUSTOM STYLING ==========

    class Media:
        css = {
            'all': ('admin/css/custom_ai_reading_admin.css',)
        }


@admin.register(TarotCardDraw)
class TarotCardDrawAdmin(admin.ModelAdmin):
    """Admin interface for Tarot Card Draws"""

    list_display = [
        'user',
        'card_display',
        'keywords',
        'drawn_at',
        'is_today_draw',
    ]

    list_filter = [
        'drawn_at',
        'card_name',
    ]

    search_fields = [
        'user__username',
        'user__email',
        'card_name',
        'keywords',
        'interpretation',
    ]

    readonly_fields = [
        'user',
        'card_display_detailed',
        'formatted_interpretation',
        'formatted_astro_context',
        'formatted_natal_insight',
        'drawn_at',
    ]

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'drawn_at')
        }),
        ('Card Information', {
            'fields': ('card_display_detailed', 'keywords')
        }),
        ('Interpretation', {
            'fields': ('formatted_interpretation',),
            'classes': ('wide',)
        }),
        ('Astrological Context', {
            'fields': ('formatted_astro_context',),
            'classes': ('wide',)
        }),
        ('Natal Insight', {
            'fields': ('formatted_natal_insight',),
            'classes': ('wide',)
        }),
    )

    def get_queryset(self, request):
        """Optimize database queries by prefetching related user data."""
        return super().get_queryset(request).select_related('user')

    # ========== LIST DISPLAY METHODS ==========

    def card_display(self, obj):
        """Display card with emoji and name in list view."""
        return format_html(
            '<span style="font-size: 16px;">{} <strong>{}</strong></span>',
            obj.emoji,
            obj.card_name
        )

    card_display.short_description = 'Card'

    def is_today_draw(self, obj):
        """Check if the card was drawn today."""
        today = timezone.now().date()
        if obj.drawn_at.date() == today:
            return format_html('<span style="color: #10b981; font-weight: 600;">✓ Today</span>')
        return format_html('<span style="color: #6b7280;">{}</span>', obj.drawn_at.strftime('%b %d'))

    is_today_draw.short_description = 'Drawn'

    # ========== READONLY FIELD METHODS ==========

    def card_display_detailed(self, obj):
        """Detailed card display for change form."""
        return format_html(
            '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            'padding: 20px; border-radius: 12px; color: white; text-align: center; margin: 10px 0;">'
            '<span style="font-size: 32px; display: block; margin-bottom: 8px;">{}</span>'
            '<h3 style="margin: 0; font-size: 24px;">{}</h3>'
            '<p style="margin: 8px 0 0 0; opacity: 0.9;">Card #{}</p>'
            '</div>',
            obj.emoji,
            obj.card_name,
            obj.card_number
        )

    card_display_detailed.short_description = 'Tarot Card'

    def formatted_interpretation(self, obj):
        """Format the interpretation for display."""
        return self._format_text_field(obj.interpretation, "Interpretation")

    formatted_interpretation.short_description = 'Interpretation'

    def formatted_astro_context(self, obj):
        """Format the astrological context for display."""
        return self._format_text_field(obj.astro_context, "Astrological Context", "No astrological context provided.")

    formatted_astro_context.short_description = 'Astrological Context'

    def formatted_natal_insight(self, obj):
        """Format the natal insight for display."""
        return self._format_text_field(obj.natal_insight, "Natal Insight", "No natal insight provided.")

    formatted_natal_insight.short_description = 'Natal Insight'

    def _format_text_field(self, text, title, empty_message="No content available."):
        """Helper method to format text fields consistently."""
        if not text:
            return format_html(
                '<div style="color: #9ca3af; font-style: italic; padding: 16px; '
                'background-color: #f3f4f6; border-radius: 8px;">{}</div>',
                empty_message
            )

        return format_html(
            '<div style="background-color: #f3f4f6; padding: 16px; '
            'border-radius: 8px; border-left: 4px solid #8b5cf6; '
            'white-space: pre-wrap; line-height: 1.6;">{}</div>',
            text
        )

    # ========== ADMIN PERMISSIONS ==========

    def has_add_permission(self, request):
        """Disable manual adding - tarot draws are generated by users."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup."""
        return True

    def has_change_permission(self, request, obj=None):
        """Allow changes so actions work, but fields are read-only."""
        return True

    # ========== CUSTOM ACTIONS ==========

    actions = [
        'delete_old_tarot_draws',
        'export_tarot_readings',
    ]

    def delete_old_tarot_draws(self, request, queryset):
        """Delete tarot draws older than 30 days."""
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        old_draws = queryset.filter(drawn_at__lt=cutoff_date)
        count = old_draws.count()

        old_draws.delete()

        self.message_user(
            request,
            f"Successfully deleted {count} tarot draw(s) older than 30 days.",
            level='success' if count > 0 else 'warning'
        )

    delete_old_tarot_draws.short_description = "🗑️ Delete tarot draws older than 30 days"

    def export_tarot_readings(self, request, queryset):
        """Export selected tarot readings as summary."""
        for draw in queryset:
            self.message_user(
                request,
                f"🔮 {draw.user.username} drew {draw.card_name} {draw.emoji} "
                f"on {draw.drawn_at.strftime('%b %d, %Y')}\n"
                f"Keywords: {draw.keywords}\n"
                f"Interpretation: {draw.interpretation[:100]}...",
                level='info'
            )

    export_tarot_readings.short_description = "📤 Export tarot readings summary"