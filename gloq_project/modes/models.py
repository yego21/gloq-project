from django.db import models

class Mode(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    is_premium = models.BooleanField(default=False)  # For future paywalling
    is_active = models.BooleanField(default=True)    # In case some modes are disabled
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class DailyContent(models.Model):
    CONTENT_TYPES = [
        ('global', 'Global'),
        ('zodiac', 'Zodiac-specific'),
        ('personalized', 'User-personalized'),
    ]

    mode = models.ForeignKey(Mode, on_delete=models.CASCADE)
    date = models.DateField()
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='global')
    personalization_key = models.CharField(max_length=100, blank=True, null=True)
    content_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['mode', 'date', 'content_type', 'personalization_key']
        indexes = [
            models.Index(fields=['mode', 'date', 'content_type']),
        ]

    def __str__(self):
        return f"{self.mode.name} - {self.date} ({self.content_type})"