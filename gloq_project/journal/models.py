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

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

    class Meta:
        ordering = ['-created_at']





















