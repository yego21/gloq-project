from django.urls import path
from .views import birth_profile_setup


app_name = "userprofile"

urlpatterns = [
    # path("profile/update/", update_profile, name="profile_update"),
    path('profile/birth-setup/', birth_profile_setup, name='birth_profile_setup'),
]