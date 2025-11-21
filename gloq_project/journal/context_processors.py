from modes.models import Mode

def active_mode(request):
    mode = None

    # 1. Check if selected_mode is in session
    selected_mode_id = request.session.get("selected_mode_id")
    if selected_mode_id:
        mode = Mode.objects.filter(id=selected_mode_id).first()

    # 2. If not, fallback to preferred_mode
    if not mode and request.user.is_authenticated:
        user_profile = getattr(request.user, "userprofile", None)
        if user_profile and user_profile.preferred_mode:
            mode = user_profile.preferred_mode

    return {"active_mode": mode}
