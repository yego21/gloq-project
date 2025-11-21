from django.shortcuts import render
from modes.models import Mode
# from openai import OpenAI
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from modes.utils import get_mode_styler_context, get_active_mode
from django.views.decorators.http import require_POST


# Assumes you have a helper to tag entries










# @login_required
# def mode_explorer(request):
#     modes = JournalMode.objects.all()
#     if request.method == "POST":
#         selected_mode_id = request.POST.get("mode_id")
#         profile = request.user.userprofile
#         profile.selected_mode_id = selected_mode_id
#         profile.save()
#         return redirect('journal_dashboard')
#
#     return render(request, 'journal/mode_explorer.html', {'modes': modes})

def mystical_test_view(request):
    return render(request, "journal/testings/mystical_ui.html")



@login_required
@require_POST
def _mode_banner(request):
    mode_slug = request.POST.get("slug")  # Get from POST data
    if not mode_slug:
        mode_slug = get_active_mode(request)  # Fallback to session

    print(f"DEBUG: SLUG: = {mode_slug}")
    mode = get_object_or_404(Mode, slug=mode_slug)
    # Don't update session here - switch_mode_dynamic already did it

    mode_styler = get_mode_styler_context(mode_slug)
    return render(request, "journal/modes/_mode_banner.html", {
        "mode_styler": mode_styler,
        'selected_mode': mode,
    })








# @require_POST
# @login_required
# def set_journal_mode(request):
#     mode_slug = request.POST.get('mode')
#     try:
#         mode = JournalMode.objects.get(slug=mode_slug)
#         set_mode_for_user(request, mode)
#         return JsonResponse({'status': 'success', 'mode': mode.name})
#     except JournalMode.DoesNotExist:
#         return JsonResponse({'status': 'error', 'message': 'Invalid mode'})

# def journal_entry_by_mode(request, slug):
#     mode = get_object_or_404(JournalMode, slug=slug)
#     request.session['selected_mode'] = mode.slug  # or mode.id if you prefer
#     return redirect('journal:journal_dashboard')  # We'll adapt the entry view soon

# 2. NEW JOURNAL ENTRY VIEW (HTMX endpoint)


# def submit_journal_entry(request):
#     if request.method != "POST":
#         return HttpResponseBadRequest("Invalid request.")
#
#     today = now().date()
#     entries_today = JournalEntry.objects.filter(user=request.user, created_at__date=today)
#
#     if entries_today.count() >= 3:
#         html = render_to_string("journal/partials/_alert.html", {
#             "type": "danger",
#             "message": "Daily entry limit reached.",
#         })
#         return HttpResponse(html, status=400)
#
#     form = JournalEntryForm(request.POST)
#     if form.is_valid():
#         entry = form.save(commit=False)
#         entry.user = request.user
#         entry.save()
#
#         # Tagging and save again
#         entry.tags = extract_tags(entry)
#         entry.save()
#
#         entries_today = JournalEntry.objects.filter(user=request.user, created_at__date=today).order_by('-created_at')
#         can_add = entries_today.count() < 3
#
#         entries_html = render_to_string("journal/_entries.html", {
#             'entries': entries_today,
#             'can_add': can_add,
#         }, request=request)
#
#         alert_html = render_to_string("journal/partials/_alert.html", {
#             "type": "success",
#             "message": "Journal entry saved successfully!",
#         })
#
#         return HttpResponse(alert_html + entries_html)
#     else:
#         error_html = render_to_string("journal/partials/_alert.html", {
#             "type": "danger",
#             "message": "Please correct the errors in the form.",
#         })
#         return HttpResponse(error_html, status=400)


# @login_required
# def same_day_entries(request):
#     today = now().date()
#
#     entries = JournalEntry.objects.filter(
#         user=request.user,
#         created_at__date=today
#     ).order_by('-created_at')
#
#     can_add = entries.count() < 3
#
#     html = render_to_string("journal/_entries.html", {
#         'entries': entries,
#         'can_add': can_add,
#     }, request=request)
#
#     return HttpResponse(html)





# @login_required
# def fetch_entries_by_range(request):
#     start_str = request.GET.get('start-date')
#     end_str = request.GET.get('end-date')
#
#     if not start_str or not end_str:
#         return HttpResponseBadRequest("Missing start or end date.")
#
#     try:
#         # Parse into date objects
#         start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
#         end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
#     except ValueError:
#         return HttpResponseBadRequest("Invalid date format. Expected YYYY-MM-DD.")
#
#     # Ensure proper ordering (if user swaps the range)
#     if start_date > end_date:
#         start_date, end_date = end_date, start_date
#
#     # Create timezone-aware datetime range
#     start = dj_timezone.make_aware(datetime.combine(start_date, time.min))
#     end = dj_timezone.make_aware(datetime.combine(end_date, time.max))
#
#     entries = (
#         JournalEntry.objects
#         .filter(user=request.user, created_at__range=(start, end))
#         .order_by('-created_at')
#     )
#
#     return render(request, 'journal/partials/_entries.html', {
#         'entries': entries,
#         # can_add stays per *day*, but in range view it’s tricky,
#         # so we just return False or skip it unless you want per-day logic
#         'can_add': False,
#     })















# INSERT INTO journal_journalmode (name, description, is_premium, is_active, slug, created_at)
# VALUES
# ('Medical', 'Focuses on health, wellness, and self-care ai_insights from your daily entries.', false, true, 'medical', NOW()),
# ('Creative', 'Explores your day through storytelling, imagination, and artistic expression.', false, true, 'creative', NOW()),
# ('Productive', 'Emphasizes efficiency, discipline, and meaningful results from daily actions.', false, true, 'productive', NOW()),
# ('Exploratory', 'Encourages curiosity, learning, and discovery in your daily experiences.', false, true, 'exploratory', NOW()),
# ('Visionary', 'Connects your present actions to your long-term dreams and aspirations.', false, true, 'visionary', NOW());
#
#
#
# INSERT INTO journal_journalmode (name, description, is_premium, is_active, slug, created_at)
# VALUES
# ('Spiritual', 'Connect daily life to deeper meaning, inner wisdom, and a sense of the sacred.', false, true, 'spiritual', NOW());
#
# SELECT * FROM django_cache;
# Creative
# Exploratory
# Medical
# Spiritual
# Philosophical
# Mystical
# Exploratory
# Visionary
# Productive