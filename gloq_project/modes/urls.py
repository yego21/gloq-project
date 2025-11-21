from django.urls import path
from .views import mode_banner, mode_explorer, _mode_features, set_selected_mode, set_preferred_mode, switch_mode_dynamic


app_name = "modes"

# --- Modes & Preferences ---
urlpatterns = [
    path("mode_banner/", mode_banner, name="mode_banner"),
    path("modes/", mode_explorer, name="mode_explorer"),
    path("_mode_features/", _mode_features, name="_mode_features"),
    path("set-selected-mode/<mode_slug>/", set_selected_mode, name="set_selected_mode"),
    path("set-preferred-mode/<mode_slug>/", set_preferred_mode, name="set_preferred_mode"),
    path("switch-mode-dynamic/", switch_mode_dynamic, name="switch_mode_dynamic"),
]

