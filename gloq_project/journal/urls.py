from django.urls import path
from .views.dashboard_views import journal_dashboard
from .views.search_views import search_modal, search_results, filter_results_by_tag, entry_detail
# from .views.stream_views import stream_content
from .views.stream_views import StreamView, StreamToggleView, QuickActionView, AmbientDriftView, StreamPulseView, StreamStatsView
from .views.refraction_views import synthesize_entries, load_insight_panel, load_insight_tab
from .views.entry_views import submit_journal_entry
from .misc_views import mystical_test_view


app_name = "journal"

urlpatterns = [
    # --- Dashboard & Entries ---
    path("", journal_dashboard, name="journal_dashboard"),
    path("entries/new/", submit_journal_entry, name="new_journal_entry"),
    path("entry/<int:pk>/", entry_detail, name="entry_detail"),
    path("synthesize/", synthesize_entries, name="synthesize_entries"),


    # --- Insights ---
    path("insight-panel/", load_insight_panel, name="load_insight_panel"),
    path("insight-tab/<str:tab_name>/", load_insight_tab, name="load_insight_tab"),

    # --- Search ---
    path("search/modal/", search_modal, name="search_modal"),
    path("search/results/", search_results, name="search_results"),
    path("search/results_by_tag/", filter_results_by_tag, name="filter_results_by_tag"),

    # --- Streaming ---
    # path("stream/", stream_content, name="stream_content"),
    path('stream/', StreamView.as_view(), name='stream_content'),
    path('stream/toggle/', StreamToggleView.as_view(), name='stream_toggle'),
    path('stream/action/', QuickActionView.as_view(), name='stream_action'),
    path('stream/drift/', AmbientDriftView.as_view(), name='ambient_drift'),
    path('stream/pulse/', StreamPulseView.as_view(), name='stream_pulse'),
    path('stream/stats/', StreamStatsView.as_view(), name='stream_stats'),

    # --- Deep Dives ---
    path('deep_dive/mystical/', mystical_test_view, name='mystical_deep_dive'),

    path('testing/mystical/', mystical_test_view, name='mystical_test'),
]