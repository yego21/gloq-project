from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField  # if using Postgres
from django.utils import timezone

# class JournalMode(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True)
#
#     is_premium = models.BooleanField(default=False)  # For future paywalling
#     is_active = models.BooleanField(default=True)    # In case some modes are disabled
#     slug = models.SlugField(unique=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return self.name


class DailyPlanetarySnapshot(models.Model):
    """
    Stores planetary positions for a specific date/timezone.
    One snapshot per day per timezone - shared across all journal entries.
    """
    date = models.DateField()
    timezone = models.CharField(max_length=50, default='UTC')
    planetary_data = models.JSONField(
        help_text="Complete planetary positions from AstrologyService"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('date', 'timezone')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'timezone']),
        ]

    def __str__(self):
        return f"Planetary snapshot for {self.date} ({self.timezone})"

    @classmethod
    def get_or_create_today(cls, timezone):
        """
        Minimal version with basic error printing
        """
        from django.utils.timezone import now
        from deep_dive.services.mystical.astronomical_svc import AstronomicalService

        today = now().date()

        try:
            snapshot, created = cls.objects.get_or_create(
                date=today,
                timezone=timezone,
                defaults={'planetary_data': {}}
            )

            print(f"\n🌍 Planetary snapshot check: {today} ({timezone})")

            if created or not snapshot.planetary_data:
                print("   Fetching data from astrology service...")
                try:
                    astro_service = AstronomicalService()
                    snapshot.planetary_data = astro_service.get_daily_planetary_summary(timezone)
                    snapshot.save()
                    print(f"   ✓ Data saved successfully")
                except Exception as e:
                    print(f"   ✗ ERROR: {type(e).__name__}: {str(e)}")
                    # Print just the error without full traceback
                    snapshot.planetary_data = {'error': str(e)}
                    snapshot.save()

            return snapshot

        except Exception as e:
            print(f"\n❌ FATAL ERROR in get_or_create_today:")
            print(f"   {type(e).__name__}: {str(e)}")
            raise

    @classmethod
    def get_or_create_for_date(cls, target_date):
        """
        Get snapshot for a specific date, or create it if missing.
        Works for past, present, or future dates.
        """

        from deep_dive.services.mystical.astronomical_svc import AstronomicalService


        # Try to get existing snapshot
        snapshot, created = cls.objects.get_or_create(
            date=target_date,
            defaults={'planetary_data': {}}
        )

        # If newly created OR data is empty, calculate it
        if created or not snapshot.planetary_data:
            astro_service = AstronomicalService()
            # Calculate at noon UTC to avoid edge cases
            snapshot.planetary_data = astro_service.get_planetary_summary_for_date(
                target_date,
                'UTC'
            )
            snapshot.save()

        return snapshot

    def regenerate(self):
        """
        Regenerate this snapshot's planetary data.
        Useful if data was corrupted or you want to recalculate.
        """
        from deep_dive.services.mystical.astronomical_svc import AstronomicalService

        astro_service = AstronomicalService()
        self.planetary_data = astro_service.get_planetary_summary_for_date(
            self.date,
            'UTC'
        )
        self.save()
        return self

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=5, blank=True, null=True)
    sentiment_score = models.FloatField(
        default=0.0,
        help_text='Sentiment score from -1.0 (very negative) to 1.0 (very positive)'
    )

    def __str__(self):
        return f"{self.emoji or ''} {self.name}"

    @property
    def sentiment_label(self):
        """Human-readable sentiment label"""
        if self.sentiment_score <= -0.5:
            return 'Very Negative'
        elif self.sentiment_score <= -0.2:
            return 'Negative'
        elif self.sentiment_score <= 0.2:
            return 'Neutral'
        elif self.sentiment_score <= 0.5:
            return 'Positive'
        else:
            return 'Very Positive'

    @property
    def sentiment_color(self):
        """Color for UI display"""
        if self.sentiment_score <= -0.5:
            return 'red'
        elif self.sentiment_score <= -0.2:
            return 'orange'
        elif self.sentiment_score <= 0.2:
            return 'yellow'
        elif self.sentiment_score <= 0.5:
            return 'green'
        else:
            return 'emerald'


class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    label = models.CharField(max_length=20, null=True, blank=True)  # 'entry1', 'entry2', 'entry3'
    content = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True, related_name="entries")
    created_at = models.DateTimeField(default=timezone.now)

    # Planetary context at time of creation
    planetary_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Snapshot of all planetary positions when entry was created"
    )

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']

    planetary_snapshot = models.ForeignKey(
        DailyPlanetarySnapshot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries'
    )

    def save(self, *args, **kwargs):
        """Auto-assign planetary snapshot based on entry's creation date in user's local timezone"""
        is_new = self.pk is None

        # Save first to ensure created_at is set
        if is_new:
            super().save(*args, **kwargs)

        # Assign snapshot if missing
        if not self.planetary_snapshot:
            local_date = self._get_local_date()
            self.planetary_snapshot = DailyPlanetarySnapshot.get_or_create_for_date(local_date)
            super().save(update_fields=['planetary_snapshot'])
        elif not is_new:
            super().save(*args, **kwargs)

    def _get_local_date(self):
        """Get entry's creation date in user's local timezone"""
        try:
            import pytz
            user_tz = pytz.timezone(self.user.birthprofile.timezone or 'UTC')
            local_dt = self.created_at.astimezone(user_tz)
            return local_dt.date()
        except:
            return self.created_at.date()























