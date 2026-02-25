import random

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now
from datetime import timedelta
from ..services.mystical.astronomical_svc import get_moon_phase, get_planetary_summary


from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views import View
from datetime import datetime, date
import json
import pytz

from django.urls import reverse

from userprofile.models import BirthProfile

from ..services.mystical.natal_chart_svc import NatalChartService
from ..services.mystical.pattern_analyzer_svc import UserPatternAnalyzer
from journal.models import JournalEntry

from ..services.mystical.planet_insights_svc import get_planet_insight
from ..utils.mystical_utils import get_page_range, generate_aspect_interpretation, generate_planet_interpretation
from journal.models import DailyPlanetarySnapshot


@login_required
def rhythm_dashboard(request):
    """
    Personal Rhythm Dashboard - Dedicated page for pattern analysis.

    Shows:
    - Cosmic rhythm (current celestial state)
    - Journal patterns (frequency, themes, timing)
    - Advanced analytics (correlations, cycles)
    - Progressive insights based on data richness
    """
    import json

    try:
        analyzer = UserPatternAnalyzer(request.user)
        insights = analyzer.get_all_insights()
        chart_data = analyzer.get_visualization_data()

        context = {
            'insights': insights,
            'chart_data': json.dumps(chart_data),
            'data_level': insights['data_level'],
            'meta': insights['meta'],
            'page_title': 'Personal Rhythm',
            'show_navigation': True  # Show link back to mystical page
        }

        return render(
            request,
            'deep_dive/mystical/tarot_and_stats/mystic_rhythms/_rhythm_dashboard.html',
            context
        )

    except Exception as e:
        import traceback
        print(f"Rhythm dashboard error: {e}")
        print(traceback.format_exc())

        # Return error state with minimal data
        return render(
            request,
            'deep_dive/mystical/tarot_and_stats/mystic_rhythms/_rhythm_dashboard.html',
            {
                'error': True,
                'error_message': 'Unable to analyze patterns at this time',
                'insights': {'data_level': 'minimal', 'cosmic_rhythm': None, 'journal_rhythm': None},
                'chart_data': json.dumps({}),
                'meta': {'level_description': 'Error loading data'},
                'page_title': 'Personal Rhythm'
            }
        )


@login_required
def personal_rhythm_section(request):
    """
    Render the personal rhythm section HTML.
    This replaces the biorhythm section in your template.
    """
    import json

    try:
        analyzer = UserPatternAnalyzer(request.user)
        insights = analyzer.get_all_insights()
        chart_data = analyzer.get_visualization_data()

        context = {
            'insights': insights,
            'chart_data': json.dumps(chart_data),  # Convert to JSON for JavaScript
            'data_level': insights['data_level'],
            'meta': insights['meta']
        }

        return render(
            request,
            'deep_dive/mystical/tarot_and_stats/mystic_rhythms/includes/personal_rhythm.html',
            context
        )

    except Exception as e:
        import traceback
        print(f"Personal rhythm render error: {e}")
        print(traceback.format_exc())

        # Return error state
        return render(
            request,
            'deep_dive/mystical/tarot_and_stats/mystic_rhythms/includes/personal_rhythm.html',
            {
                'error': True,
                'error_message': 'Unable to analyze patterns at this time',
                'insights': {'data_level': 'minimal'},
                'chart_data': json.dumps({}),
                'meta': {}
            }
        )


# ========================================
# TESTING ENDPOINT (Remove after testing)
# ========================================

@login_required
def test_rhythm_analysis(request):
    """
    Debug endpoint to test the pattern analyzer.
    Access via /deep-dive/test-rhythm/

    Shows raw JSON output for debugging.
    Remove this after testing.
    """
    analyzer = UserPatternAnalyzer(request.user)

    insights = analyzer.get_all_insights()
    chart_data = analyzer.get_visualization_data()

    # Pretty print for debugging
    import json
    output = {
        'user': request.user.username,
        'data_assessment': {
            'level': insights['data_level'],
            'journal_count': insights['journal_count'],
            'has_birth_chart': insights['has_birth_chart'],
            'meta': insights['meta']
        },
        'cosmic_rhythm': insights.get('cosmic_rhythm'),
        'journal_rhythm': insights.get('journal_rhythm'),
        'chart_data': chart_data
    }

    return JsonResponse(output, json_dumps_params={'indent': 2})




# ========================================
# TESTING ENDPOINT (Remove after testing)
# ========================================

@login_required
def test_rhythm_analysis(request):
    """
    Debug endpoint to test the pattern analyzer.
    Access via /deep-dive/test-rhythm/

    Shows raw JSON output for debugging.
    Remove this after testing.
    """
    analyzer = UserPatternAnalyzer(request.user)

    insights = analyzer.get_all_insights()
    chart_data = analyzer.get_visualization_data()

    # Pretty print for debugging
    import json
    output = {
        'user': request.user.username,
        'data_assessment': {
            'level': insights['data_level'],
            'journal_count': insights['journal_count'],
            'has_birth_chart': insights['has_birth_chart'],
            'meta': insights['meta']
        },
        'cosmic_rhythm': insights.get('cosmic_rhythm'),
        'journal_rhythm': insights.get('journal_rhythm'),
        'chart_data': chart_data
    }

    return JsonResponse(output, json_dumps_params={'indent': 2})


def mystical(request):
    """
    Main page - just renders the skeleton with HTMX load zones
    """
    return render(request, 'deep_dive/mystical/mystical.html', {
        'birth_setup_url': reverse('userprofile:birth_profile_setup')
    })


def moon_planets(request):
    """
    Returns moon phase + planetary data partial
    """
    # Get moon phase data from your existing service
    moon_data = get_moon_phase()

    # Get planetary positions from your existing service
    planetary_data = get_planetary_summary()



    return render(request, 'deep_dive/mystical/astronomicals/_moon_planets.html', {
        'moon_data': moon_data,
        'planetary_data': planetary_data
    })


# Helper class to wrap reading data with is_today check
class ReadingWrapper:
    def __init__(self, reading_dict, reading_type, ai_reading_obj):
        self.reading_text = reading_dict.get('reading_text', '')
        self.generated_at = reading_dict.get('generated_at')
        self.reading_type = reading_type
        self._ai_reading = ai_reading_obj

    @property
    def is_today(self):
        return self._ai_reading.is_today(self.reading_type)

@login_required
def birth_chart_view(request):
    """
    Main natal chart view - handles everything in one place.
    No need for separate unified_chart_modal view.
    """
    try:
        # Get user's birth profile
        birth_profile = BirthProfile.objects.get(user=request.user)

        # Get natal chart data
        natal_chart_data = birth_profile.cached_chart_data

        if not natal_chart_data:
            return render(request, 'deep_dive/mystical/astrology/birth_chart_container.html', {
                'error': 'No natal chart data available. Please generate your chart first.',
                'has_chart': False,
                'birth_setup_url': reverse('userprofile:birth_profile_setup'),
            })

        # Extract Big Three for summary
        sun_planet = next((p for p in natal_chart_data.get('planets', []) if p['name'] == 'Sun'), None)
        moon_planet = next((p for p in natal_chart_data.get('planets', []) if p['name'] == 'Moon'), None)
        rising_sign = natal_chart_data.get('ascendant', {}).get('sign', 'Unknown')

        # Prepare complete context
        context = {
            'birth_profile': birth_profile,
            'natal_chart': natal_chart_data,  # Contains: planets, aspects, houses, stelliums, retrogrades, chart_ruler, singletons, etc.
            'has_chart': True,
            'chart_info': {
                'sun_sign': sun_planet['sign'] if sun_planet else 'Unknown',
                'moon_sign': moon_planet['sign'] if moon_planet else 'Unknown',
                'rising_sign': rising_sign,
                'planet_count': len(natal_chart_data.get('planets', [])),
                'aspect_count': len(natal_chart_data.get('aspects', [])),
                'dominant_element': natal_chart_data.get('dominant_element', 'Spirit'),
            }
        }

        # Render EVERYTHING in one template
        return render(request, 'deep_dive/mystical/astrology/birth_chart_container.html', context)

    except BirthProfile.DoesNotExist:
        return render(request, 'deep_dive/mystical/astrology/birth_chart_container.html', {
            'error': 'No birth profile found. Please create your birth profile first.',
            'has_chart': False,
            'birth_setup_url': reverse('userprofile:birth_profile_setup')
        })
    except Exception as e:
        return render(request, 'deep_dive/mystical/astrology/birth_chart_container.html', {
            'error': f'Error loading chart data: {str(e)}',
            'has_chart': False,
            'birth_setup_url': reverse('userprofile:birth_profile_setup')
        })




@login_required
def save_planet_note(request, planet_name):
    """Saves planet note via HTMX"""
    # (Keep as-is from previous artifact)
    pass


def astro_birth_chart(request):
    """
    Returns birth chart preview section with chart data
    Handles 3 states: no profile, profile but no chart, chart exists
    """
    from userprofile.models import BirthProfile

    natal_chart = None
    birth_profile = None
    has_birth_profile = False
    has_birth_time = False

    if request.user.is_authenticated:
        try:
            birth_profile = request.user.birth_profile
            has_birth_profile = True
            has_birth_time = birth_profile.has_birth_time
            natal_chart = birth_profile.cached_chart_data
        except BirthProfile.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error loading birth profile: {e}")

    # Extract simple fields for template
    chart_context = {}
    if natal_chart:
        sun_planet = next((p for p in natal_chart.get('planets', []) if p['name'] == 'Sun'), None)
        moon_planet = next((p for p in natal_chart.get('planets', []) if p['name'] == 'Moon'), None)


        chart_context = {
            'sun_sign': sun_planet['sign'] if sun_planet else 'Unknown',
            'moon_sign': moon_planet['sign'] if moon_planet else 'Unknown',
            'rising_sign': natal_chart.get('ascendant', {}).get('sign', 'N/A'),
            'dominant_element': natal_chart.get('dominant_element', 'Spirit'),
            'planet_count': len(natal_chart.get('planets', [])),
            'aspect_count': len(natal_chart.get('aspects', [])),
        }

    return render(request, 'deep_dive/mystical/astrology/_birth_chart.html', {
        'has_birth_profile': has_birth_profile,
        'has_chart': natal_chart is not None,
        'has_birth_time': has_birth_time,
        'natal_chart_data': natal_chart,  # Keep as Python dict for template
        'natal_chart': json.dumps(natal_chart) if natal_chart else None,  # JSON for JS
        'chart_info': chart_context,
        'birth_setup_url': reverse('userprofile:birth_profile_setup')
    })


@login_required
def planet_meaning(request, planet_name):
    """
    Returns detailed astrological interpretation for a specific planet.
    Loads via HTMX into the General Meaning section.
    """
    try:
        birth_profile = BirthProfile.objects.get(user=request.user)
        natal_chart_data = birth_profile.cached_chart_data

        if not natal_chart_data:
            return HttpResponse(
                '<p class="text-red-400 text-sm">Chart data not available</p>',
                status=404
            )

        # Find the planet
        planet = next(
            (p for p in natal_chart_data.get('planets', []) if p['name'] == planet_name),
            None
        )

        if not planet:
            return HttpResponse(
                f'<p class="text-red-400 text-sm">Planet {planet_name} not found</p>',
                status=404
            )

        # Get aspects involving this planet
        planet_aspects = [
            aspect for aspect in natal_chart_data.get('aspects', [])
            if aspect['planet1'] == planet_name or aspect['planet2'] == planet_name
        ]

        # Generate interpretation based on planet placement
        interpretation = generate_planet_interpretation(
            planet_name=planet_name,
            sign=planet['sign'],
            house=planet.get('house'),
            degree=planet.get('degree'),
            is_retrograde=planet.get('is_retrograde', False),
            aspects=planet_aspects
        )

        context = {
            'planet': planet,
            'interpretation': interpretation,
            'planet_aspects': planet_aspects[:3],  # Show top 3 aspects
        }

        return render(
            request,
            'deep_dive/mystical/astrology/partials/planet_meaning.html',
            context
        )

    except BirthProfile.DoesNotExist:
        return HttpResponse(
            '<p class="text-red-400 text-sm">Birth profile not found</p>',
            status=404
        )
    except Exception as e:
        return HttpResponse(
            f'<p class="text-red-400 text-sm">Error: {str(e)}</p>',
            status=500
        )




# @login_required
# def planet_journals(request, planet_name):
#     """
#     Returns journal entries that match the user's natal planet placement.
#     Shows entries written when transiting planet was in same sign as natal.
#     """
#     from userprofile.models import BirthProfile
#     from journal.models import JournalEntry, DailyPlanetarySnapshot
#
#     try:
#         # Get user's natal chart
#         birth_profile = BirthProfile.objects.get(user=request.user)
#         natal_chart = birth_profile.cached_chart_data
#
#         if not natal_chart:
#             return render(request, 'deep_dive/mystical/astrology/partials/planet_journals.html', {
#                 'entries': [],
#                 'planet_name': planet_name,
#                 'error': 'No natal chart data available'
#             })
#
#         # Find the natal planet
#         natal_planet = next(
#             (p for p in natal_chart.get('planets', [])
#              if p['name'] == planet_name),
#             None
#         )
#
#         if not natal_planet:
#             return render(request, 'deep_dive/mystical/astrology/partials/planet_journals.html', {
#                 'entries': [],
#                 'planet_name': planet_name,
#                 'error': f'{planet_name} not found in natal chart'
#             })
#
#         natal_sign = natal_planet['sign']
#
#         # Find matching snapshot IDs
#         matching_snapshot_ids = []
#         snapshots = DailyPlanetarySnapshot.objects.all()
#
#         for snapshot in snapshots:
#             if not snapshot.planetary_data:
#                 continue
#
#             positions = snapshot.planetary_data.get('planetary_positions', [])
#
#             for planet in positions:
#                 if planet.get('name') == planet_name and planet.get('sign') == natal_sign:
#                     matching_snapshot_ids.append(snapshot.id)
#                     break
#
#         # Query entries efficiently
#         all_matching_entries = JournalEntry.objects.filter(
#             user=request.user,
#             planetary_snapshot_id__in=matching_snapshot_ids
#         ).select_related('planetary_snapshot').prefetch_related('tags').order_by('-created_at')
#
#         # Pagination
#         page_number = request.GET.get('page', 1)
#         items_per_page = 5
#         paginator = Paginator(all_matching_entries, items_per_page)
#         page_obj = paginator.get_page(page_number)
#
#         # Add match context to entries
#         for entry in page_obj:
#             entry.match_context = {
#                 'type': 'return',
#                 'description': f'{planet_name} in {natal_sign}',
#                 'natal_sign': natal_sign
#             }
#
#         # Calculate page range for display
#         page_range = get_page_range(page_obj.number, paginator.num_pages)
#
#         context = {
#             'entries': page_obj,
#             'planet_name': planet_name,
#             'natal_sign': natal_sign,
#             'total_entries': paginator.count,
#             'current_page': page_obj.number,
#             'total_pages': paginator.num_pages,
#             'has_previous': page_obj.has_previous(),
#             'has_next': page_obj.has_next(),
#             'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
#             'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
#             'page_range': page_range,
#         }
#
#         # If it's an HTMX request (pagination), return only the entries + pagination (partial)
#         # if request.headers.get('HX-Request'):
#         #     return render(
#         #         request,
#         #         'deep_dive/mystical/astrology/partials/_planet_journals_entries.html',
#         #         context
#         #     )
#
#         # Otherwise return the full template (wrapper)
#         return render(request, 'deep_dive/mystical/astrology/partials/planet_journals.html', context)
#
#     except BirthProfile.DoesNotExist:
#         return render(request, 'deep_dive/mystical/astrology/partials/planet_journals.html', {
#             'entries': [],
#             'planet_name': planet_name,
#             'error': 'No birth profile found'
#         })
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#
#         return render(request, 'deep_dive/mystical/astrology/partials/planet_journals.html', {
#             'entries': [],
#             'planet_name': planet_name,
#             'error': f'Error: {str(e)}'
#         })

@login_required
def planet_journals(request, planet_name):
    # 1. Fetch Natal Sign for the header context
    from userprofile.models import BirthProfile
    natal_sign = "Unknown"
    try:
        birth_profile = BirthProfile.objects.get(user=request.user)
        natal_chart = birth_profile.cached_chart_data
        natal_planet = next((p for p in natal_chart.get('planets', []) if p['name'] == planet_name.capitalize()), None)
        if natal_planet:
            natal_sign = natal_planet['sign']
    except Exception:
        pass

    # 2. Optimized Atomic Fetch
    # We use .prefetch_related('tags') to prevent N+1 queries in the card loop
    all_matching_entries = JournalEntry.objects.filter(
        user=request.user,
        coincidences__planet_key=planet_name.capitalize()
    ).select_related('planetary_snapshot').prefetch_related('tags').order_by('-created_at')

    # 3. Pagination Logic
    items_per_page = 5
    page_number = request.GET.get('page', 1)
    paginator = Paginator(all_matching_entries, items_per_page)
    page_obj = paginator.get_page(page_number)

    # 4. Context Building
    # We maintain the variable names your template expects
    context = {
        'entries': page_obj,  # This replaces the raw list with the Paginator object
        'planet_name': planet_name,
        'natal_sign': natal_sign,
        'total_entries': paginator.count,
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'page_range': get_page_range(page_obj.number, paginator.num_pages),
    }

    # 5. HTMX Support
    # If it's an HTMX request, we only return the entries + pagination
    if request.headers.get('HX-Request'):
        return render(
            request,
            'deep_dive/mystical/astrology/partials/planet_journals.html',
            context
        )

    return render(request, 'deep_dive/mystical/astrology/partials/planet_journals.html', context)


@login_required
def journal_entry_detail(request, entry_id):
    """
    Returns a single journal entry detail view with navigation context.
    """
    from journal.models import JournalEntry
    from userprofile.models import BirthProfile
    from journal.models import DailyPlanetarySnapshot

    try:
        entry = JournalEntry.objects.select_related(
            'planetary_snapshot'
        ).prefetch_related('tags').get(
            id=entry_id,
            user=request.user
        )

        # Get the context for navigation (planet and sign from query params)
        planet_name = request.GET.get('planet')
        natal_sign = request.GET.get('sign')

        # Initialize navigation variables
        current_index = None
        total_entries = None
        has_previous = False
        has_next = False
        previous_entry_id = None
        next_entry_id = None

        # Get all matching entries for pagination context
        if planet_name and natal_sign:
            try:
                birth_profile = BirthProfile.objects.get(user=request.user)
                natal_chart = birth_profile.cached_chart_data

                if natal_chart:
                    # Find matching snapshot IDs (same logic as planet_journals)
                    matching_snapshot_ids = []
                    snapshots = DailyPlanetarySnapshot.objects.all()

                    for snapshot in snapshots:
                        if not snapshot.planetary_data:
                            continue

                        positions = snapshot.planetary_data.get('planetary_positions', [])
                        for planet in positions:
                            if planet.get('name') == planet_name and planet.get('sign') == natal_sign:
                                matching_snapshot_ids.append(snapshot.id)
                                break

                    # Get all entries in order
                    all_entries = JournalEntry.objects.filter(
                        user=request.user,
                        planetary_snapshot_id__in=matching_snapshot_ids
                    ).order_by('-created_at').values_list('id', flat=True)

                    entry_ids = list(all_entries)

                    # Find current position
                    if entry_id in entry_ids:
                        current_index = entry_ids.index(entry_id) + 1
                        total_entries = len(entry_ids)

                        # Get previous and next entry IDs
                        has_previous = current_index > 1
                        has_next = current_index < total_entries

                        previous_entry_id = entry_ids[current_index - 2] if has_previous else None
                        next_entry_id = entry_ids[current_index] if has_next else None
            except BirthProfile.DoesNotExist:
                pass  # Navigation will be disabled

        context = {
            'entry': entry,
            'current_index': current_index,
            'total_entries': total_entries,
            'has_previous': has_previous,
            'has_next': has_next,
            'previous_entry_id': previous_entry_id,
            'next_entry_id': next_entry_id,
            'planet_name': planet_name,
            'natal_sign': natal_sign,
        }

        return render(
            request,
            'deep_dive/mystical/astrology/partials/_journal_entry_detail.html',
            context
        )

    except JournalEntry.DoesNotExist:
        return render(
            request,
            'deep_dive/mystical/astrology/partials/_journal_entry_detail.html',
            {'error': 'Journal entry not found'}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render(
            request,
            'deep_dive/mystical/astrology/partials/_journal_entry_detail.html',
            {'error': f'Error loading entry: {str(e)}'}
        )


# @login_required
# def planet_insights(request, planet_name):
#     """
#     Controller for the Planet Insights partial.
#     Responsible only for request handling and response rendering.
#     """
#     # 1. Fetch the analytical data from the Service
#     # (Assuming generate_planet_insight_data is imported from your services)
#     insight_data = generate_planet_insight_data(request.user, planet_name)
#
#     # 2. Handle the "No Data" state gracefully
#     if not insight_data:
#         return render(request, 'deep_dive/mystical/astrology/partials/_no_insights.html', {
#             'planet_name': planet_name
#         })
#
#     # 3. Prepare the final context
#     context = {
#         'planet_name': planet_name,
#         **insight_data  # Spreads out sign, house, theme, retro_percentage, etc.
#     }
#
#     # 4. Return the partial
#     return render(request, 'deep_dive/mystical/astrology/partials/planet_insights.html', context)

@login_required
def planet_insights(request, planet_name):
    """
    Controller for the Planet Insights partial.
    Data is cached at service level for efficiency.
    """
    insight_data = get_planet_insight(request.user, planet_name)

    # Handle no data state
    if not insight_data.get('has_data'):
        return render(request, 'deep_dive/mystical/astrology/partials/_no_insights.html', {
            'planet_name': planet_name,
            'message': insight_data.get('message'),
            'entry_count': insight_data.get('entry_count', 0)
        })

    context = {
        'planet_name': planet_name,
        **insight_data
    }

    return render(request, 'deep_dive/mystical/astrology/partials/planet_insights.html', context)


def astro_ai_readings(request):
    """
    Returns AI readings dashboard section
    Requires natal chart to be generated first
    """
    from userprofile.models import BirthProfile

    has_chart = False
    has_birth_profile = False

    # Initialize empty readings
    readings = {
        'daily_overview': None,
        'transit_focus': None,
        'element_wisdom': None,
    }

    if request.user.is_authenticated:
        # Check if user has a chart
        try:
            birth_profile = request.user.birth_profile
            has_birth_profile = True
            has_chart = birth_profile.cached_chart_data is not None
        except BirthProfile.DoesNotExist:
            pass

        # Load readings if chart exists
        if has_chart:
            try:
                current_reading = AIReading.objects.get(user=request.user)

                # Wrap each reading with is_today check
                if current_reading.has_reading_type('daily_overview'):
                    reading_data = current_reading.get_reading('daily_overview')
                    readings['daily_overview'] = ReadingWrapper(reading_data, 'daily_overview', current_reading)

                if current_reading.has_reading_type('transit_focus'):
                    reading_data = current_reading.get_reading('transit_focus')
                    readings['transit_focus'] = ReadingWrapper(reading_data, 'transit_focus', current_reading)

                if current_reading.has_reading_type('element_wisdom'):
                    reading_data = current_reading.get_reading('element_wisdom')
                    readings['element_wisdom'] = ReadingWrapper(reading_data, 'element_wisdom', current_reading)

            except AIReading.DoesNotExist:
                # No readings exist for this user yet
                pass

    return render(request, 'deep_dive/mystical/astrology/_ai_readings.html', {
        'has_chart': has_chart,
        'has_birth_profile': has_birth_profile,
        'daily_reading': readings['daily_overview'],
        'transit_reading': readings['transit_focus'],
        'element_reading': readings['element_wisdom'],
    })

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
import json


@login_required
def chart_details_modal(request):
    """
    Serves the unified chart modal with both Chart View and Data View tabs.
    Combines the functionality of the full chart visualization and tabular data.
    """
    from userprofile.models import BirthProfile

    try:
        # Get user's birth profile
        birth_profile = BirthProfile.objects.get(user=request.user)

        # Get natal chart data using cached_chart_data
        natal_chart_data = birth_profile.cached_chart_data

        if not natal_chart_data:
            return render(request, 'deep_dive/mystical/astrology/chart_details_modal.html', {
                'error': 'No natal chart data available. Please generate your chart first.',
                'has_chart': False,
                'birth_setup_url': reverse('userprofile:birth_profile_setup'),
                'no_chart': 'NO CHART'
            })

        # Get current planetary positions
        astro_service = AstronomicalService()
        current_planetary_data = astro_service.get_daily_planetary_summary()

        # Create a lookup dict for current positions by planet name and sign
        current_positions_lookup = {}
        for planet_pos in current_planetary_data.get('planetary_positions', []):
            planet_name = planet_pos['name']
            planet_sign = planet_pos['sign']
            current_positions_lookup[planet_name] = planet_sign

        # Mark natal planets that are currently active (same sign)
        for planet in natal_chart_data.get('planets', []):
            planet_name = planet['name']
            natal_sign = planet['sign']

            # Check if this planet is in the same sign currently
            if planet_name in current_positions_lookup:
                current_sign = current_positions_lookup[planet_name]
                planet['is_currently_active'] = (natal_sign == current_sign)
            else:
                planet['is_currently_active'] = False

        # Extract summary data for display
        sun_planet = next((p for p in natal_chart_data.get('planets', []) if p['name'] == 'Sun'), None)
        moon_planet = next((p for p in natal_chart_data.get('planets', []) if p['name'] == 'Moon'), None)
        rising_sign = natal_chart_data.get('ascendant', {}).get('sign', 'Unknown')

        # Prepare context
        context = {
            # 'birth_profile': birth_profile,
            'natal_chart': natal_chart_data,
            'current_planetary_data': current_planetary_data,
            'current_positions_lookup': current_positions_lookup,
            'has_chart': True,
            'sun_sign': sun_planet['sign'] if sun_planet else 'Unknown',
            'moon_sign': moon_planet['sign'] if moon_planet else 'Unknown',
            'rising_sign': rising_sign,
            'planet_count': len(natal_chart_data.get('planets', [])),
            'aspect_count': len(natal_chart_data.get('aspects', [])),
            'dominant_element': natal_chart_data.get('dominant_element', 'Spirit'),
        }

        return render(request, 'deep_dive/mystical/astrology/chart_details_modal.html', context)

    except BirthProfile.DoesNotExist:
        return render(request, 'deep_dive/mystical/astrology/chart_details_modal.html', {
            'error': 'No birth profile found. Please create your birth profile first.',
            'has_chart': False,
            'birth_setup_url': reverse('userprofile:birth_profile_setup')
        })
    except Exception as e:
        return render(request, 'deep_dive/mystical/astrology/chart_details_modal.html', {
            'error': f'Error loading chart data: {str(e)}',
            'has_chart': False,
            'birth_setup_url': reverse('userprofile:birth_profile_setup')
        })



# Optional: Keep these existing detail views for HTMX interactions in Data View tab
@login_required
def planet_detail(request, planet_name):
    """
    Returns detailed information about a specific planet.
    Used by HTMX in both Chart View and Data View tabs.
    """
    try:
        birth_profile = BirthProfile.objects.get(user=request.user)
        natal_chart = birth_profile.cached_chart_data

        if not natal_chart:
            return JsonResponse({'error': 'No chart data'}, status=404)

        # Find the planet
        planet = next((p for p in natal_chart['planets'] if p['name'] == planet_name), None)

        if not planet:
            return JsonResponse({'error': 'Planet not found'}, status=404)

        # Find aspects involving this planet
        planet_aspects = [
            aspect for aspect in natal_chart.get('aspects', [])
            if aspect['planet1'] == planet_name or aspect['planet2'] == planet_name
        ]

        # Planet meanings and descriptions
        planet_meanings = {
            'Sun': 'Core Identity & Life Force',
            'Moon': 'Emotions & Inner Self',
            'Mercury': 'Communication & Mind',
            'Venus': 'Love & Values',
            'Mars': 'Action & Desire',
            'Jupiter': 'Growth & Expansion',
            'Saturn': 'Structure & Discipline',
            'Uranus': 'Innovation & Change',
            'Neptune': 'Dreams & Spirituality',
            'Pluto': 'Transformation & Power',
        }

        element_descriptions = {
            'Fire': 'Dynamic, passionate, and action-oriented energy',
            'Earth': 'Practical, grounded, and material-focused energy',
            'Air': 'Intellectual, communicative, and social energy',
            'Water': 'Emotional, intuitive, and feeling-oriented energy',
        }

        context = {
            # 'planet': planet,
            # 'aspects': planet_aspects,
            # 'planet_meaning': planet_meanings.get(planet_name, 'Celestial body'),
            # 'element_description': element_descriptions.get(planet.get('element'), ''),
        }

        return render(request, 'deep_dive/mystical/astrology/chart_modals/_planet_detail.html', context)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def aspect_detail(request, planet1, planet2, aspect_type):
    """
    Returns detailed information about a specific aspect.
    Used by HTMX in both Chart View and Data View tabs.
    """
    try:
        birth_profile = BirthProfile.objects.get(user=request.user)
        natal_chart = birth_profile.cached_chart_data

        if not natal_chart:
            return JsonResponse({'error': 'No chart data'}, status=404)

        # Find the aspect
        aspect = next((
            a for a in natal_chart.get('aspects', [])
            if ((a['planet1'] == planet1 and a['planet2'] == planet2) or
                (a['planet1'] == planet2 and a['planet2'] == planet1)) and
               a['aspect_type'] == aspect_type
        ), None)

        if not aspect:
            return JsonResponse({'error': 'Aspect not found'}, status=404)

        # Get full planet data
        planet1_data = next((p for p in natal_chart['planets'] if p['name'] == planet1), None)
        planet2_data = next((p for p in natal_chart['planets'] if p['name'] == planet2), None)

        # Generate specific interpretation for this planetary combination
        aspect_interp = generate_aspect_interpretation(
            planet1,
            planet2,
            aspect_type,
            aspect.get('orb', 0)
        )

        # Comprehensive aspect metadata
        aspect_meanings = {
            'Conjunction': {
                'symbol': '☌',
                'angle': '0°',
                'description': 'A powerful blending of planetary energies where two planets unite as one force.',
                'detailed': 'The conjunction represents the most intense aspect, where planetary energies merge completely. This creates a concentrated point of power in your chart, making these planets work as a unified team. The effects can be amplified for better or worse, depending on the planets involved.',
                'keywords': 'Unity, Fusion, Intensity, Synthesis, Concentration',
                'influence': 'Strong and direct impact on personality and life themes.',
                'nature': 'Neutral to Powerful',
                'color': 'yellow',
                'energy': 'Maximum intensity and focus',
                'challenge': 'May lack objectivity; planets can overshadow each other',
                'gift': 'Powerful unified expression; concentrated energy for manifestation',
            },
            'Opposition': {
                'symbol': '☍',
                'angle': '180°',
                'description': 'A dynamic tension between opposing forces creating awareness through polarity.',
                'detailed': 'The opposition pulls you in two directions, creating a see-saw effect that demands balance. This aspect brings external awareness through relationships and projections. You may experience these energies as coming from "out there" until you learn to integrate both sides within yourself.',
                'keywords': 'Polarity, Balance, Awareness, Projection, Integration',
                'influence': 'Creates awareness through contrast and relationship dynamics.',
                'nature': 'Challenging',
                'color': 'red',
                'energy': 'Pull between two extremes; seek middle ground',
                'challenge': 'Can feel torn between conflicting needs or projected onto others',
                'gift': 'Heightened awareness; ability to see multiple perspectives; relationship wisdom',
            },
            'Trine': {
                'symbol': '△',
                'angle': '120°',
                'description': 'A harmonious flow of energy representing natural talents and gifts.',
                'detailed': 'The trine is the aspect of ease and natural ability. These planets support each other effortlessly, creating talents that feel innate. However, because this energy flows so smoothly, there can be a tendency to take these gifts for granted or not develop them fully.',
                'keywords': 'Harmony, Flow, Talent, Ease, Natural Gifts',
                'influence': 'Supportive aspect that enhances natural abilities and self-expression.',
                'nature': 'Harmonious',
                'color': 'green',
                'energy': 'Smooth, flowing, effortless cooperation',
                'challenge': 'May lead to complacency; gifts can be underutilized',
                'gift': 'Natural talents; things come easily; inner harmony and confidence',
            },
            'Square': {
                'symbol': '□',
                'angle': '90°',
                'description': 'A dynamic challenge that creates friction and motivates action.',
                'detailed': 'The square represents internal tension that drives growth through challenge. These planets are in conflict, creating a motivating friction that pushes you to take action. While uncomfortable, squares are often responsible for the greatest personal development and achievement.',
                'keywords': 'Challenge, Growth, Motivation, Friction, Action',
                'influence': 'Creates productive tension that drives development and achievement.',
                'nature': 'Challenging',
                'color': 'orange',
                'energy': 'Dynamic tension; catalyst for action and growth',
                'challenge': 'Feels like internal struggle; requires effort to resolve',
                'gift': 'Builds strength through adversity; motivates achievement and mastery',
            },
            'Sextile': {
                'symbol': '⚹',
                'angle': '60°',
                'description': 'Opportunities for growth through conscious effort and skill development.',
                'detailed': 'The sextile offers supportive energy that requires some initiative to activate. Unlike the trine, which flows automatically, the sextile rewards conscious effort and provides opportunities when you take action. It represents skills that can be developed with practice.',
                'keywords': 'Opportunity, Cooperation, Skill, Support, Development',
                'influence': 'Supportive aspect that requires initiative to activate opportunities.',
                'nature': 'Harmonious',
                'color': 'blue',
                'energy': 'Cooperative and supportive when engaged',
                'challenge': 'Opportunities can be missed if not actively pursued',
                'gift': 'Accessible talents; supportive connections; learnable skills',
            },
            'Quincunx': {
                'symbol': '⚻',
                'angle': '150°',
                'description': 'A subtle tension requiring adjustment and adaptation between incompatible energies.',
                'detailed': 'The quincunx (or inconjunct) connects planets that have nothing in common by element or modality. This creates a persistent sense of unease that requires constant adjustment. These energies don\'t naturally understand each other, requiring creative solutions and flexibility.',
                'keywords': 'Adjustment, Adaptation, Tension, Incompatibility, Creativity',
                'influence': 'Creates a need for continual adaptation and creative problem-solving.',
                'nature': 'Minor Challenging',
                'color': 'purple',
                'energy': 'Awkward, requires constant micro-adjustments',
                'challenge': 'Feels like trying to fit square peg in round hole',
                'gift': 'Develops flexibility; unique solutions; creative adaptability',
            },
            'Semisquare': {
                'symbol': '∠',
                'angle': '45°',
                'description': 'A minor irritation that creates subtle tension and motivation.',
                'detailed': 'A softer version of the square, the semisquare creates a background friction that can manifest as minor irritations or nagging tensions. While less intense, it still provides motivating energy for growth and change.',
                'keywords': 'Friction, Irritation, Minor Challenge, Motivation',
                'influence': 'Subtle tension that builds over time, motivating gradual change.',
                'nature': 'Minor Challenging',
                'color': 'orange',
                'energy': 'Low-level friction; persistent subtle tension',
                'challenge': 'Can manifest as minor but persistent annoyances',
                'gift': 'Gentle push toward growth without overwhelming pressure',
            },
            'Sesquisquare': {
                'symbol': '□∠',
                'angle': '135°',
                'description': 'A minor challenging aspect creating restlessness and need for release.',
                'detailed': 'Also called the sesquiquadrate, this aspect creates a buildup of tension that seeks release through action. It\'s less confrontational than a square but can manifest as internal restlessness or impatience.',
                'keywords': 'Restlessness, Release, Impatience, Action',
                'influence': 'Creates building tension that needs periodic release through action.',
                'nature': 'Minor Challenging',
                'color': 'orange',
                'energy': 'Building pressure seeking outlet',
                'challenge': 'Can lead to impulsive actions or frustration',
                'gift': 'Motivates taking action; prevents stagnation',
            }
        }

        # Get metadata for this aspect type
        meaning = aspect_meanings.get(aspect_type, {
            'symbol': '?',
            'angle': 'Variable',
            'description': 'A unique aspect between these planets.',
            'detailed': 'This is a less common aspect in astrology.',
            'keywords': 'Unique, Specialized',
            'influence': 'Specific to this planetary combination.',
            'nature': 'Variable',
            'color': 'slate',
            'energy': 'Depends on planets involved',
            'challenge': 'Interpretation varies',
            'gift': 'Unique expression of planetary energies',
        })

        # Calculate aspect strength based on orb
        orb = float(aspect.get('orb', 0))
        if orb <= 1:
            strength = 'Very Strong'
            strength_color = 'emerald'
        elif orb <= 3:
            strength = 'Strong'
            strength_color = 'green'
        elif orb <= 5:
            strength = 'Moderate'
            strength_color = 'blue'
        elif orb <= 7:
            strength = 'Weak'
            strength_color = 'slate'
        else:
            strength = 'Very Weak'
            strength_color = 'slate'

        context = {
            'aspect': aspect,
            'planet1': planet1_data,
            'planet2': planet2_data,
            'meaning': meaning,
            'strength': strength,
            'strength_color': strength_color,
            'specific_interpretation': aspect_interp,  # Add the specific interpretation
        }

        return render(request, 'deep_dive/mystical/astrology/chart_modals/_aspect_detail.html', context)

    except BirthProfile.DoesNotExist:
        return JsonResponse({'error': 'Birth profile not found'}, status=404)
    except Exception as e:
        logger.error(f"Error loading aspect detail: {str(e)}")
        return JsonResponse({'error': 'Failed to load aspect details'}, status=500)


# @login_required
# def house_detail(request, house_number):
#     """
#     Returns detailed information about a specific house.
#     Used by HTMX in the Data View tab.
#     """
#     try:
#         birth_profile = request.user.birthprofile
#         natal_chart = birth_profile.natal_chart
#
#         if not natal_chart:
#             return JsonResponse({'error': 'No chart data'}, status=404)
#
#         chart_data = natal_chart.chart_data
#
#         # Find the house
#         house = next((h for h in chart_data['houses'] if h['house_number'] == house_number), None)
#
#         if not house:
#             return JsonResponse({'error': 'House not found'}, status=404)
#
#         # Find planets in this house
#         planets_in_house = [
#             p for p in chart_data['planets']
#             if p.get('house') == house_number
#         ]
#
#         context = {
#             'house': house,
#             'planets': planets_in_house,
#         }
#
#         return render(request, 'deep_dive/mystical/partials/house_detail.html', context)
#
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)





def view_reading(request, reading_type):
    """Load a reading into the view modal"""
    reading = None
    valid_reading_types = ['daily_overview', 'transit_focus', 'element_wisdom']

    if request.user.is_authenticated and reading_type in valid_reading_types:
        try:
            ai_reading_instance = AIReading.objects.get(user=request.user)
            reading = ai_reading_instance.get_reading(reading_type)
        except AIReading.DoesNotExist:
            reading = None

    return render(request, 'deep_dive/mystical/astrology/includes/reading_view_modal.html', {
        'reading': reading,
        'reading_type': reading_type,  # Pass the type to template for context
    })


@login_required
def interactive_mystical(request):
    """
    Render the interactive mystical elements section.
    Checks if user has drawn a card today and pre-populates it.
    NOW INCLUDES: Personal Rhythm preview data
    """
    from datetime import date
    from django.utils.timesince import timesince
    from ..models import TarotCardDraw
    from ..services.mystical.pattern_analyzer_svc import UserPatternAnalyzer
    import json

    # Check if user drew a card today
    today_card = TarotCardDraw.objects.filter(
        user=request.user,
        drawn_at__date=date.today()
    ).first()

    # Prepare context
    context = {
        'has_drawn_today': bool(today_card),
    }

    # If card exists, add its data
    if today_card:
        context.update({
            'card_number': today_card.card_number,
            'card_emoji': today_card.emoji,
            'card_title': today_card.card_name,
            'card_keywords': today_card.keywords,
            'card_interpretation': today_card.interpretation,
            'card_astro_context': today_card.astro_context,
            'card_natal_insight': today_card.natal_insight,
            'drawn_time_ago': timesince(today_card.drawn_at),
        })

    # Add Personal Rhythm preview data
    try:
        analyzer = UserPatternAnalyzer(request.user)
        insights = analyzer.get_all_insights()

        context.update({
            'insights': insights,
            'meta': insights['meta']
        })
    except Exception as e:
        print(f"Error loading rhythm preview: {e}")
        # Provide fallback data
        context.update({
            'insights': {
                'data_level': 'minimal',
                'journal_count': 0,
                'cosmic_rhythm': {'moon': {'emoji': '🌙', 'phase': 'Unknown'}},
            },
            'meta': {'level_name': 'Minimal'}
        })

    return render(request, 'deep_dive/mystical/tarot_and_stats/_interactive_mystical.html', context)
    # """
    # Render the personal rhythm section HTML.
    # This replaces the biorhythm section in your template.
    # """
    import json

    try:
        analyzer = UserPatternAnalyzer(request.user)
        insights = analyzer.get_all_insights()
        chart_data = analyzer.get_visualization_data()

        context = {
            'insights': insights,
            'chart_data': json.dumps(chart_data),  # Convert to JSON for JavaScript
            'data_level': insights['data_level'],
            'meta': insights['meta']
        }

        return render(
            request,
            'deep_dive/mystical/tarot_and_stats/mystic_rhythms/includes/personal_rhythm.html',
            context
        )

    except Exception as e:
        import traceback
        print(f"Personal rhythm render error: {e}")
        print(traceback.format_exc())

        # Return error state
        return render(
            request,
            'deep_dive/mystical/tarot_and_stats/mystic_rhythms/includes/personal_rhythm.html',
            {
                'error': True,
                'error_message': 'Unable to analyze patterns at this time',
                'insights': {'data_level': 'minimal'},
                'chart_data': json.dumps({}),
                'meta': {}
            }
        )
    # """
    # Render the interactive mystical elements section.
    # Checks if user has drawn a card today and pre-populates it.
    # """
    from datetime import date
    from django.utils.timesince import timesince
    from ..models import TarotCardDraw

    # Check if user drew a card today
    today_card = TarotCardDraw.objects.filter(
        user=request.user,
        drawn_at__date=date.today()
    ).first()

    # Prepare context
    context = {
        'has_drawn_today': bool(today_card),
    }

    # If card exists, add its data
    if today_card:
        context.update({
            'card_number': today_card.card_number,
            'card_emoji': today_card.emoji,
            'card_title': today_card.card_name,
            'card_keywords': today_card.keywords,
            'card_interpretation': today_card.interpretation,
            'card_astro_context': today_card.astro_context,
            'card_natal_insight': today_card.natal_insight,
            'drawn_time_ago': timesince(today_card.drawn_at),  # ← NEW
        })

    return render(request, 'deep_dive/mystical/tarot_and_stats/_interactive_mystical.html', context)


from django.views.decorators.http import require_POST
from django.http import JsonResponse


@require_POST
def generate_natal_chart(request):
    """
    Generates natal chart for user with existing birth profile
    """
    if not request.user.is_authenticated:
        return HttpResponse("Please log in", status=401)

    try:
        from userprofile.models import BirthProfile
        import json

        # Get birth profile
        birth_profile = request.user.birth_profile

        # Calculate using the service directly
        service = NatalChartService(birth_profile)
        natal_chart = service.generate_natal_chart()

        # Cache the result
        birth_profile.cached_chart_data = natal_chart
        birth_profile.save(update_fields=['cached_chart_data'])

        if natal_chart:
            sun_planet = next((p for p in natal_chart.get('planets', []) if p['name'] == 'Sun'), None)
            moon_planet = next((p for p in natal_chart.get('planets', []) if p['name'] == 'Moon'), None)

            chart_context = {
                'sun_sign': sun_planet['sign'] if sun_planet else 'Unknown',
                'moon_sign': moon_planet['sign'] if moon_planet else 'Unknown',
                'rising_sign': natal_chart.get('ascendant', {}).get('sign', 'N/A'),
                'dominant_element': natal_chart.get('dominant_element', 'Spirit'),
                'planet_count': len(natal_chart.get('planets', [])),
                'aspect_count': len(natal_chart.get('aspects', [])),
            }
        # Prepare context
        context = {
            'has_chart': True,
            'has_birth_profile': True,
            'natal_chart': json.dumps(natal_chart),  # JSON string for the script tag
            'daily_reading': None,  # Add if you have these
            'transit_reading': None,
            'element_reading': None,
            'chart_info': chart_context,
        }

        # Return the partial template
        return render(request, 'deep_dive/mystical/astrology/_birth_chart.html', context)

    except BirthProfile.DoesNotExist:
        return HttpResponse("Birth profile not found. Please create one first.", status=404)
    except Exception as e:
        print(f"Error generating natal chart: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error generating chart: {str(e)}", status=500)



def get_tarot_card_data():
    """
    Get tarot card data based on current moon phase or random draw
    """
    # You can connect this to moon phase or make it random
    return {
        'emoji': '🌙',
        'title': 'The Moon',
        'keywords': 'Intuition • Dreams • Subconscious',
        'description': 'Tap to reveal today\'s mystical guidance based on current lunar energy'
    }


def get_mood_chart_data(user):
    """
    Get mood chart data from user's journal entries or other sources
    Returns list of numbers for the chart
    """
    # Replace with actual query to journal entries or mood tracking
    # This should return 8 values corresponding to the 8 moon phases

    if not user:
        return [12, 19, 15, 22, 28, 24, 18, 14]

    # Example: Query journal entries grouped by moon phase
    # journal_counts = user.journalentry_set.values('moon_phase').annotate(count=Count('id'))

    # For now, return sample data
    return [12, 19, 15, 22, 28, 24, 18, 14]



def moon_phase_api(request):
    """Simple function that returns moon data as JSON"""
    moon_data = get_moon_phase()  # Your existing function!
    print(f'MOON DATA:{moon_data}')
    return JsonResponse(moon_data)

def planetary_api(request):
    """Simple function that returns planet data as JSON"""
    timezone = request.GET.get('timezone', 'UTC')
    planet_data = get_planetary_summary(timezone)  # Your existing function!
    return JsonResponse(planet_data)


# deep_dive/views.py
# Add these views to your existing views.py

# deep_dive/views.py
# Add these views to your existing views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from ..models import AIReading
from ..services.mystical.ai_chart_reading_svc import generate_reading


@require_http_methods(["POST"])
@login_required
def generate_ai_reading(request):
    """
    Generate an AI reading based on user's natal chart.
    Cached daily - only generates once per day per reading type.

    POST params:
        reading_type: 'daily_overview' | 'transit_focus' | 'element_wisdom'
        force_refresh: 'true' to bypass cache
        modal_view: 'true' if regenerating from modal
    """
    reading_type = request.POST.get('reading_type', 'daily_overview')
    force_refresh = request.POST.get('force_refresh', 'false') == 'true'
    modal_view = request.POST.get('modal_view', 'false') == 'true'
    user = request.user

    # Validate reading type
    valid_types = ['daily_overview', 'transit_focus', 'element_wisdom']
    if reading_type not in valid_types:
        return JsonResponse({
            'error': 'Invalid reading type'
        }, status=400)

    try:
        # Get user's natal chart from birth profile
        birth_profile = request.user.birth_profile
        natal_chart = birth_profile.cached_chart_data

        if not natal_chart:
            return JsonResponse({
                'error': 'No natal chart data found. Please generate your chart first.'
            }, status=404)

        # Get or create user's reading collection
        ai_reading, created = AIReading.objects.get_or_create(user=request.user)

        # Check if reading already exists and is from today
        from_cache = False
        if not force_refresh and ai_reading.is_today(reading_type):
            print(f"{reading_type} already generated today - using cached version")
            from_cache = True
        else:
            # Generate fresh reading
            print(f"Generating fresh {reading_type} for {request.user.username}")
            reading_data = generate_reading(natal_chart, reading_type, user)  # Pass user here!

            print(f"Generated reading_data keys: {reading_data.keys()}")
            print(f"transit_summaries exists: {'transit_summaries' in reading_data}")
            print(f"transit_summaries value: {reading_data.get('transit_summaries')}")
            print(f"transit_summaries type: {type(reading_data.get('transit_summaries'))}")

            # Update the specific reading type
            ai_reading.update_reading(reading_type, reading_data)
            ai_reading.refresh_from_db()



        # Get the updated reading data
        updated_reading = ai_reading.get_reading(reading_type)
        print(f"After save - reading keys: {updated_reading.keys() if updated_reading else 'None'}")
        print(f"After save - transit_summaries: {updated_reading.get('transit_summaries') if updated_reading else 'None'}")
        # print(updated_reading.reading_text)
        # If this is a modal view request, return the updated modal
        if modal_view:
            return render(request, 'deep_dive/mystical/astrology/includes/reading_view_modal.html', {
                'reading': updated_reading,
                'from_cache': from_cache
            })

        # Otherwise, return the dashboard section as before
        # Build readings dictionary for template with wrapper objects
        readings = {
            'daily_overview': None,
            'transit_focus': None,
            'element_wisdom': None,
        }

        # Populate available readings with wrapper objects
        for reading_key in readings.keys():
            if ai_reading.has_reading_type(reading_key):
                reading_data = ai_reading.get_reading(reading_key)
                readings[reading_key] = ReadingWrapper(reading_data, reading_key, ai_reading)

        # Return updated reading section HTML
        return render(request, 'deep_dive/mystical/astrology/includes/_ai_reading_dashboard_partial.html', {
            'daily_reading': readings['daily_overview'],
            'transit_reading': readings['transit_focus'],
            'element_reading': readings['element_wisdom'],
        })

    except AttributeError:
        return JsonResponse({
            'error': 'No birth profile found. Please create your birth profile first.'
        }, status=404)

    except Exception as e:
        import traceback
        print(f"Reading generation error: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': f'Failed to generate reading: {str(e)}'
        }, status=500)


@login_required
def get_reading_options(request):
    """
    Return the reading type selection modal/menu.
    User clicks to choose which type of reading to generate.
    """
    return render(request, 'deep_dive/mystical/partials/reading_options_modal.html')


@login_required
def refresh_reading_display(request):
    """
    Refresh the reading display without regenerating.
    Shows the most recent reading of any type.
    """
    try:
        # Get user's birth profile to check if chart exists
        birth_profile = request.user.birth_profile
        natal_chart = birth_profile.cached_chart_data
        has_chart = natal_chart is not None
    except AttributeError:
        has_chart = False

    try:
        ai_reading = AIReading.objects.get(user=request.user)
        latest = ai_reading.get_latest_reading()

        if latest:
            return render(request, 'deep_dive/mystical/partials/ai_reading_content.html', {
                'reading': latest,
                'just_generated': False
            })
        else:
            return render(request, 'deep_dive/mystical/partials/ai_reading_placeholder.html', {
                'has_chart': has_chart
            })
    except AIReading.DoesNotExist:
        return render(request, 'deep_dive/mystical/partials/ai_reading_placeholder.html', {
            'has_chart': has_chart
        })


# deep_dive/views/mystical_views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from datetime import date
import random

from ..models import TarotCardDraw
from ..services.mystical.tarot_deck import COSMIC_TAROT_DECK
from ..services.mystical.tarot_natal_svc import TarotNatalService, ThreeCardSpreadService
from ..services.mystical.ai_chart_reading_svc import TransitCalculator
from ..services.mystical.astronomical_svc import AstronomicalService


def _get_natal_and_transits(user):
    """
    Shared helper: fetch natal chart + today's transits from snapshot.

    Returns:
        (natal_chart dict, transits list)
        transits will be [] if snapshot missing or transit calc fails.
    """
    birth_profile = BirthProfile.objects.get(user=user)
    natal_chart = birth_profile.cached_chart_data

    if not natal_chart:
        raise ValueError('No natal chart data found. Please generate your chart first.')

    try:
        snapshot = DailyPlanetarySnapshot.get_or_create_for_date(date.today())
        current_positions = snapshot.planetary_data.get('planetary_positions', [])
        transit_calc = TransitCalculator(natal_chart)
        transits = transit_calc.calculate_transits(current_positions)
    except Exception as e:
        print(f"Transit calculation failed: {e}")
        transits = []

    return natal_chart, transits


# ============================================================
# DAILY DRAW
# ============================================================

@login_required
def draw_tarot_card(request):
    """
    POST: Draw today's daily tarot card.
    One card per day — checks DB before drawing.
    Returns JSON for JS to update the UI.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        # 1. Check if already drawn today
        today_draw = TarotCardDraw.objects.filter(
            user=request.user,
            drawn_at__date=date.today()
        ).first()

        if today_draw:
            return JsonResponse({
                'error': 'You have already drawn your card for today. Return tomorrow for a new reading!'
            }, status=400)

        # 2. Get natal chart + transits
        natal_chart, transits = _get_natal_and_transits(request.user)

        # 3. Initialize service
        tarot_service = TarotNatalService(natal_chart)
        dominant_planet = tarot_service.get_dominant_planetary_energy()

        # 4. Select card
        if transits:
            selected_card = tarot_service.select_card_by_transits(transits, COSMIC_TAROT_DECK)
        else:
            dominant_elem = natal_chart.get('dominant_element', 'Earth')
            elem_cards = [c for c in COSMIC_TAROT_DECK if c.get('element') == dominant_elem]
            selected_card = random.choice(elem_cards) if elem_cards else random.choice(COSMIC_TAROT_DECK)

        # 5. Personalize
        interpretation = tarot_service.personalize_interpretation(
            selected_card['base_interpretation'], dominant_planet
        )
        natal_insight = tarot_service.generate_natal_insight(selected_card)
        astro_context = tarot_service.generate_astro_context(selected_card, transits)

        # 6. Save
        TarotCardDraw.objects.create(
            user=request.user,
            card_number=selected_card['card_number'],
            card_name=selected_card['title'],
            emoji=selected_card['emoji'],
            keywords=selected_card['keywords'],
            interpretation=interpretation,
            astro_context=astro_context,
            natal_insight=natal_insight,
        )

        print(f"✨ {request.user.username} drew: {selected_card['title']}")

        return JsonResponse({
            'card_number': selected_card['card_number'],
            'title': selected_card['title'],
            'emoji': selected_card['emoji'],
            'keywords': selected_card['keywords'],
            'interpretation': interpretation,
            'astro_context': astro_context,
            'natal_insight': natal_insight,
        })

    except BirthProfile.DoesNotExist:
        return JsonResponse({'error': 'No birth profile found. Please create your birth profile first.'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Failed to draw card: {str(e)}'}, status=500)


# ============================================================
# CARD HISTORY
# ============================================================

def _calculate_current_streak(draw_dates):
    """Count consecutive daily draws ending today or yesterday."""
    if not draw_dates:
        return 0

    today = now().date()
    streak = 0
    current_day = today

    for d in draw_dates:
        if d == current_day:
            streak += 1
            current_day -= timedelta(days=1)
        else:
            break

    return streak


@login_required
def tarot_card_history(request):
    """
    GET: Returns history partial for the card history modal.
    Last 30 draws + streak count.
    """
    all_draws = TarotCardDraw.objects.filter(user=request.user).order_by('-drawn_at')
    draw_dates = sorted({d.drawn_at.date() for d in all_draws}, reverse=True)
    current_streak = _calculate_current_streak(draw_dates)

    draws = all_draws[:30]

    return render(request, 'deep_dive/mystical/tarot/_tarot_history.html', {
        'draws': draws,
        'total_draws': all_draws.count(),
        'current_streak': current_streak,
    })


# ============================================================
# TAROT SPREAD (modal, session-only)
# ============================================================

@login_required
def tarot_spread(request):
    """
    GET: Returns the initial spread modal content (face-down cards + intention form).
        Called every time the modal opens — resets state cleanly.

    POST: Generates and returns the spread result partial.
        Swapped into the same modal container.
    """
    if request.method == 'GET':
        return render(request, 'deep_dive/mystical/tarot/_tarot_spread.html')

    # POST — generate spread, return JSON
    try:
        natal_chart, transits = _get_natal_and_transits(request.user)
        user_intention = request.POST.get('intention', '').strip()

        spread_service = ThreeCardSpreadService(natal_chart, transits, user_intention)
        past_card, present_card, future_card = spread_service.generate_spread(COSMIC_TAROT_DECK)

        tarot_service = TarotNatalService(natal_chart)
        dominant_planet = tarot_service.get_dominant_planetary_energy()

        def card_data(card):
            return {
                'card_number': card['card_number'],
                'title': card['title'],
                'emoji': card['emoji'],
                'keywords': card['keywords'],
                'interpretation': tarot_service.personalize_interpretation(
                    card['base_interpretation'], dominant_planet
                ),
            }

        return JsonResponse({
            'past': card_data(past_card),
            'present': card_data(present_card),
            'future': card_data(future_card),
            'reading_summary': spread_service.generate_spread_narrative(
                past_card, present_card, future_card
            ),
            'user_intention': user_intention,
        })

    except BirthProfile.DoesNotExist:
        return JsonResponse({'error': 'No birth profile found.'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def tarot_main(request):
    """
    Renders the main Tarot tab content.
    Checks if user has drawn today and pre-populates card data if so.
    """
    from datetime import date
    from django.utils.timesince import timesince
    from ..models import TarotCardDraw

    today_card = TarotCardDraw.objects.filter(
        user=request.user,
        drawn_at__date=date.today()
    ).first()

    context = {
        'has_drawn_today': bool(today_card),
    }

    if today_card:
        context.update({
            'card_number': today_card.card_number,
            'card_emoji': today_card.emoji,
            'card_title': today_card.card_name,
            'card_keywords': today_card.keywords,
            'card_interpretation': today_card.interpretation,
            'card_astro_context': today_card.astro_context,
            'card_natal_insight': today_card.natal_insight,
            'drawn_time_ago': timesince(today_card.drawn_at),
        })

    return render(request, 'deep_dive/mystical/tarot/_tarot_main.html', context)

# @login_required
# def draw_tarot_card(request):
#     """
#     Draw a daily tarot card based on natal chart + current transits.
#     One card per day - cached daily like AI readings.
#
#     Process:
#     1. Check if already drawn today
#     2. Get natal chart + current transits
#     3. Use TarotNatalService to select & personalize card
#     4. Save to database
#     5. Return card data as JSON
#     """
#
#     if request.method != 'POST':
#         return JsonResponse({'error': 'POST required'}, status=405)
#
#     try:
#         # ============================================
#         # 1. GET USER'S NATAL CHART
#         # ============================================
#         birth_profile = request.user.birth_profile
#         natal_chart = birth_profile.cached_chart_data
#
#         if not natal_chart:
#             return JsonResponse({
#                 'error': 'No natal chart data found. Please generate your chart first.'
#             }, status=404)
#
#         # ============================================
#         # 2. CHECK IF ALREADY DRAWN TODAY
#         # ============================================
#         today_draw = TarotCardDraw.objects.filter(
#             user=request.user,
#             drawn_at__date=date.today()
#         ).first()
#
#         if today_draw:
#             return JsonResponse({
#                 'error': 'You have already drawn your card for today. Return tomorrow for a new reading!'
#             }, status=400)
#
#         # ============================================
#         # 3. GET CURRENT TRANSITS
#         # ============================================
#         try:
#             # Use your existing services
#             astro_service = AstronomicalService()
#             current_positions = astro_service.get_daily_planetary_summary()
#
#             transit_calc = TransitCalculator(natal_chart)
#             transits = transit_calc.calculate_transits(
#                 current_positions['planetary_positions']
#             )
#         except Exception as e:
#             print(f"Transit calculation failed: {e}")
#             transits = []  # Continue without transits
#
#         # ============================================
#         # 4. INITIALIZE TAROT SERVICE
#         # ============================================
#         tarot_service = TarotNatalService(natal_chart)
#
#         # Get dominant planetary energy
#         dominant_planet = tarot_service.get_dominant_planetary_energy()
#
#         # ============================================
#         # 5. SELECT CARD (transit-based if available)
#         # ============================================
#         if transits:
#             selected_card = tarot_service.select_card_by_transits(transits, COSMIC_TAROT_DECK)
#         else:
#             # Fallback to element-based selection
#             dominant_elem = natal_chart.get('dominant_element', 'Earth')
#             elem_cards = [c for c in COSMIC_TAROT_DECK if c.get('element') == dominant_elem]
#             selected_card = random.choice(elem_cards) if elem_cards else random.choice(COSMIC_TAROT_DECK)
#
#         # ============================================
#         # 6. PERSONALIZE INTERPRETATION
#         # ============================================
#         base_interpretation = selected_card['base_interpretation']
#         personalized_interpretation = tarot_service.personalize_interpretation(
#             base_interpretation,
#             dominant_planet
#         )
#
#         # ============================================
#         # 7. GENERATE NATAL INSIGHT
#         # ============================================
#         natal_insight = tarot_service.generate_natal_insight(selected_card)
#
#         # ============================================
#         # 8. GENERATE ASTROLOGICAL CONTEXT
#         # ============================================
#         astro_context = tarot_service.generate_astro_context(selected_card, transits)
#
#         # ============================================
#         # 9. SAVE TO DATABASE
#         # ============================================
#         card_draw = TarotCardDraw.objects.create(
#             user=request.user,
#             card_number=selected_card['card_number'],
#             card_name=selected_card['title'],
#             emoji=selected_card['emoji'],
#             keywords=selected_card['keywords'],
#             interpretation=personalized_interpretation,
#             astro_context=astro_context,
#             natal_insight=natal_insight,
#             drawn_at=timezone.now()
#         )
#
#         print(f"✨ {request.user.username} drew: {selected_card['title']}")
#
#         # ============================================
#         # 10. RETURN CARD DATA
#         # ============================================
#         return JsonResponse({
#             'card_number': selected_card['card_number'],
#             'title': selected_card['title'],
#             'emoji': selected_card['emoji'],
#             'keywords': selected_card['keywords'],
#             'interpretation': personalized_interpretation,
#             'astro_context': astro_context,
#             'natal_insight': natal_insight,
#             'can_draw_again': False
#         })
#
#     except AttributeError as e:
#         return JsonResponse({
#             'error': 'No birth profile found. Please create your birth profile first.'
#         }, status=404)
#
#     except Exception as e:
#         import traceback
#         print(f"❌ Tarot draw error: {e}")
#         print(traceback.format_exc())
#         return JsonResponse({
#             'error': f'Failed to draw card: {str(e)}'
#         }, status=500)
#
# from datetime import timedelta
# def calculate_current_streak(draw_dates):
#     if not draw_dates:
#         return 0
#
#     today = now().date()
#     streak = 0
#     current_day = today
#
#     for d in draw_dates:
#         if d == current_day:
#             streak += 1
#             current_day -= timedelta(days=1)
#         else:
#             # streak breaks if a day is missed
#             break
#     return streak
#
# @login_required
# def tarot_card_history(request):
#     """
#     Show user's past tarot draws with natal chart connections.
#     Returns HTML partial for modal.
#     """
#     from django.utils.timezone import now
#
#     all_draws = TarotCardDraw.objects.filter(
#         user=request.user
#     ).order_by('-drawn_at')
#
#     draw_dates = sorted({d.drawn_at.date() for d in all_draws}, reverse=True)
#     current_streak = calculate_current_streak(draw_dates)
#
#     draws = TarotCardDraw.objects.filter(
#         user=request.user
#     ).order_by('-drawn_at')[:30]  # Last 30 draws
#
#     return render(request, 'deep_dive/mystical/tarot_and_stats/tarot/_tarot_history.html', {
#         'draws': draws,
#         'total_draws': draws.count(),
#         'current_streak': current_streak,
#     })
#
#
# @login_required
# def draw_tarot_spread(request):
#     """
#     Two modes:
#     1. GET: Show initial spread interface with face-down cards
#     2. POST: Generate and return the actual spread
#     """
#
#     if request.method == 'GET':
#         return render(request, 'deep_dive/mystical/tarot_and_stats/tarot/_tarot_spread_initial.html')
#
#     # POST: Generate the spread
#     try:
#         birth_profile = request.user.birth_profile
#         natal_chart = birth_profile.cached_chart_data
#
#         if not natal_chart:
#             return JsonResponse({'error': 'No natal chart found'}, status=404)
#
#         user_intention = request.POST.get('intention', '').strip()
#
#         # Get current transits
#         try:
#             astro_service = AstronomicalService()
#             current_positions = astro_service.get_daily_planetary_summary()
#             transit_calc = TransitCalculator(natal_chart)
#             transits = transit_calc.calculate_transits(
#                 current_positions['planetary_positions']
#             )
#         except Exception as e:
#             print(f"Transit error: {e}")
#             transits = []
#
#         # Generate spread with intention
#         spread_service = ThreeCardSpreadService(natal_chart, transits, user_intention)
#         past_card, present_card, future_card = spread_service.generate_spread(COSMIC_TAROT_DECK)
#
#         # Personalize interpretations
#         tarot_service = TarotNatalService(natal_chart)
#         dominant_planet = tarot_service.get_dominant_planetary_energy()
#
#         spread_data = {
#             'past': {
#                 'position': 'Past Influences',
#                 'position_desc': 'What brought you here',
#                 **past_card,
#                 'interpretation': tarot_service.personalize_interpretation(
#                     past_card['base_interpretation'],
#                     dominant_planet
#                 ),
#             },
#             'present': {
#                 'position': 'Present Energy',
#                 'position_desc': 'Where you are now',
#                 **present_card,
#                 'interpretation': tarot_service.personalize_interpretation(
#                     present_card['base_interpretation'],
#                     dominant_planet
#                 ),
#             },
#             'future': {
#                 'position': 'Future Potential',
#                 'position_desc': 'Where you\'re heading',
#                 **future_card,
#                 'interpretation': tarot_service.personalize_interpretation(
#                     future_card['base_interpretation'],
#                     dominant_planet
#                 ),
#             }
#         }
#
#         reading_summary = spread_service.generate_spread_narrative(
#             past_card, present_card, future_card
#         )
#
#         return render(request, 'deep_dive/mystical/tarot_and_stats/tarot/_tarot_spread_result.html', {
#             'spread': spread_data,
#             'reading_summary': reading_summary,
#             'user_intention': user_intention
#         })
#
#     except Exception as e:
#         import traceback
#         print(f"Spread error: {e}")
#         print(traceback.format_exc())
#         return JsonResponse({'error': str(e)}, status=500)


def generate_spread_summary(spread_data: dict, natal_chart: dict) -> str:
    """
    Generate a cohesive summary tying the 3 cards together.
    References natal chart themes.
    """

    dominant_elem = natal_chart.get('dominant_element', 'Earth')

    summary = f"This three-card journey reflects your {dominant_elem} nature. "
    summary += f"From {spread_data['past']['title']} through {spread_data['present']['title']} "
    summary += f"toward {spread_data['future']['title']}, you're being guided to integrate "
    summary += "these energies into a cohesive path forward."

    return summary


