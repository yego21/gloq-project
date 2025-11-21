import json
from pytz import timezone, UTC
import pytz

# from .models import JournalMode
# from .models import Mode
# from .mode_styler import MODE_STYLER_CONFIG, MODE_HEADER_CONFIG
# from django.contrib.auth.decorators import login_required


def get_session_timezone(request):
    tzname = request.session.get('timezone')
    if tzname in pytz.all_timezones:
        return timezone(tzname)
    return UTC