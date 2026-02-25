from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz = request.session.get('timezone')
        if tz:
            timezone.activate(tz)
        else:
            timezone.deactivate()
        return self.get_response(request)

# middleware.py
from datetime import date
from django.core.cache import cache

class DailyPlanetarySnapshotMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        today = date.today()
        cache_key = f"planetary_snapshot_initialized_{today}"

        if not cache.get(cache_key):
            try:
                from journal.models import DailyPlanetarySnapshot
                DailyPlanetarySnapshot.get_or_create_for_date(today)
                cache.set(cache_key, True, timeout=60 * 60 * 6)  # recheck every 6 hours
            except Exception as e:
                # Don't let snapshot failure break the request
                pass

        return self.get_response(request)