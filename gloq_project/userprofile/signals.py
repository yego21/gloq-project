from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

# To disable signals
def disable_signals():
    """Temporarily disable signal handlers"""
    post_save.disconnect(create_user_profile, sender=User)
    post_save.disconnect(create_user_profile, sender=User)

# To enable signals
def enable_signals():
    """Reconnect signal handlers after data is loaded"""
    post_save.connect(create_user_profile, sender=User)
    post_save.disconnect(create_user_profile, sender=User)