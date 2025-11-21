# from django.shortcuts import render, redirect, get_object_or_404
# from django.http import HttpResponse, HttpResponseBadRequest
# from django.contrib.auth.decorators import login_required
# from django.views.decorators.http import require_POST
# import json
#
# # from ..models import JournalMode
# from ..utils import get_active_mode, get_mode_styler_context, get_header_config, get_current_mode, \
#     get_session_timezone
# from gloq_project.modes.features.mode_styler import get_feature_styles, get_card_icons
# from ..utils import get_daily_content
# from ..services.mystical.astronomical_svc import get_moon_phase, get_planetary_summary
#
#
#
#
# @require_POST
# def mode_banner(request):
#     active_mode = get_active_mode(request)
#
#     # Handle POST override - this should OVERRIDE the active mode temporarily
#     mode_slug = request.POST.get("slug")
#     if mode_slug:
#         # User is explicitly switching modes via POST
#         mode = get_object_or_404(JournalMode, slug=mode_slug)
#         # Optionally update session to remember this choice
#         request.session['selected_mode_id'] = mode.id
#     else:
#         # Use your active mode logic (preferred mode for new sessions, etc.)
#         mode = active_mode or get_object_or_404(JournalMode, slug='default')
#     mode_header = get_header_config(active_mode)
#     return render(request, "journal/modes/_mode_banner.html", {'mode_header': mode_header, 'mode':mode})
#
#
# @login_required
# def mode_selector(request):
#     modes = JournalMode.objects.filter(is_active=True).order_by('name')
#     print('Current Mode:' + str(get_current_mode(request)))
#     return render(request, "journal/partials/_mode_selector.html", {'modes': modes})
#
#
# @login_required
# def mode_explorer(request):
#     modes = JournalMode.objects.all()
#     active_mode = get_active_mode(request)
#     mode_styler = get_mode_styler_context(active_mode)
#     return render(request, "journal/modes/mode_explorer.html", {
#         "modes": modes,
#         "active_mode": active_mode,
#         'mode_styler': mode_styler,
#         'user_timezone': str(get_session_timezone(request)),
#     })
#
#
# @login_required
# @require_POST
# def switch_mode_dynamic(request):
#     mode_slug = request.POST.get('mode_slug')
#     if not mode_slug:
#         return HttpResponseBadRequest("No mode selected")
#
#     try:
#         mode = JournalMode.objects.get(slug=mode_slug, is_active=True)
#         # Update session only
#         request.session['selected_mode_slug'] = mode.slug
#
#         # Get updated context
#         mode_styler = get_mode_styler_context(mode_slug)
#
#         # Return multiple HTMX updates
#         response = HttpResponse()
#         response['HX-Trigger-After-Swap'] = json.dumps({
#             "updateTheme": {
#                 "mode_slug": mode_slug,
#                 # "background_class": mode_styler['background_class'],
#                 "mode_name": mode.name
#             }
#         })
#         return response
#
#     except JournalMode.DoesNotExist:
#         return HttpResponseBadRequest("Invalid mode")
#
#
# @login_required
# def set_selected_mode(request, mode_slug):
#     mode = get_object_or_404(JournalMode, slug=mode_slug)
#     request.session['selected_mode_slug'] = mode.slug
#     return redirect("journal:mode_explorer")
#
# @login_required
# def set_preferred_mode(request, mode_slug):
#     mode = get_object_or_404(JournalMode, slug=mode_slug)
#     userprofile = request.user.userprofile
#     userprofile.preferred_mode = mode
#     userprofile.save()
#     return redirect("journal:mode_explorer")
#
#
#
#
#
#
#
# # @login_required
# # def mode_selector(request):
# #     modes = JournalMode.objects.filter(is_active=True).order_by('name')
# #     return render(request, "journal/partials/_mode_selector.html", {'modes': modes})
# #
# # @login_required
# # def mode_explorer(request):
# #     modes = JournalMode.objects.all()
# #     active_mode = get_active_mode(request)
# #     mode_styler = get_mode_styler_context(active_mode)
# #     return render(request, "journal/modes/mode_explorer.html", {"modes": modes, "active_mode": active_mode, 'mode_styler': mode_styler})
# #
# # @login_required
# # @require_POST
# # def switch_mode_dynamic(request):
# #     mode_slug = request.POST.get('mode_slug')
# #     if not mode_slug:
# #         return HttpResponseBadRequest("No mode selected")
# #     try:
# #         mode = JournalMode.objects.get(slug=mode_slug, is_active=True)
# #         request.session['selected_mode_slug'] = mode.slug
# #         response = HttpResponse()
# #         response['HX-Trigger-After-Swap'] = json.dumps({"updateTheme": {"mode_slug": mode_slug, "mode_name": mode.name}})
# #         return response
# #     except JournalMode.DoesNotExist:
# #         return HttpResponseBadRequest("Invalid mode")
# #
# #
# # @login_required
# # def set_selected_mode(request, mode_slug):
# #     mode = get_object_or_404(JournalMode, slug=mode_slug)
# #     request.session['selected_mode_slug'] = mode.slug
# #     return redirect("journal:mode_explorer")
# #
# # @login_required
# # def set_preferred_mode(request, mode_slug):
# #     mode = get_object_or_404(JournalMode, slug=mode_slug)
# #     userprofile = request.user.userprofile
# #     userprofile.preferred_mode = mode
# #     userprofile.save()
# #     return redirect("journal:mode_explorer")
#
#
# @login_required
# @require_POST
# def _mode_features(request):
#     # Get the active mode from context processor (your logic for new sessions, etc.)
#     active_mode = get_active_mode(request)
#
#     # Handle POST override - this should OVERRIDE the active mode temporarily
#     mode_slug = request.POST.get("slug")
#     mode = get_object_or_404(JournalMode, slug=mode_slug)
#     print("MODE_FEATURE_MODE:"+ str(mode_slug))
#     if mode_slug == 'mystical':
#         print("MYSTICAL:" + str(mode_slug))
#         moon_phase = get_moon_phase()
#         planetary_data = get_planetary_summary()
#
#         context = {
#             'feature_content': {
#                 'title': f"{moon_phase['emoji']} Mystical Guidance",
#                 'astronomical': f"The {moon_phase['phase']} ({moon_phase['illumination']} illuminated) brings profound energy. {moon_phase['description']} {moon_phase.get('mystical_meaning', '')}",
#                 'action': f"Under this {moon_phase['phase']}, focus on {moon_phase['description'].lower()}. The {planetary_data.get('dominant_element', 'cosmic')} element guides your mystical journey today.",
#                 'fact': f"Cosmic Alignment: {planetary_data.get('cosmic_weather', 'The stars dance in mysterious patterns')} The Moon travels through {planetary_data.get('moon_sign', 'ethereal realms')}, while the Sun blazes in {planetary_data.get('sun_sign', 'cosmic fire')}."
#             },
#             'feature_styles': {
#                 'question_container': 'mode-card content-inquiry p-6 rounded-xl expandable-card',
#                 'astronomical_container': 'mode-card content-mystical p-6 rounded-xl expandable-card bg-gradient-to-br from-purple-50 to-indigo-100 border-2 border-purple-200',
#                 'action_container': 'mode-card content-action p-6 rounded-xl expandable-card',
#                 'fact_container': 'mode-card content-insight p-6 rounded-xl expandable-card',
#                 'icon_container': 'w-10 h-10 bg-gradient-to-br from-purple-400 to-purple-600 rounded-lg flex items-center justify-center',
#                 'icon_class': 'w-5 h-5 text-white icon-float',
#                 'title': 'text-lg font-semibold text-gray-900 mb-2',
#                 'text': 'text-gray-700 mb-3',
#                 'expanded_content': 'mt-4 p-4 bg-white/50 rounded-lg',
#                 'expanded_text': 'text-sm text-gray-600',
#                 'action_btn': 'px-3 py-1 text-xs bg-purple-100 text-purple-700 rounded-full hover:bg-purple-200'
#             }
#         }
#
#     else:
#         # User is explicitly switching modes via POST
#         mode = get_object_or_404(JournalMode, slug=mode_slug)
#         # Optionally update session to remember this choice
#         request.session['selected_mode_id'] = mode.id
#
#
#         mode_styler = get_mode_styler_context(active_mode)
#         mode_header = get_header_config(active_mode)
#         feature_styles = get_feature_styles(active_mode)
#         feature_content = get_daily_content(request, mode_slug)
#         card_icons = get_card_icons()
#         context = {
#             "mode_styler": mode_styler,
#             'mode_header': mode_header,
#             'selected_mode': mode,
#             'feature_styles': feature_styles,
#             'feature_content': feature_content,
#             'card_icons': card_icons,
#         }
#         print(f"DEBUG: Resolved active_mode features = {active_mode}")
#     return render(request, "journal/modes/_mode_features.html", context)