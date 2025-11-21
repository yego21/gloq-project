from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserPlan

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_plan(sender, instance, created, **kwargs):
    if created:
        UserPlan.objects.create(user=instance)



# To disable signals
def disable_signals():
    """Temporarily disable signal handlers"""
    post_save.disconnect(create_user_plan, sender=User)
    post_save.disconnect(create_user_plan, sender=User)

# To enable signals
def enable_signals():
    """Reconnect signal handlers after data is loaded"""
    post_save.connect(create_user_plan, sender=User)
    post_save.disconnect(create_user_plan, sender=User)