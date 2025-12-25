from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from ..models import JournalEntry
from modes.models import Mode
from ..forms import JournalEntryForm
from userprofile.utils import get_session_timezone
from modes.utils import get_active_mode, get_mode_styler_context, get_header_config


# @login_required
# def journal_dashboard(request):
#     active_mode = get_active_mode(request) or JournalMode.objects.get(slug='default')
#     form = JournalEntryForm()
#     today = now().date()
#     entries_today = JournalEntry.objects.filter(user=request.user, created_at__date=today).order_by('-created_at')
#     can_add = entries_today.count() < 3
#     modes = JournalMode.objects.filter(is_active=True).order_by('name')
#     mode_styler = get_mode_styler_context(active_mode)
#
#     return render(request, 'dashboard.html', {
#         'form': form,
#         'entries': entries_today,
#         'active_mode': active_mode,
#         'modes': modes,
#         'can_add': can_add,
#         'user_timezone': str(get_session_timezone(request)),
#         'mode_styler': mode_styler,
#     })


# 1. MAIN DASHBOARD VIEW
@login_required
def journal_dashboard(request):
    """
    Main dashboard view - renders the journal dashboard with mode content loaded via HTMX
    """
    print("===== DASHBOARD DEBUG START =====")

    # Debug session state
    session_selected_mode_slug = request.session.get("selected_mode_slug")
    session_preferred_mode_slug = getattr(request.user.userprofile.preferred_mode, "slug", None)

    print(f"DEBUG: Session 'selected_mode_slug' = {session_selected_mode_slug}")
    print(f"DEBUG: UserProfile 'preferred_mode_slug' = {session_preferred_mode_slug}")

    # Determine active_mode (this returns a slug string)
    active_mode = get_active_mode(request)
    if not active_mode:
        # Fallback to preferred mode or default
        active_mode = session_preferred_mode_slug or 'philosophical'

    print(f"DEBUG: Resolved active_mode = {active_mode}")

    # Prepare dashboard data
    form = JournalEntryForm()
    today = now().date()
    entries_today = JournalEntry.objects.filter(user=request.user, created_at__date=today).order_by('-created_at')
    can_add = entries_today.count() < 3
    modes = Mode.objects.filter(is_active=True).order_by('name')
    mode_styler = get_mode_styler_context(active_mode)
    mode_header = get_header_config(active_mode)

    print(f"DEBUG: Entries today count = {entries_today.count()}")
    print(f"DEBUG: Can add more entries today? = {can_add}")
    print("===== DASHBOARD DEBUG END =====")

    return render(request, 'dashboard.html', {
        'form': form,
        'entries': entries_today,
        'active_mode': active_mode,
        'modes': modes,
        'can_add': can_add,
        'user_timezone': str(get_session_timezone(request)),
        'mode_styler': mode_styler,
        'mode_header': mode_header,
    })