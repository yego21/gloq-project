from datetime import datetime
from django.utils.timezone import localtime
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
import pytz
from django.views.decorators.csrf import csrf_exempt
from journal.models import JournalEntry


def landing_or_dashboard(request):
    if request.user.is_authenticated:
        return redirect('journal:journal_dashboard')  # Or 'dashboard'
    else:
        return render(request, 'landing.html')

def logout_view(request):
    logout(request)

    if request.headers.get('HX-Request'):
        return JsonResponse({"redirect": True, "redirect_url": "/"})  # or 'login' or any landing page

    else:
        # For non-HTMX requests, do a standard redirect.

        return redirect('landing_or_dashboard')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('landing_or_dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'user_management/signup.html', {'form': form})


@csrf_exempt
def set_timezone(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tz = data.get('timezone')
        if tz in pytz.all_timezones:
            request.session['timezone'] = tz
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)





