from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserPlan(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    preferred_mode = models.CharField(max_length=30, default='philosophical')  # optional
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"


class UserUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    tokens_used = models.PositiveIntegerField(default=0)
    actions_performed = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} on {self.date}: {self.tokens_used} tokens"