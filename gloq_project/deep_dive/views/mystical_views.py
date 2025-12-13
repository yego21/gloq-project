import random

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now

from ..services.mystical.astronomical_svc import get_moon_phase, get_planetary_summary



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


# @login_required
# def get_personal_rhythm_data(request):
#     """
#     API endpoint that returns personal rhythm analysis data.
#     Used by HTMX to load rhythm section.
#
#     Returns JSON with insights and chart data.
#     """
#     try:
#         analyzer = UserPatternAnalyzer(request.user)
#         insights = analyzer.get_all_insights()
#         chart_data = analyzer.get_visualization_data()
#
#         return JsonResponse({
#             'success': True,
#             'insights': insights,
#             'chart_data': chart_data
#         })
#
#     except Exception as e:
#         import traceback
#         print(f"Personal rhythm error: {e}")
#         print(traceback.format_exc())
#
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)


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


def astro_chart_reading(request):
    """
    Returns chart preview section
    If user is logged in and has a birth profile, include chart data
    """
    from userprofile.models import BirthProfile
    natal_chart = None
    birth_profile = None
    has_birth_profile = False
    current_reading = None
    has_birth_time = False

    # Initialize empty readings
    readings = {
        'daily_overview': None,
        'transit_focus': None,
        'element_wisdom': None,
    }

    if request.user.is_authenticated:
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
            # 'rising_sign': natal_chart.get('ascendant', {}).get('sign', 'N/A'),
            'dominant_element': natal_chart.get('dominant_element', 'Spirit'),
            'planet_count': len(natal_chart.get('planets', [])),
            'aspect_count': len(natal_chart.get('aspects', [])),
        }

    return render(request, 'deep_dive/mystical/astrology/_astro_chart_reading.html', {
        'has_birth_profile': has_birth_profile,
        'has_chart': natal_chart is not None,
        'has_birth_time': has_birth_time,
        'natal_chart': json.dumps(natal_chart) if natal_chart else None,
        'daily_reading': readings['daily_overview'],
        'transit_reading': readings['transit_focus'],
        'element_reading': readings['element_wisdom'],
        'chart_info': chart_context,
        'birth_setup_url': reverse('userprofile:birth_profile_setup')
    })


# Add this to your deep_dive/views.py file

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
import json


@login_required
def unified_chart_modal(request):
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
            return render(request, 'deep_dive/mystical/astrology/chart_modals/unified_chart_modal.html', {
                'error': 'No natal chart data available. Please generate your chart first.',
                'has_chart': False,
                'birth_setup_url': reverse('userprofile:birth_profile_setup'),
                'no_chart': 'NO CHART'
            })



        # Extract summary data for display
        # sun_planet = next((p for p in natal_chart_data.get('planets', []) if p['name'] == 'Sun'), None)
        # moon_planet = next((p for p in natal_chart_data.get('planets', []) if p['name'] == 'Moon'), None)
        # rising_sign = natal_chart_data.get('ascendant', {}).get('sign', 'Unknown')

        # Prepare context
        context = {
            'birth_profile': birth_profile,
            'natal_chart': natal_chart_data,
            'has_chart': True,
            # 'sun_sign': sun_planet['sign'] if sun_planet else 'Unknown',
            # 'moon_sign': moon_planet['sign'] if moon_planet else 'Unknown',
            # 'rising_sign': rising_sign,
            'planet_count': len(natal_chart_data.get('planets', [])),
            'aspect_count': len(natal_chart_data.get('aspects', [])),
            'dominant_element': natal_chart_data.get('dominant_element', 'Spirit'),
        }

        return render(request, 'deep_dive/mystical/astrology/chart_modals/unified_chart_modal.html', context)

    except BirthProfile.DoesNotExist:
        return render(request, 'deep_dive/mystical/chart_modals/unified_chart_modal.html', {
            'error': 'No birth profile found. Please create your birth profile first.',
            'has_chart': False,
            'birth_setup_url': reverse('userprofile:birth_profile_setup')
        })
    except Exception as e:
        return render(request, 'deep_dive/mystical/chart_modals/unified_chart_modal.html', {
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
            'planet': planet,
            'aspects': planet_aspects,
            'planet_meaning': planet_meanings.get(planet_name, 'Celestial body'),
            'element_description': element_descriptions.get(planet.get('element'), ''),
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
            if (a['planet1'] == planet1 and a['planet2'] == planet2 and a['aspect_type'] == aspect_type)
        ), None)

        if not aspect:
            return JsonResponse({'error': 'Aspect not found'}, status=404)

        # Get full planet data
        planet1_data = next((p for p in natal_chart['planets'] if p['name'] == planet1), None)
        planet2_data = next((p for p in natal_chart['planets'] if p['name'] == planet2), None)

        # Aspect interpretations
        aspect_meanings = {
            'Conjunction': {
                'symbol': '☌',
                'description': 'A powerful blending of planetary energies. These planets work together as a unified force.',
                'keywords': 'Unity, Fusion, Intensity, Synthesis',
                'influence': 'Strong and direct impact on personality and life themes.',
                'nature': 'Neutral to Powerful',
                'color': 'yellow',
            },
            'Opposition': {
                'symbol': '☍',
                'description': 'A dynamic tension between opposing forces. Requires balance and integration.',
                'keywords': 'Polarity, Balance, Awareness, Projection',
                'influence': 'Creates awareness through contrast and relationship dynamics.',
                'nature': 'Challenging',
                'color': 'red',
            },
            'Trine': {
                'symbol': '△',
                'description': 'A harmonious flow of energy. Natural talents and ease in expression.',
                'keywords': 'Harmony, Flow, Talent, Ease',
                'influence': 'Supportive aspect that enhances natural abilities.',
                'nature': 'Harmonious',
                'color': 'green',
            },
            'Square': {
                'symbol': '□',
                'description': 'A dynamic challenge that motivates growth and action.',
                'keywords': 'Challenge, Growth, Motivation, Friction',
                'influence': 'Creates productive tension that drives development.',
                'nature': 'Challenging',
                'color': 'orange',
            },
            'Sextile': {
                'symbol': '⚹',
                'description': 'Opportunities for growth through conscious effort.',
                'keywords': 'Opportunity, Cooperation, Skill, Support',
                'influence': 'Supportive aspect that requires some initiative to activate.',
                'nature': 'Harmonious',
                'color': 'blue',
            }
        }

        context = {
            'aspect': aspect,
            'planet1': planet1_data,
            'planet2': planet2_data,
            'meaning': aspect_meanings.get(aspect_type, {}),
        }

        return render(request, 'deep_dive/mystical/astrology/chart_modals/_aspect_detail.html', context)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
                # 'rising_sign': natal_chart.get('ascendant', {}).get('sign', 'N/A'),
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
        return render(request, 'deep_dive/mystical/astrology/_astro_chart_reading.html', context)

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
from .tarot_deck import COSMIC_TAROT_DECK
from ..services.mystical.tarot_natal_svc import TarotNatalService, ThreeCardSpreadService
from ..services.mystical.ai_chart_reading_svc import TransitCalculator
from ..services.mystical.astronomical_svc import AstronomicalService


@login_required
def draw_tarot_card(request):
    """
    Draw a daily tarot card based on natal chart + current transits.
    One card per day - cached daily like AI readings.

    Process:
    1. Check if already drawn today
    2. Get natal chart + current transits
    3. Use TarotNatalService to select & personalize card
    4. Save to database
    5. Return card data as JSON
    """

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        # ============================================
        # 1. GET USER'S NATAL CHART
        # ============================================
        birth_profile = request.user.birth_profile
        natal_chart = birth_profile.cached_chart_data

        if not natal_chart:
            return JsonResponse({
                'error': 'No natal chart data found. Please generate your chart first.'
            }, status=404)

        # ============================================
        # 2. CHECK IF ALREADY DRAWN TODAY
        # ============================================
        today_draw = TarotCardDraw.objects.filter(
            user=request.user,
            drawn_at__date=date.today()
        ).first()

        if today_draw:
            return JsonResponse({
                'error': 'You have already drawn your card for today. Return tomorrow for a new reading!'
            }, status=400)

        # ============================================
        # 3. GET CURRENT TRANSITS
        # ============================================
        try:
            # Use your existing services
            astro_service = AstronomicalService()
            current_positions = astro_service.get_daily_planetary_summary()

            transit_calc = TransitCalculator(natal_chart)
            transits = transit_calc.calculate_transits(
                current_positions['planetary_positions']
            )
        except Exception as e:
            print(f"Transit calculation failed: {e}")
            transits = []  # Continue without transits

        # ============================================
        # 4. INITIALIZE TAROT SERVICE
        # ============================================
        tarot_service = TarotNatalService(natal_chart)

        # Get dominant planetary energy
        dominant_planet = tarot_service.get_dominant_planetary_energy()

        # ============================================
        # 5. SELECT CARD (transit-based if available)
        # ============================================
        if transits:
            selected_card = tarot_service.select_card_by_transits(transits, COSMIC_TAROT_DECK)
        else:
            # Fallback to element-based selection
            dominant_elem = natal_chart.get('dominant_element', 'Earth')
            elem_cards = [c for c in COSMIC_TAROT_DECK if c.get('element') == dominant_elem]
            selected_card = random.choice(elem_cards) if elem_cards else random.choice(COSMIC_TAROT_DECK)

        # ============================================
        # 6. PERSONALIZE INTERPRETATION
        # ============================================
        base_interpretation = selected_card['base_interpretation']
        personalized_interpretation = tarot_service.personalize_interpretation(
            base_interpretation,
            dominant_planet
        )

        # ============================================
        # 7. GENERATE NATAL INSIGHT
        # ============================================
        natal_insight = tarot_service.generate_natal_insight(selected_card)

        # ============================================
        # 8. GENERATE ASTROLOGICAL CONTEXT
        # ============================================
        astro_context = tarot_service.generate_astro_context(selected_card, transits)

        # ============================================
        # 9. SAVE TO DATABASE
        # ============================================
        card_draw = TarotCardDraw.objects.create(
            user=request.user,
            card_number=selected_card['card_number'],
            card_name=selected_card['title'],
            emoji=selected_card['emoji'],
            keywords=selected_card['keywords'],
            interpretation=personalized_interpretation,
            astro_context=astro_context,
            natal_insight=natal_insight,
            drawn_at=timezone.now()
        )

        print(f"✨ {request.user.username} drew: {selected_card['title']}")

        # ============================================
        # 10. RETURN CARD DATA
        # ============================================
        return JsonResponse({
            'card_number': selected_card['card_number'],
            'title': selected_card['title'],
            'emoji': selected_card['emoji'],
            'keywords': selected_card['keywords'],
            'interpretation': personalized_interpretation,
            'astro_context': astro_context,
            'natal_insight': natal_insight,
            'can_draw_again': False
        })

    except AttributeError as e:
        return JsonResponse({
            'error': 'No birth profile found. Please create your birth profile first.'
        }, status=404)

    except Exception as e:
        import traceback
        print(f"❌ Tarot draw error: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': f'Failed to draw card: {str(e)}'
        }, status=500)

from datetime import timedelta
def calculate_current_streak(draw_dates):
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
            # streak breaks if a day is missed
            break
    return streak

@login_required
def tarot_card_history(request):
    """
    Show user's past tarot draws with natal chart connections.
    Returns HTML partial for modal.
    """
    from django.utils.timezone import now

    all_draws = TarotCardDraw.objects.filter(
        user=request.user
    ).order_by('-drawn_at')

    draw_dates = sorted({d.drawn_at.date() for d in all_draws}, reverse=True)
    current_streak = calculate_current_streak(draw_dates)

    draws = TarotCardDraw.objects.filter(
        user=request.user
    ).order_by('-drawn_at')[:30]  # Last 30 draws

    return render(request, 'deep_dive/mystical/tarot_and_stats/tarot/_tarot_history.html', {
        'draws': draws,
        'total_draws': draws.count(),
        'current_streak': current_streak,
    })


@login_required
def draw_tarot_spread(request):
    """
    Two modes:
    1. GET: Show initial spread interface with face-down cards
    2. POST: Generate and return the actual spread
    """

    if request.method == 'GET':
        return render(request, 'deep_dive/mystical/tarot_and_stats/tarot/_tarot_spread_initial.html')

    # POST: Generate the spread
    try:
        birth_profile = request.user.birth_profile
        natal_chart = birth_profile.cached_chart_data

        if not natal_chart:
            return JsonResponse({'error': 'No natal chart found'}, status=404)

        user_intention = request.POST.get('intention', '').strip()

        # Get current transits
        try:
            astro_service = AstronomicalService()
            current_positions = astro_service.get_daily_planetary_summary()
            transit_calc = TransitCalculator(natal_chart)
            transits = transit_calc.calculate_transits(
                current_positions['planetary_positions']
            )
        except Exception as e:
            print(f"Transit error: {e}")
            transits = []

        # Generate spread with intention
        spread_service = ThreeCardSpreadService(natal_chart, transits, user_intention)
        past_card, present_card, future_card = spread_service.generate_spread(COSMIC_TAROT_DECK)

        # Personalize interpretations
        tarot_service = TarotNatalService(natal_chart)
        dominant_planet = tarot_service.get_dominant_planetary_energy()

        spread_data = {
            'past': {
                'position': 'Past Influences',
                'position_desc': 'What brought you here',
                **past_card,
                'interpretation': tarot_service.personalize_interpretation(
                    past_card['base_interpretation'],
                    dominant_planet
                ),
            },
            'present': {
                'position': 'Present Energy',
                'position_desc': 'Where you are now',
                **present_card,
                'interpretation': tarot_service.personalize_interpretation(
                    present_card['base_interpretation'],
                    dominant_planet
                ),
            },
            'future': {
                'position': 'Future Potential',
                'position_desc': 'Where you\'re heading',
                **future_card,
                'interpretation': tarot_service.personalize_interpretation(
                    future_card['base_interpretation'],
                    dominant_planet
                ),
            }
        }

        reading_summary = spread_service.generate_spread_narrative(
            past_card, present_card, future_card
        )

        return render(request, 'deep_dive/mystical/tarot_and_stats/tarot/_tarot_spread_result.html', {
            'spread': spread_data,
            'reading_summary': reading_summary,
            'user_intention': user_intention
        })

    except Exception as e:
        import traceback
        print(f"Spread error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


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


