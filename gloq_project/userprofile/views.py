from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
# from .forms import UserProfileForm
from .models import UserProfile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BirthProfile
import pytz


# @login_required
# def update_profile(request):
#     # Get or create user profile
#     profile, created = UserProfile.objects.get_or_create(user=request.user)
#
#     if request.method == 'POST':
#         form = UserProfileForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Profile updated successfully!')
#             return redirect('journal:journal_dashboard')  # This is your redirect
#         else:
#             messages.error(request, 'Please correct the errors below.')
#     else:
#         form = UserProfileForm(instance=profile)
#
#     return render(request, 'userprofile/profile_update.html', {'form': form})





@login_required
def birth_profile_setup(request):
    """Form for users to input birth data for natal chart calculations"""

    # Check if user already has a birth profile
    if hasattr(request.user, 'birth_profile'):
        messages.info(request, 'You already have a birth profile. Redirecting to your natal chart.')
        return redirect('deep_dive:mystical')  # Adjust to your URL name

    if request.method == 'POST':
        try:
            # Create birth profile from form data
            BirthProfile.objects.create(
                user=request.user,
                birth_date=request.POST['birth_date'],
                birth_time=request.POST.get('birth_time') or None,
                birth_latitude=request.POST['birth_latitude'],
                birth_longitude=request.POST['birth_longitude'],
                birth_timezone=request.POST.get('birth_timezone', 'UTC'),
                birth_city=request.POST.get('birth_city', ''),
                birth_country=request.POST.get('birth_country', '')
            )
            messages.success(request, 'Birth profile created! Your natal chart is ready.')
            return redirect('deep_dive:mystical')
        except Exception as e:
            messages.error(request, f'Error creating birth profile: {str(e)}')

    # Get list of timezones for dropdown
    timezones = pytz.common_timezones

    context = {
        'timezones': timezones,
    }

    return render(request, 'userprofile/birth_profile_setup.html', context)







