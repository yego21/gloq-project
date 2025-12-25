from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

# from ..models import JournalMode
from .models import Mode
from .utils import get_active_mode, get_mode_styler_context, get_header_config, get_current_mode, get_session_timezone
from .features.mode_styler import get_feature_styles, get_card_icons
from .utils import get_daily_content
from deep_dive.services.mystical.astronomical_svc import get_moon_phase, get_planetary_summary
from deep_dive.views import mystical_views, spiritual_views, creative_views, productive_views, philosophical_views


@require_POST
def mode_banner(request):
    active_mode = get_active_mode(request)

    # Handle POST override - this should OVERRIDE the active mode temporarily
    mode_slug = request.POST.get("slug")
    if mode_slug:
        # User is explicitly switching modes via POST
        mode = get_object_or_404(Mode, slug=mode_slug)
        # Optionally update session to remember this choice
        request.session['selected_mode_id'] = mode.id
    else:
        # Use your active mode logic (preferred mode for new sessions, etc.)
        mode = active_mode or get_object_or_404(Mode, slug='default')
    mode_header = get_header_config(active_mode)
    return render(request, "modes/_mode_banner.html", {'mode_header': mode_header, 'mode':mode, 'active':active_mode})


# @login_required
# def mode_selector(request):
#     modes = Mode.objects.filter(is_active=True).order_by('name')
#     print('Current Mode:' + str(get_current_mode(request)))
#     return render(request, "journal/partials/_mode_selector.html", {'modes': modes})


@login_required
def mode_explorer(request):
    modes = Mode.objects.all()
    active_mode = get_active_mode(request)
    mode_styler = get_mode_styler_context(active_mode)
    return render(request, "modes/mode_explorer.html", {
        "modes": modes,
        "active_mode": active_mode,
        'mode_styler': mode_styler,
        'user_timezone': str(get_session_timezone(request)),
    })


@login_required
@require_POST
def switch_mode_dynamic(request):
    mode_slug = request.POST.get('mode_slug')
    if not mode_slug:
        return HttpResponseBadRequest("No mode selected")

    try:
        mode = Mode.objects.get(slug=mode_slug, is_active=True)
        # Update session only
        request.session['selected_mode_slug'] = mode.slug

        # Get updated context
        mode_styler = get_mode_styler_context(mode_slug)

        # Return multiple HTMX updates
        response = HttpResponse()
        response['HX-Trigger-After-Swap'] = json.dumps({
            "updateTheme": {
                "mode_slug": mode_slug,
                # "background_class": mode_styler['background_class'],
                "mode_name": mode.name
            }
        })
        return response

    except Mode.DoesNotExist:
        return HttpResponseBadRequest("Invalid mode")


@login_required
def set_selected_mode(request, mode_slug):
    mode = get_object_or_404(Mode, slug=mode_slug)
    request.session['selected_mode_slug'] = mode.slug
    return redirect("modes:mode_explorer")

@login_required
def set_preferred_mode(request, mode_slug):
    mode = get_object_or_404(Mode, slug=mode_slug)
    userprofile = request.user.userprofile
    userprofile.preferred_mode = mode
    userprofile.save()
    return redirect("modes:mode_explorer")

@login_required
def _mode_features(request, philosophical_philosophical=None):
    """
    Router view that delegates to the appropriate deep_dive mode view
    Returns the mode's content to be loaded into #mode-features div
    """
    slug = request.POST.get('slug') or request.GET.get('slug')

    if not slug:
        # Fallback to active mode
        active_mode = get_active_mode(request)
        slug = active_mode if active_mode else 'philosophical'

    try:
        # Verify mode exists
        mode = get_object_or_404(Mode, slug=slug)
        request.session['selected_mode_slug'] = mode.slug

        # Route to appropriate deep_dive view based on slug
        # These views should return rendered HTML for the mode content
        if slug == 'mystical':
            return mystical_views.mystical(request)
        elif slug == 'spiritual':
            return spiritual_views.spiritual(request)
        elif slug == 'creative':
            return creative_views.creative(request)
        elif slug == 'productive':
            return productive_views.productive(request)
        elif slug == 'philosophical':
            return philosophical_views.philosophical(request)
        # Add other modes here as you build them
        # elif slug == 'visionary':
        #     return visionary_views.visionary_content(request)
        else:
            # Fallback for modes without deep_dive pages yet
            return render(request, 'modes/_mode_placeholder.html', {
                'mode_name': mode.name,
                'mode_slug': slug
            })

    except Mode.DoesNotExist:
        return HttpResponseBadRequest("Invalid mode")
# @login_required
# def _mode_features(request):
#     """
#     Returns the appropriate feature content based on the active mode
#     """
#
#
#
#     active_mode = get_active_mode(request)
#
#
#     slug = request.POST.get('slug')
#
#     if not slug:
#         # Fallback to active mode if no slug provided
#         active_mode = get_active_mode(request)
#         slug = active_mode.slug if active_mode else 'default'
#
#     # Handle mystical mode separately - delegate to deep_dive template
#     if slug == 'mystical':
#         return render(request, 'deep_dive/mystical/mystical.html', {
#             'mode_slug': slug
#         })
#
#     # Handle other modes with your existing logic
#     try:
#         mode = get_object_or_404(Mode, slug=slug)
#         request.session['selected_mode_id'] = mode.id
#
#         # Get all the context you need for normal modes
#         active_mode = get_active_mode(request)
#         mode_styler = get_mode_styler_context(active_mode)
#         mode_header = get_header_config(active_mode)
#         feature_styles = get_feature_styles(active_mode)
#         feature_content = get_daily_content(request, slug)
#         card_icons = get_card_icons()
#
#         context = {
#             "mode_styler": mode_styler,
#             'mode_header': mode_header,
#             'selected_mode': mode,
#             'feature_styles': feature_styles,
#             'feature_content': feature_content,
#             'card_icons': card_icons,
#         }
#
#         return render(request, "modes/_mode_features.html", context)
#
#     except Mode.DoesNotExist:
#         return HttpResponseBadRequest("Invalid mode")




