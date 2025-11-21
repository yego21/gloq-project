from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.db.models.functions import TruncDate
from ..models import JournalEntry, Tag
from django.shortcuts import get_object_or_404

def search_modal(request):
    # Lightweight modal with two date pickers
    return render(request, "journal/search/_search_modal.html")

def search_results(request):
    start_raw = request.GET.get("start")
    end_raw   = request.GET.get("end")
    tag_id    = request.GET.get("tag_filter")  # new

    start_date = parse_date(start_raw) if start_raw else None
    end_date   = parse_date(end_raw) if end_raw else None

    error = None
    if not start_date or not end_date:
        error = "Pick both start and end dates."
    elif start_date > end_date:
        error = "Start date cannot be after end date."

    entries = []
    if not error:
        qs = (
            JournalEntry.objects
            .filter(user=request.user, created_at__date__range=(start_date, end_date))
            .annotate(day=TruncDate("created_at"))
            .order_by("-day", "-created_at")
        )
        if tag_id:  # only apply if selected
            qs = qs.filter(tags__id=tag_id)
        entries = qs

    ctx = {
        "entries": entries,
        "start_date": start_date,
        "end_date": end_date,
        "tag_id": tag_id,   # so template knows what's selected
        "error": error,
        "tags": Tag.objects.filter(entries__user=request.user).distinct(),  # for dropdown
    }
    return render(request, "journal/search/_search_results.html", ctx)


def filter_results_by_tag(request):
    """Handle tag filtering within modal"""
    tag_id = request.GET.get("tag_filter")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    # Parse dates
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None

    entries = JournalEntry.objects.filter(user=request.user)

    # Apply date filter
    if start_date and end_date:
        entries = entries.filter(created_at__date__range=(start_date, end_date))

    # Apply tag filter
    if tag_id:
        try:
            entries = entries.filter(tags__id=int(tag_id))
        except (ValueError, TypeError):
            pass

    entries = entries.annotate(day=TruncDate("created_at")).order_by("-day", "-created_at")

    # ✅ Only include tags used by this user
    user_tags = Tag.objects.filter(entries__user=request.user).distinct()

    ctx = {
        "entries": entries,
        "tag_id": tag_id,
        "start_date": start_date,
        "end_date": end_date,
        "tags": user_tags,
    }
    return render(request, "journal/search/_search_result_by_tag_mood.html", ctx)

def entry_detail(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    return render(request, "journal/search/_entry_detail_modal.html", {"entry": entry})