# deep_dive/models.py
# Replace the AIReading model with this simpler version

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AIReading(models.Model):
    """
    Stores AI-generated astrological readings for a user.
    Three separate fields for three reading types.
    OneToOne relationship - one record per user with all reading types.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='ai_readings',
        help_text="User who owns these readings"
    )

    # Daily Overview Reading
    daily_overview_text = models.TextField(
        blank=True,
        help_text="Daily overview reading content"
    )
    daily_overview_transits = models.JSONField(
        default=list,
        help_text="Top transits for daily overview"
    )
    daily_overview_moon_phase = models.CharField(
        max_length=50,
        blank=True,
        help_text="Moon phase during daily overview"
    )
    daily_overview_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When daily overview was generated"
    )
    daily_overview_transit_summaries = models.JSONField(default=list, blank=True)

    # Transit Focus Reading
    transit_focus_text = models.TextField(
        blank=True,
        help_text="Transit focus reading content"
    )
    transit_focus_transits = models.JSONField(
        default=list,
        help_text="Top transits for transit focus"
    )
    transit_focus_moon_phase = models.CharField(
        max_length=50,
        blank=True,
        help_text="Moon phase during transit focus"
    )
    transit_focus_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When transit focus was generated"
    )
    transit_focus_transit_summaries = models.JSONField(default=list, blank=True)

    # Element Wisdom Reading
    element_wisdom_text = models.TextField(
        blank=True,
        help_text="Element wisdom reading content"
    )
    element_wisdom_transits = models.JSONField(
        default=list,
        help_text="Top transits for element wisdom"
    )
    element_wisdom_moon_phase = models.CharField(
        max_length=50,
        blank=True,
        help_text="Moon phase during element wisdom"
    )
    element_wisdom_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When element wisdom was generated"
    )
    element_wisdom_transit_summaries = models.JSONField(default=list, blank=True)

    # General metadata
    cosmic_weather = models.TextField(
        blank=True,
        help_text="General cosmic conditions"
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
                'transit_summaries': self.daily_overview_transit_summaries,
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
                'transit_summaries': self.element_wisdom_transit_summaries,
            }
        return None

    def has_reading_type(self, reading_type):
        """Check if a specific reading type has been generated"""
        if reading_type == 'daily_overview':
            return bool(self.daily_overview_text.strip() and self.daily_overview_generated_at)
        elif reading_type == 'transit_focus':
            return bool(self.transit_focus_text.strip() and self.transit_focus_generated_at)
        elif reading_type == 'element_wisdom':
            return bool(self.element_wisdom_text.strip() and self.element_wisdom_generated_at)
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
        """Update specific reading by type."""
        from django.utils import timezone

        if reading_type == 'daily_overview':
            self.daily_overview_text = reading_data['reading_text']
            self.daily_overview_transits = reading_data['top_transits']
            self.daily_overview_transit_summaries = reading_data.get('transit_summaries', [])  # ADD THIS
            self.daily_overview_moon_phase = reading_data['moon_phase']
            self.daily_overview_generated_at = timezone.now()
        elif reading_type == 'transit_focus':
            self.transit_focus_text = reading_data['reading_text']
            self.transit_focus_transits = reading_data['top_transits']
            self.transit_focus_transit_summaries = reading_data.get('transit_summaries', [])  # ADD THIS
            self.transit_focus_moon_phase = reading_data['moon_phase']
            self.transit_focus_generated_at = timezone.now()
        elif reading_type == 'element_wisdom':
            self.element_wisdom_text = reading_data['reading_text']
            self.element_wisdom_transits = reading_data['top_transits']
            self.element_wisdom_transit_summaries = reading_data.get('transit_summaries', [])  # ADD THIS
            self.element_wisdom_moon_phase = reading_data['moon_phase']
            self.element_wisdom_generated_at = timezone.now()

        self.cosmic_weather = reading_data.get('cosmic_weather', '')
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

    def __str__(self):
        return f"{self.user.username} - {self.card_name} - {self.drawn_at.date()}"