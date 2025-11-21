from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import pytz
from modes.models import Mode
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_mode = models.ForeignKey(
        Mode,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        default='2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    timezone = models.CharField(
        max_length=100,
        choices=[(tz, tz) for tz in pytz.all_timezones],
        default='UTC',
        blank=True,
        null=True,
    )
    selected_mode = models.ForeignKey(
        Mode, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='users'
    )



    # ===== AI COMMENTARY SETTINGS =====
    # Controls whether instant AI commentary is enabled for this user
    enable_instant_commentary = models.BooleanField(
        default=True,
        verbose_name="Enable Instant AI Insights",
        help_text="Show AI-generated commentary immediately after creating journal entries"
    )

    # Maximum number of commentaries to show per day (prevents overload)
    max_daily_commentaries = models.IntegerField(
        default=3,
        verbose_name="Max Daily Insights",
        help_text="Maximum number of AI insights to show per day"
    )

    # Minimum word count required to trigger commentary (avoids spam on short entries)
    min_words_for_commentary = models.IntegerField(
        default=30,
        verbose_name="Minimum Words for Insights",
        help_text="Entries must have at least this many words to trigger AI insights"
    )

    # ===== USAGE TRACKING =====
    # Tracks the last date commentary was shown (for daily reset)
    last_commentary_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Last Insight Date",
        help_text="Date when the last AI insight was shown"
    )

    # Counter for commentaries shown today (respects daily limit)
    today_commentary_count = models.IntegerField(
        default=0,
        verbose_name="Today's Insight Count",
        help_text="Number of AI insights shown today (resets daily)"
    )

    def __str__(self):
        return self.user.username

    def reset_daily_commentary_count(self):
        """
        Reset the daily commentary counter if it's a new day.
        This ensures the count resets at midnight based on the user's timezone.
        """
        if self.last_commentary_date != timezone.now().date():
            self.today_commentary_count = 0
            self.last_commentary_date = timezone.now().date()
            self.save(update_fields=['today_commentary_count', 'last_commentary_date'])

    def can_receive_commentary(self, content=None):
        """
        Check if this user should receive AI commentary right now.
        Optional content parameter allows checking word count requirements.

        Returns:
            bool: True if commentary should be shown, False otherwise
        """
        # Reset counter if it's a new day
        self.reset_daily_commentary_count()

        # Check if instant commentary is enabled
        if not self.enable_instant_commentary:
            return False

        # Check daily limit
        if self.today_commentary_count >= self.max_daily_commentaries:
            return False

        # Check word count if content is provided
        if content:
            word_count = len(content.split())
            if word_count < self.min_words_for_commentary:
                return False

            # Additional quality check: minimum character length
            if len(content.strip()) < 50:
                return False

        return True

    def increment_commentary_count(self):
        """
        Safely increment the commentary counter and update last date.
        Call this after showing a commentary to the user.
        """
        self.today_commentary_count += 1
        self.last_commentary_date = timezone.now().date()
        self.save(update_fields=['today_commentary_count', 'last_commentary_date'])






class BirthProfile(models.Model):
    """
    Stores user's birth data for natal chart calculations.

    Design decisions:
    - OneToOne: Each user has exactly one birth profile
    - Cached data: Birth charts are static, calculate once and store
    - Optional fields: Handle cases where exact birth time is unknown
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='birth_profile'
        # Access via: user.birth_profile
        # Cascade delete: if user deleted, birth profile deleted too
    )

    # === REQUIRED BIRTH DATA ===
    birth_date = models.DateField(
        help_text="Date of birth (required)"
        # Separated from time to handle "unknown time" cases
    )

    birth_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Exact time of birth (optional - affects house calculations)"
        # If null: can calculate planets but not houses/ascendant
    )

    birth_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Birth location latitude (-90 to 90)"
    )

    birth_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Birth location longitude (-180 to 180)"
    )

    birth_timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="IANA timezone (e.g., 'Asia/Manila', 'America/New_York')"
        # Critical for converting local birth time to UTC for calculations
    )

    # === OPTIONAL DISPLAY DATA ===
    birth_city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City name for display"
    )

    birth_country = models.CharField(
        max_length=100,
        blank=True,
        help_text="Country name for display"
    )

    # === COMPUTED/CACHED DATA ===
    has_birth_time = models.BooleanField(
        default=False,
        help_text="Flag indicating if exact birth time is known"
        # Determines which features are available
        # True: full natal chart with houses
        # False: planetary positions only
    )

    cached_chart_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Cached natal chart calculation (JSON)"
        # Structure will be: {
        #   'planets': [...],
        #   'houses': [...] or null,
        #   'aspects': [...],
        #   'calculated_at': timestamp
        # }
    )

    # === METADATA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Birth Profile"
        verbose_name_plural = "Birth Profiles"
        ordering = ['-created_at']

    def __str__(self):
        time_str = "with time" if self.has_birth_time else "no time"
        return f"{self.user.username}'s Birth Profile ({time_str})"

    def clean(self):
        """
        Model-level validation that runs before save().
        Django admin and forms will call this automatically.
        """
        # Validate birth date is in the past
        if self.birth_date and self.birth_date > timezone.now().date():
            raise ValidationError({
                'birth_date': 'Birth date cannot be in the future.'
            })

        # Validate latitude range
        if self.birth_latitude and not (-90 <= float(self.birth_latitude) <= 90):
            raise ValidationError({
                'birth_latitude': 'Latitude must be between -90 and 90 degrees.'
            })

        # Validate longitude range
        if self.birth_longitude and not (-180 <= float(self.birth_longitude) <= 180):
            raise ValidationError({
                'birth_longitude': 'Longitude must be between -180 and 180 degrees.'
            })

    def save(self, *args, **kwargs):
        """
        Override save to automatically set has_birth_time flag.
        This runs every time the model is saved.
        """
        # Set flag based on whether birth_time exists
        self.has_birth_time = self.birth_time is not None

        # Call the parent save method
        super().save(*args, **kwargs)

    def invalidate_cache(self):
        """
        Clear cached chart data to force recalculation.
        Call this when birth data is updated.
        """
        self.cached_chart_data = None
        self.save(update_fields=['cached_chart_data', 'updated_at'])

    def get_birth_datetime(self):
        """
        Combine birth_date and birth_time into a datetime object.
        Returns None if birth_time is not set.

        Used by chart calculation service.
        """
        if not self.birth_time:
            return None

        from datetime import datetime
        import pytz

        # Combine date and time
        naive_dt = datetime.combine(self.birth_date, self.birth_time)

        # Localize to birth timezone
        tz = pytz.timezone(self.birth_timezone)
        local_dt = tz.localize(naive_dt)

        return local_dt

    @property
    def chart_completeness(self):
        """
        Returns a percentage of how complete the birth profile is.
        Useful for UI progress indicators.
        """
        total_fields = 5  # date, time, lat, lon, timezone
        filled_fields = 3  # date, lat, lon always required

        if self.birth_time:
            filled_fields += 1
        if self.birth_timezone != 'UTC':
            filled_fields += 1

        return int((filled_fields / total_fields) * 100)


# Profile property for User model (keep your existing code)
def get_profile(self):
    return UserProfile.objects.get_or_create(user=self)[0]


User.add_to_class("profile", property(get_profile))