# deep_dive/models.py
"""
Fixed AIReading model with proper field types and data handling
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AIReading(models.Model):
    """
    Stores AI-generated astrological readings for a user.
    Three separate reading types with type-specific data.
    OneToOne relationship - one record per user with all reading types.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='ai_readings',
        help_text="User who owns these readings"
    )

    # ========================================
    # DAILY OVERVIEW READING FIELDS
    # ========================================
    daily_overview_text = models.TextField(
        blank=True,
        help_text="Daily overview reading content"
    )
    daily_overview_transits = models.JSONField(
        default=list,
        help_text="Top transits for daily overview"
    )
    daily_overview_moon_phase = models.JSONField(
        default=dict,
        blank=True,
        help_text="Moon phase data (phase, emoji, illumination, description)"
    )
    daily_overview_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When daily overview was generated"
    )

    # NEW: Daily Overview cosmic context
    daily_overview_element_dist = models.JSONField(
        default=dict,
        blank=True,
        help_text="Element distribution in current sky"
    )
    daily_overview_modality_dist = models.JSONField(
        default=dict,
        blank=True,
        help_text="Modality distribution"
    )
    daily_overview_sign_concentrations = models.JSONField(
        default=list,
        blank=True,
        help_text="Signs with multiple planets"
    )
    daily_overview_sky_conjunctions = models.JSONField(
        default=list,
        blank=True,
        help_text="Current planetary conjunctions in sky"
    )
    daily_overview_cosmic_weather = models.TextField(
        blank=True,
        help_text="Cosmic weather description"
    )

    # ========================================
    # TRANSIT FOCUS READING FIELDS
    # ========================================
    transit_focus_text = models.TextField(
        blank=True,
        help_text="Transit focus reading content"
    )
    transit_focus_transits = models.JSONField(
        default=list,
        help_text="Top transits for transit focus"
    )
    transit_focus_moon_phase = models.CharField(
        max_length=100,
        blank=True,
        help_text="Moon phase name only"
    )
    transit_focus_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When transit focus was generated"
    )

    # NEW: Full transit interpretations
    transit_focus_transit_summaries = models.JSONField(
        default=list,
        blank=True,
        help_text="Full transit interpretations with psychological depth"
    )

    # ========================================
    # ELEMENT WISDOM READING FIELDS
    # ========================================
    element_wisdom_text = models.TextField(
        blank=True,
        help_text="Element wisdom reading content"
    )
    element_wisdom_transits = models.JSONField(
        default=list,
        help_text="Empty list - element wisdom doesn't use transits"
    )
    element_wisdom_moon_phase = models.JSONField(
        default=dict,
        blank=True,
        help_text="Moon phase data (minimal)"
    )
    element_wisdom_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When element wisdom was generated"
    )

    # NEW: Elemental analysis data
    element_wisdom_current_elements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Current sky element distribution and analysis"
    )
    element_wisdom_natal_elements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Natal chart element distribution"
    )
    element_wisdom_comparison = models.JSONField(
        default=dict,
        blank=True,
        help_text="Comparison between natal and current elements"
    )

    # ========================================
    # GENERAL METADATA
    # ========================================
    cosmic_weather = models.TextField(
        blank=True,
        help_text="General cosmic conditions description"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When record was first created"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update to any reading"
    )

    class Meta:
        verbose_name = 'AI Reading Collection'
        verbose_name_plural = 'AI Reading Collections'
        indexes = [
            models.Index(fields=['-daily_overview_generated_at']),
            models.Index(fields=['-transit_focus_generated_at']),
            models.Index(fields=['-element_wisdom_generated_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - AI Readings"

    def get_reading(self, reading_type):
        """Get specific reading data by type."""
        if reading_type == 'daily_overview':
            return {
                'reading_type': 'daily_overview',
                'reading_text': self.daily_overview_text,
                'top_transits': self.daily_overview_transits,
                'moon_phase': self.daily_overview_moon_phase,
                'generated_at': self.daily_overview_generated_at,
                'transits_analyzed': len(self.daily_overview_transits),
                'element_distribution': self.daily_overview_element_dist,
                'modality_distribution': self.daily_overview_modality_dist,
                'sign_concentrations': self.daily_overview_sign_concentrations,
                'sky_conjunctions': self.daily_overview_sky_conjunctions,
                'cosmic_weather': self.daily_overview_cosmic_weather,
            }
        elif reading_type == 'transit_focus':
            return {
                'reading_type': 'transit_focus',
                'reading_text': self.transit_focus_text,
                'top_transits': self.transit_focus_transits,
                'moon_phase': self.transit_focus_moon_phase,
                'generated_at': self.transit_focus_generated_at,
                'transits_analyzed': len(self.transit_focus_transits),
                'transit_summaries': self.transit_focus_transit_summaries,
            }
        elif reading_type == 'element_wisdom':
            return {
                'reading_type': 'element_wisdom',
                'reading_text': self.element_wisdom_text,
                'top_transits': self.element_wisdom_transits,
                'moon_phase': self.element_wisdom_moon_phase,
                'generated_at': self.element_wisdom_generated_at,
                'transits_analyzed': len(self.element_wisdom_transits),
                'current_elements': self.element_wisdom_current_elements,
                'natal_elements': self.element_wisdom_natal_elements,
                'elemental_weather_comparison': self.element_wisdom_comparison,
            }
        return None

    def has_reading_type(self, reading_type):
        """Check if a specific reading type has been generated"""
        if reading_type == 'daily_overview':
            return bool(
                self.daily_overview_text and self.daily_overview_text.strip() and self.daily_overview_generated_at)
        elif reading_type == 'transit_focus':
            return bool(self.transit_focus_text and self.transit_focus_text.strip() and self.transit_focus_generated_at)
        elif reading_type == 'element_wisdom':
            return bool(
                self.element_wisdom_text and self.element_wisdom_text.strip() and self.element_wisdom_generated_at)
        return False

    def get_available_reading_types(self):
        """Get list of reading types that have been generated"""
        available = []
        if self.has_reading_type('daily_overview'):
            available.append('daily_overview')
        if self.has_reading_type('transit_focus'):
            available.append('transit_focus')
        if self.has_reading_type('element_wisdom'):
            available.append('element_wisdom')
        return available

    def update_reading(self, reading_type, reading_data):
        """
        Update reading data for a specific type.
        FIXED: Properly handle dict vs string fields and timezone-aware datetimes.
        """
        from django.utils import timezone as tz

        # Get generated_at timestamp with proper timezone handling
        generated_at = reading_data.get('generated_at')
        if generated_at:
            # If it's a string, parse it
            if isinstance(generated_at, str):
                from django.utils.dateparse import parse_datetime
                generated_at = parse_datetime(generated_at)
            # Make it timezone-aware if it isn't
            if generated_at and generated_at.tzinfo is None:
                generated_at = tz.make_aware(generated_at)

        if reading_type == 'daily_overview':
            self.daily_overview_text = reading_data.get('reading_text', '')
            self.daily_overview_transits = reading_data.get('top_transits', [])
            self.daily_overview_generated_at = generated_at

            # Cosmic context data (NEW)
            self.daily_overview_moon_phase = reading_data.get('moon_phase', {})  # Store as dict
            self.daily_overview_element_dist = reading_data.get('element_distribution', {})
            self.daily_overview_modality_dist = reading_data.get('modality_distribution', {})
            self.daily_overview_sign_concentrations = reading_data.get('sign_concentrations', [])
            self.daily_overview_sky_conjunctions = reading_data.get('sky_conjunctions', [])
            self.daily_overview_cosmic_weather = reading_data.get('cosmic_weather', '')

        elif reading_type == 'transit_focus':
            self.transit_focus_text = reading_data.get('reading_text', '')
            self.transit_focus_transits = reading_data.get('top_transits', [])
            self.transit_focus_transit_summaries = reading_data.get('transit_summaries', [])
            self.transit_focus_generated_at = generated_at

            # Extract just the phase name as string
            moon_data = reading_data.get('moon_phase', '')
            if isinstance(moon_data, dict):
                self.transit_focus_moon_phase = moon_data.get('phase', '')
            else:
                self.transit_focus_moon_phase = str(moon_data)

        elif reading_type == 'element_wisdom':
            self.element_wisdom_text = reading_data.get('reading_text', '')
            self.element_wisdom_transits = reading_data.get('top_transits', [])  # Empty list
            self.element_wisdom_generated_at = generated_at

            # Elemental analysis data (NEW)
            self.element_wisdom_moon_phase = reading_data.get('moon_phase', {})
            self.element_wisdom_current_elements = reading_data.get('current_elements', {})
            self.element_wisdom_natal_elements = reading_data.get('natal_elements', {})
            self.element_wisdom_comparison = reading_data.get('elemental_weather_comparison', {})

        self.save()

    def is_today(self, reading_type):
        """Check if specific reading was generated today."""
        from datetime import date
        generated_at = None

        if reading_type == 'daily_overview':
            generated_at = self.daily_overview_generated_at
        elif reading_type == 'transit_focus':
            generated_at = self.transit_focus_generated_at
        elif reading_type == 'element_wisdom':
            generated_at = self.element_wisdom_generated_at

        if generated_at:
            return generated_at.date() == date.today()
        return False

    def get_latest_reading(self):
        """Get the most recently generated reading of any type."""
        readings = []

        if self.daily_overview_generated_at:
            readings.append(('daily_overview', self.daily_overview_generated_at))
        if self.transit_focus_generated_at:
            readings.append(('transit_focus', self.transit_focus_generated_at))
        if self.element_wisdom_generated_at:
            readings.append(('element_wisdom', self.element_wisdom_generated_at))

        if readings:
            latest_type, _ = max(readings, key=lambda x: x[1])
            return self.get_reading(latest_type)
        return None

    def get_moon_phase_display(self, reading_type):
        """Helper to display moon phase nicely regardless of storage format."""
        if reading_type == 'daily_overview':
            moon = self.daily_overview_moon_phase
            if isinstance(moon, dict):
                return f"{moon.get('emoji', '🌙')} {moon.get('phase', 'Unknown')}"
            return str(moon)
        elif reading_type == 'transit_focus':
            return self.transit_focus_moon_phase or 'Unknown'
        elif reading_type == 'element_wisdom':
            moon = self.element_wisdom_moon_phase
            if isinstance(moon, dict):
                return f"{moon.get('emoji', '🌙')} {moon.get('phase', 'Unknown')}"
            return str(moon)
        return 'Unknown'


class TarotCardDraw(models.Model):
    """Records of user's daily tarot card draws"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tarot_draws')
    card_number = models.CharField(max_length=50)
    card_name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=5)
    keywords = models.CharField(max_length=200)
    interpretation = models.TextField()
    astro_context = models.TextField(blank=True)
    natal_insight = models.TextField(blank=True)
    drawn_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-drawn_at']
        indexes = [
            models.Index(fields=['-drawn_at']),
            models.Index(fields=['user', '-drawn_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.card_name} - {self.drawn_at.date()}"