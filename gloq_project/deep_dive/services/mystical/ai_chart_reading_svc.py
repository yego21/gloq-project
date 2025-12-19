# deep_dive/services/ai_chart_reading_svc.py
"""
AI-powered astrological reading service.
Enhanced with psychologically nuanced transit interpretations and type-specific data returns.
"""

from datetime import datetime, date
from typing import Dict, List, Optional
import json
from collections import Counter
from django.core.cache import cache
from django.conf import settings
from groq import Groq

from deep_dive.services.mystical.astronomical_svc import AstronomicalService


class TransitCalculator:
    """
    Calculates transit-to-natal aspects.

    Transit = Current planetary position
    Natal = Birth chart planetary position
    Aspect = Angular relationship between them
    """

    def __init__(self, natal_chart: Dict):
        """
        Args:
            natal_chart: User's natal chart data from NatalChartService
        """
        self.natal_chart = natal_chart
        self.natal_planets = {p['name']: p for p in natal_chart['planets']}

    def calculate_transits(self, current_positions: List[Dict]) -> List[Dict]:
        """
        Compare current planetary positions to natal positions.

        Args:
            current_positions: List of current planet positions from AstronomicalService

        Returns:
            List of transit aspects with interpretive weight
        """
        transits = []

        # Major aspect angles with orbs
        aspect_definitions = [
            (0, 'Conjunction', 6, 'intense'),  # Same position - powerful
            (60, 'Sextile', 4, 'harmonious'),  # Opportunity
            (90, 'Square', 6, 'challenging'),  # Tension/growth
            (120, 'Trine', 6, 'flowing'),  # Easy energy
            (180, 'Opposition', 6, 'dynamic'),  # Awareness/balance
        ]

        # Compare each current planet to natal planets
        for current_planet in current_positions:
            current_name = current_planet['name']
            current_lon = current_planet['longitude']

            # Only check if we have this planet in natal chart
            if current_name not in self.natal_planets:
                continue

            for natal_name, natal_planet in self.natal_planets.items():
                # Don't compare planet to itself
                if current_name == natal_name:
                    continue

                natal_lon = natal_planet['longitude']

                # Calculate angular separation
                angle_diff = abs(current_lon - natal_lon)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff

                # Check each aspect type
                for aspect_angle, aspect_name, orb, quality in aspect_definitions:
                    deviation = abs(angle_diff - aspect_angle)

                    if deviation <= orb:
                        # Calculate strength (closer = stronger)
                        strength = 1 - (deviation / orb)

                        transits.append({
                            'transit_planet': current_name,
                            'natal_planet': natal_name,
                            'aspect_type': aspect_name,
                            'quality': quality,
                            'angle': round(angle_diff, 2),
                            'orb': round(deviation, 2),
                            'strength': round(strength, 2),
                            'transit_sign': current_planet['sign'],
                            'natal_sign': natal_planet['sign'],
                        })
                        break

        # Sort by strength (most significant first)
        transits.sort(key=lambda x: x['strength'], reverse=True)

        return transits


class CosmicDataAnalyzer:
    """Helper class to analyze astronomical data and extract meaningful patterns."""

    @staticmethod
    def get_element_distribution(planetary_positions: List[Dict]) -> Dict[str, int]:
        """Count planets in each element."""
        elements = Counter([p['element'] for p in planetary_positions if 'element' in p])
        return {
            'Fire': elements.get('Fire', 0),
            'Earth': elements.get('Earth', 0),
            'Air': elements.get('Air', 0),
            'Water': elements.get('Water', 0)
        }

    @staticmethod
    def get_modality_distribution(planetary_positions: List[Dict]) -> Dict[str, int]:
        """Count planets in each modality (Cardinal, Fixed, Mutable)."""
        modality_map = {
            # Cardinal signs
            'Aries': 'Cardinal', 'Cancer': 'Cardinal', 'Libra': 'Cardinal', 'Capricorn': 'Cardinal',
            # Fixed signs
            'Taurus': 'Fixed', 'Leo': 'Fixed', 'Scorpio': 'Fixed', 'Aquarius': 'Fixed',
            # Mutable signs
            'Gemini': 'Mutable', 'Virgo': 'Mutable', 'Sagittarius': 'Mutable', 'Pisces': 'Mutable'
        }

        modalities = Counter([
            modality_map.get(p['sign'], 'Unknown')
            for p in planetary_positions
            if 'sign' in p
        ])

        return {
            'Cardinal': modalities.get('Cardinal', 0),
            'Fixed': modalities.get('Fixed', 0),
            'Mutable': modalities.get('Mutable', 0)
        }

    @staticmethod
    def get_sign_distribution(planetary_positions: List[Dict]) -> Dict[str, List[str]]:
        """Group planets by zodiac sign."""
        sign_groups = {}
        for planet in planetary_positions:
            sign = planet.get('sign')
            if sign:
                if sign not in sign_groups:
                    sign_groups[sign] = []
                sign_groups[sign].append(planet['name'])
        return sign_groups

    @staticmethod
    def find_conjunctions(planetary_positions: List[Dict], orb: float = 8.0) -> List[Dict]:
        """Find close conjunctions between current planets in the sky."""
        conjunctions = []

        for i, planet1 in enumerate(planetary_positions):
            for planet2 in planetary_positions[i + 1:]:
                lon1 = planet1['longitude']
                lon2 = planet2['longitude']

                angle_diff = abs(lon1 - lon2)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff

                if angle_diff <= orb:
                    conjunctions.append({
                        'planet1': planet1['name'],
                        'planet2': planet2['name'],
                        'orb': round(angle_diff, 2),
                        'sign': planet1['sign']
                    })

        return conjunctions

    @staticmethod
    def calculate_element_balance_score(element_dist: Dict[str, int]) -> Dict[str, any]:
        """Calculate elemental balance metrics."""
        total = sum(element_dist.values())
        if total == 0:
            return {'balance': 'neutral', 'dominant': None, 'lacking': None}

        percentages = {elem: (count / total) * 100 for elem, count in element_dist.items()}

        dominant = max(percentages, key=percentages.get)
        lacking = min(percentages, key=percentages.get) if percentages[
                                                               min(percentages, key=percentages.get)] < 15 else None

        # Calculate balance (closer to 25% each = more balanced)
        variance = sum([(pct - 25) ** 2 for pct in percentages.values()]) / 4
        balance = 'balanced' if variance < 100 else 'imbalanced'

        return {
            'balance': balance,
            'dominant': dominant if percentages[dominant] > 35 else None,
            'lacking': lacking,
            'percentages': {k: round(v, 1) for k, v in percentages.items()}
        }

    @staticmethod
    def compare_elemental_weather(natal_elements: Dict[str, int], current_elements: Dict[str, int]) -> Dict[str, str]:
        """Compare natal element distribution to current sky."""
        comparisons = {}

        for element in ['Fire', 'Earth', 'Air', 'Water']:
            natal_count = natal_elements.get(element, 0)
            current_count = current_elements.get(element, 0)

            if current_count > natal_count:
                comparisons[element] = 'amplified'
            elif current_count < natal_count:
                comparisons[element] = 'diminished'
            else:
                comparisons[element] = 'stable'

        return comparisons


class AIReadingService:
    """
    Generates AI-powered astrological readings using Groq.
    Enhanced with psychologically nuanced transit interpretations and type-specific data.
    """

    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.astro_service = AstronomicalService()
        self.cosmic_analyzer = CosmicDataAnalyzer()

    def generate_daily_reading(
            self,
            natal_chart: Dict,
            reading_type: str = 'daily_overview',
            user=None
    ) -> Dict:
        """
        Generate an AI reading based on natal chart and current transits.
        Returns type-specific data optimized for each reading context.

        Args:
            natal_chart: User's natal chart data
            reading_type: Type of reading (daily_overview, transit_focus, element_wisdom)
            user: User object to fetch journal entries

        Returns:
            Dict with reading content and TYPE-SPECIFIC metadata
        """
        # Get current planetary positions
        current_positions = self.astro_service.get_daily_planetary_summary()
        current_moon = self.astro_service.get_current_moon_phase()

        # Calculate transits
        transit_calc = TransitCalculator(natal_chart)
        transits = transit_calc.calculate_transits(
            current_positions['planetary_positions']
        )

        # Get today's journal entries if user is provided
        journal_context = self._get_todays_journal_context(user) if user else None

        # Build prompt based on reading type
        if reading_type == 'daily_overview':
            prompt = self._build_daily_overview_prompt(
                natal_chart, transits, current_positions, current_moon, journal_context
            )
            max_tokens = 600
        elif reading_type == 'transit_focus':
            prompt = self._build_transit_focus_prompt(
                natal_chart, transits, journal_context
            )
            max_tokens = 700
        elif reading_type == 'element_wisdom':
            prompt = self._build_element_wisdom_prompt(
                natal_chart, current_positions, journal_context
            )
            max_tokens = 500
        else:
            raise ValueError(f"Unknown reading type: {reading_type}")

        # Call Groq API
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an experienced, warm, and emotionally intelligent astrologer speaking directly to a returning client. Your voice is wise but never preachy, mystical but grounded, specific and nuanced rather than generic. You acknowledge both light and shadow. You weave journal reflections naturally into your interpretations without explicitly saying 'your journal says' — instead, you reflect their lived experience back to them with empathy and insight. Avoid horoscope clichés, forced positivity, and vague predictions. Be human, real, and resonant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=max_tokens,
            )

            reading_text = response.choices[0].message.content.strip()

            # Build TYPE-SPECIFIC response data
            if reading_type == 'daily_overview':
                return self._build_daily_overview_response(
                    reading_text, transits, current_positions, current_moon, journal_context
                )
            elif reading_type == 'transit_focus':
                return self._build_transit_focus_response(
                    reading_text, transits, current_moon, journal_context
                )
            elif reading_type == 'element_wisdom':
                return self._build_element_wisdom_response(
                    reading_text, natal_chart, current_positions, current_moon, journal_context
                )

        except Exception as e:
            print(f"AI reading generation error: {e}")
            return self._fallback_reading(reading_type)

    def _build_daily_overview_response(
            self,
            reading_text: str,
            transits: List[Dict],
            current_positions: Dict,
            current_moon: Dict,
            journal_context: Optional[str]
    ) -> Dict:
        """Build response data optimized for Daily Overview - cosmic context, not detailed transits."""

        planetary_positions = current_positions['planetary_positions']

        # Get element and modality distributions
        element_dist = self.cosmic_analyzer.get_element_distribution(planetary_positions)
        modality_dist = self.cosmic_analyzer.get_modality_distribution(planetary_positions)
        sign_groups = self.cosmic_analyzer.get_sign_distribution(planetary_positions)
        conjunctions = self.cosmic_analyzer.find_conjunctions(planetary_positions)

        # Get just the TOP transit as brief context (not full interpretation)
        top_transit_context = None
        if transits:
            top = transits[0]
            top_transit_context = {
                'summary': f"{top['transit_planet']} {top['aspect_type']} {top['natal_planet']}",
                'quality': top['quality'],
                'orb': float(top['orb'])
            }

        return {
            'reading_type': 'daily_overview',
            'reading_text': reading_text,
            'generated_at': datetime.now().isoformat(),

            # Brief transit context (just 1)
            'primary_transit': top_transit_context,
            'total_transits': len(transits),

            # Cosmic weather data
            'moon_phase': {
                'phase': current_moon['phase'],
                'emoji': current_moon['emoji'],
                'illumination': current_moon['illumination'],
                'description': current_moon['description']
            },
            'element_distribution': element_dist,
            'modality_distribution': modality_dist,
            'dominant_element': current_positions.get('dominant_element'),
            'cosmic_weather': current_positions.get('cosmic_weather'),

            # Planetary patterns
            'sign_concentrations': [
                {'sign': sign, 'planets': planets, 'count': len(planets)}
                for sign, planets in sign_groups.items()
                if len(planets) > 1  # Only show signs with 2+ planets
            ],
            'sky_conjunctions': conjunctions[:3],  # Top 3 conjunctions in the sky

            'journal_included': journal_context is not None,
        }

    def _build_transit_focus_response(
            self,
            reading_text: str,
            transits: List[Dict],
            current_moon: Dict,
            journal_context: Optional[str]
    ) -> Dict:
        """Build response data optimized for Transit Focus - detailed transit analysis."""

        # Generate FULL transit summaries for top 3 transits
        transit_summaries = []
        for transit in transits[:3]:
            interpretation = self._get_transit_interpretation_context(transit)
            summary = {
                'transit_planet': transit['transit_planet'],
                'transit_sign': transit['transit_sign'],
                'aspect_type': transit['aspect_type'],
                'natal_planet': transit['natal_planet'],
                'natal_sign': transit['natal_sign'],
                'orb': float(transit['orb']),
                'quality': transit['quality'],
                'strength': float(transit['strength']),
                'summary': interpretation.get('summary', ''),
                'meaning': interpretation['meaning'],
                'life_areas': interpretation['life_areas'],
                'themes': interpretation['themes'],
                'shadow_aspect': interpretation.get('shadow_aspect', ''),
                'grounded_recommendation': interpretation.get('grounded_recommendation', ''),
                'tone': interpretation['tone'],
                'disclaimer': interpretation.get('disclaimer', '')
            }
            transit_summaries.append(summary)

        return {
            'reading_type': 'transit_focus',
            'reading_text': reading_text,
            'generated_at': datetime.now().isoformat(),

            # Full transit details
            'transits_analyzed': len(transits),
            'top_transits': [
                {
                    **t,
                    'angle': float(t['angle']),
                    'orb': float(t['orb']),
                    'strength': float(t['strength'])
                }
                for t in transits[:3]
            ],
            'transit_summaries': transit_summaries,  # FULL interpretations

            # Minimal cosmic context
            'moon_phase': current_moon['phase'],

            'journal_included': journal_context is not None,
        }

    def _build_element_wisdom_response(
            self,
            reading_text: str,
            natal_chart: Dict,
            current_positions: Dict,
            current_moon: Dict,
            journal_context: Optional[str]
    ) -> Dict:
        """Build response data optimized for Element Wisdom - NO transits, pure elemental analysis."""

        planetary_positions = current_positions['planetary_positions']

        # Current sky element distribution
        current_element_dist = self.cosmic_analyzer.get_element_distribution(planetary_positions)
        current_modality_dist = self.cosmic_analyzer.get_modality_distribution(planetary_positions)

        # Natal element distribution (from natal chart planets)
        natal_element_dist = self.cosmic_analyzer.get_element_distribution(natal_chart['planets'])
        natal_modality_dist = self.cosmic_analyzer.get_modality_distribution(natal_chart['planets'])

        # Element balance analysis
        current_balance = self.cosmic_analyzer.calculate_element_balance_score(current_element_dist)
        natal_balance = self.cosmic_analyzer.calculate_element_balance_score(natal_element_dist)

        # Compare natal vs current
        element_comparison = self.cosmic_analyzer.compare_elemental_weather(
            natal_element_dist,
            current_element_dist
        )

        # Planetary breakdown by element
        planets_by_element = {}
        for planet in planetary_positions:
            element = planet.get('element')
            if element:
                if element not in planets_by_element:
                    planets_by_element[element] = []
                planets_by_element[element].append({
                    'name': planet['name'],
                    'sign': planet['sign'],
                    'symbol': planet.get('symbol', '')
                })

        return {
            'reading_type': 'element_wisdom',
            'reading_text': reading_text,
            'generated_at': datetime.now().isoformat(),

            # NO TRANSITS - pure elemental focus

            # Current sky elements
            'current_elements': {
                'distribution': current_element_dist,
                'modality': current_modality_dist,
                'dominant': current_positions.get('dominant_element'),
                'balance': current_balance,
                'planets_by_element': planets_by_element
            },

            # Natal elements
            'natal_elements': {
                'distribution': natal_element_dist,
                'modality': natal_modality_dist,
                'dominant': natal_chart.get('dominant_element'),
                'balance': natal_balance
            },

            # Comparison
            'elemental_weather_comparison': element_comparison,

            # Moon context (elements are lunar-connected)
            'moon_phase': {
                'phase': current_moon['phase'],
                'emoji': current_moon['emoji']
            },

            'journal_included': journal_context is not None,
        }

    def _get_todays_journal_context(self, user) -> Optional[str]:
        """
        Fetch today's journal entries for the user.

        Args:
            user: User object

        Returns:
            Formatted string of today's journal entries or None
        """
        if not user:
            return None

        try:
            from django.utils import timezone
            from datetime import datetime

            # Import your JournalEntry model
            from journal.models import JournalEntry

            # Get today's start and end
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timezone.timedelta(days=1)

            # Fetch today's entries
            entries = JournalEntry.objects.filter(
                user=user,
                created_at__gte=today_start,
                created_at__lt=today_end
            ).order_by('created_at')

            if not entries.exists():
                return None

            # Format entries
            journal_text = ""
            for entry in entries:
                label = entry.label or "Entry"
                tags = ", ".join([tag.name for tag in entry.tags.all()]) if entry.tags.exists() else "No tags"

                # Truncate long entries
                content = entry.content[:300] + "..." if len(entry.content) > 300 else entry.content

                journal_text += f"[{label}] ({tags}): {content}\n\n"

            return journal_text.strip()

        except Exception as e:
            print(f"Error fetching journal context: {e}")
            return None

    def _get_transit_interpretation_context(self, transit: Dict) -> Dict:
        """
        Generate contextual interpretation guidance for a specific transit.
        Enhanced with psychological depth, practical guidance, and preset summaries.
        """
        transit_planet = transit['transit_planet']
        natal_planet = transit['natal_planet']
        aspect = transit['aspect_type']

        # Get specific transit key
        key = f"{transit_planet}_{aspect}_{natal_planet}"

        # COMPREHENSIVE TRANSIT DICTIONARY - All 40+ transits with summaries
        specific_transits = {
            # MARS TRANSITS
            'Mars_Opposition_Saturn': {
                'summary': 'Drive meets resistance—patience under pressure',
                'meaning': 'The tension between your drive and life\'s limitations',
                'life_areas': 'Career ambitions, authority dynamics, long-term structures',
                'themes': 'A reality check moment where your willpower meets external constraints.',
                'shadow_aspect': 'Watch for resentment toward authority or turning frustration inward.',
                'grounded_recommendation': 'Identify which walls are meant to be climbed and which redirect your path.',
                'tone': 'challenging',
                'disclaimer': 'This transit highlights existing tensions rather than creating new ones.'
            },
            'Mars_Square_Saturn': {
                'summary': 'Action meets obstacles—strategic recalibration',
                'meaning': 'Friction between immediate action and necessary restraint',
                'life_areas': 'Work ethic, physical energy management, ambitious projects',
                'themes': 'Your drive meets tangible obstacles asking for recalibration rather than brute force.',
                'shadow_aspect': 'Avoid giving up entirely or pushing so hard you break something important.',
                'grounded_recommendation': 'Focus on preparation rather than propulsion.',
                'tone': 'challenging',
                'disclaimer': 'These obstacles aren\'t personal failures but timing mechanisms.'
            },
            'Mars_Conjunction_Venus': {
                'summary': 'Passion and pleasure unite—magnetic attraction',
                'meaning': 'Passion and desire dance together',
                'life_areas': 'Romantic connections, creative expression, financial initiatives',
                'themes': 'Your actions naturally align with what brings pleasure and connection.',
                'shadow_aspect': 'Be mindful of impulsive relationship decisions or spending.',
                'grounded_recommendation': 'Channel this energy into projects blending beauty and action.',
                'tone': 'harmonious',
                'disclaimer': 'While this supports new beginnings, lasting connections require building trust over time.'
            },
            'Mars_Trine_Jupiter': {'summary': 'Confident action meets opportunity',
                                   'meaning': 'Confident action meets expansive opportunity',
                                   'life_areas': 'Risk-taking, entrepreneurial ventures',
                                   'themes': 'Your actions are supported by luck and timing.',
                                   'shadow_aspect': 'Overconfidence can lead to overlooking details.',
                                   'grounded_recommendation': 'Trust intuition but maintain awareness.',
                                   'tone': 'harmonious',
                                   'disclaimer': 'Even favorable transits don\'t eliminate all obstacles.'},
            'Mars_Trine_Pluto': {'summary': 'Focused power surges',
                                 'meaning': 'Focused action meets transformative power',
                                 'life_areas': 'Strategic initiatives, intense activity',
                                 'themes': 'Your actions carry extra power and focus.',
                                 'shadow_aspect': 'Power struggles can emerge if not conscious.',
                                 'grounded_recommendation': 'Channel this into constructive transformation.',
                                 'tone': 'harmonious',
                                 'disclaimer': 'True power transforms without needing to dominate.'},
            'Mars_Opposition_Jupiter': {'summary': 'Bold action meets wisdom',
                                        'meaning': 'Expansive action meets wise restraint',
                                        'life_areas': 'Risk assessment, entrepreneurial decisions',
                                        'themes': 'Your drive for expansion meets the need for wise boundaries.',
                                        'shadow_aspect': 'Overconfidence leading to overextension.',
                                        'grounded_recommendation': 'Think big, start small.', 'tone': 'challenging',
                                        'disclaimer': 'Growth requires both expansion and discernment.'},

            # SUN TRANSITS
            'Sun_Trine_Moon': {'summary': 'Heart and mind harmonize',
                               'meaning': 'Inner harmony between identity and emotions',
                               'life_areas': 'Self-expression, emotional security',
                               'themes': 'Your conscious self and emotional nature align easily.',
                               'shadow_aspect': 'Possible complacency.',
                               'grounded_recommendation': 'Use this to heal old emotional patterns.',
                               'tone': 'harmonious',
                               'disclaimer': 'This supports emotional intelligence but doesn\'t exempt you from inner work.'},
            'Sun_Conjunction_Venus': {'summary': 'Charm and magnetism amplified',
                                      'meaning': 'Self-expression feels attractive and valued',
                                      'life_areas': 'Relationships, self-worth, social connections',
                                      'themes': 'Your personal charm and social appeal are heightened.',
                                      'shadow_aspect': 'Vanity or over-reliance on external validation.',
                                      'grounded_recommendation': 'Share your authentic self in social situations.',
                                      'tone': 'harmonious',
                                      'disclaimer': 'This enhances existing qualities—it doesn\'t fundamentally change who you are.'},
            'Sun_Square_Saturn': {'summary': 'Identity tested by reality',
                                  'meaning': 'Your identity meets reality\'s boundaries',
                                  'life_areas': 'Career progress, authority relationships',
                                  'themes': 'This often feels like a "prove yourself" moment.',
                                  'shadow_aspect': 'Beware of shrinking from challenges.',
                                  'grounded_recommendation': 'Focus on what you can control: preparation and response.',
                                  'tone': 'challenging', 'disclaimer': 'These tests build lasting structures.'},
            'Sun_Opposition_Pluto': {'summary': 'Power dynamics surface',
                                     'meaning': 'Ego confronts transformative power dynamics',
                                     'life_areas': 'Control issues, personal transformation',
                                     'themes': 'This intense transit brings power dynamics to the surface.',
                                     'shadow_aspect': 'Power struggles or manipulation can emerge.',
                                     'grounded_recommendation': 'Notice where you\'re giving power away or clinging too tightly.',
                                     'tone': 'challenging',
                                     'disclaimer': 'Your response determines whether this becomes destructive or transformative.'},
            'Sun_Conjunction_Mercury': {'summary': 'Identity and mind unite', 'meaning': 'Identity and mind align',
                                        'life_areas': 'Self-expression, communication',
                                        'themes': 'Your thoughts and identity work in harmony.',
                                        'shadow_aspect': 'Can become overly identified with opinions.',
                                        'grounded_recommendation': 'Express your truth while remaining open.',
                                        'tone': 'neutral',
                                        'disclaimer': 'Clarity of thought supports but doesn\'t replace wisdom of heart.'},

            # MERCURY TRANSITS
            'Mercury_Square_Neptune': {'summary': 'Mental fog descends', 'meaning': 'Clarity meets confusion',
                                       'life_areas': 'Communication, decision-making',
                                       'themes': 'Information may feel fuzzy or emotionally charged.',
                                       'shadow_aspect': 'Important details may be overlooked.',
                                       'grounded_recommendation': 'Double-check information.', 'tone': 'challenging',
                                       'disclaimer': 'Not every confusing moment signals deception.'},
            'Mercury_Trine_Jupiter': {'summary': 'Mind expands optimistically', 'meaning': 'Mind expands with optimism',
                                      'life_areas': 'Learning, communication',
                                      'themes': 'Your thinking becomes more expansive.',
                                      'shadow_aspect': 'Overconfidence in opinions.',
                                      'grounded_recommendation': 'Use this for learning something new.',
                                      'tone': 'harmonious',
                                      'disclaimer': 'Expansive thinking is valuable but needs grounding.'},
            'Mercury_Conjunction_Mars': {'summary': 'Sharp mind, sharper words',
                                         'meaning': 'Sharp words and quick decisions',
                                         'life_areas': 'Communication, debates', 'themes': 'Your mind works quickly.',
                                         'shadow_aspect': 'Tendency toward argumentativeness.',
                                         'grounded_recommendation': 'Channel this into productive debates.',
                                         'tone': 'neutral',
                                         'disclaimer': 'Direct communication is powerful but timing matters.'},
            'Mercury_Square_Uranus': {'summary': 'Mental electricity sparks',
                                      'meaning': 'Mental breakthroughs meet disruptive insights',
                                      'life_areas': 'Sudden ideas, unconventional thinking',
                                      'themes': 'Your thinking might feel electric or scattered.',
                                      'shadow_aspect': 'Mental restlessness.',
                                      'grounded_recommendation': 'Capture brilliant ideas but wait before acting.',
                                      'tone': 'challenging', 'disclaimer': 'Revolutionary ideas need time to mature.'},
            'Mercury_Trine_Neptune': {'summary': 'Intuition guides thought',
                                      'meaning': 'Intuitive thinking meets creative flow',
                                      'life_areas': 'Creative writing, spiritual insights',
                                      'themes': 'Your thinking connects easily with intuition.',
                                      'shadow_aspect': 'Facts might feel less important than feelings.',
                                      'grounded_recommendation': 'Trust intuition but verify details.',
                                      'tone': 'harmonious',
                                      'disclaimer': 'Intuition illuminates but practical steps bring dreams to earth.'},

            # VENUS TRANSITS
            'Venus_Opposition_Mars': {'summary': 'Desire meets harmony',
                                      'meaning': 'The delicate dance between what you desire and how you pursue it',
                                      'life_areas': 'Relationship dynamics, sexual chemistry',
                                      'themes': 'Often manifests as a pull between harmony and assertion.',
                                      'shadow_aspect': 'Watch for passive-aggression.',
                                      'grounded_recommendation': 'Practice stating desires clearly.',
                                      'tone': 'challenging',
                                      'disclaimer': 'This highlights where you need balance between assertion and receptivity.'},
            'Venus_Trine_Saturn': {'summary': 'Love meets commitment', 'meaning': 'Love meets commitment and stability',
                                   'life_areas': 'Long-term relationships, financial planning',
                                   'themes': 'Relationship energies feel more serious and grounded.',
                                   'shadow_aspect': 'Can feel overly serious.',
                                   'grounded_recommendation': 'Strengthen existing commitments.', 'tone': 'harmonious',
                                   'disclaimer': 'Stability is valuable but relationships need flexibility too.'},
            'Venus_Square_Pluto': {'summary': 'Love confronts intensity',
                                   'meaning': 'Love confronts transformative intensity',
                                   'life_areas': 'Relationship power dynamics',
                                   'themes': 'Intense feelings surface in relationships.',
                                   'shadow_aspect': 'Possessiveness or jealousy.',
                                   'grounded_recommendation': 'Notice what you\'re clinging to and why.',
                                   'tone': 'challenging', 'disclaimer': 'Intense feelings are signals, not commands.'},
            'Venus_Conjunction_Jupiter': {'summary': 'Love expands abundantly',
                                          'meaning': 'Expansive love meets abundant connection',
                                          'life_areas': 'Social opportunities, romantic possibilities',
                                          'themes': 'Your social and romantic appeal expands.',
                                          'shadow_aspect': 'Over-optimism or financial overextension.',
                                          'grounded_recommendation': 'Enjoy abundance but maintain boundaries.',
                                          'tone': 'harmonious',
                                          'disclaimer': 'Abundance flows best when shared responsibly.'},
            'Venus_Square_Uranus': {'summary': 'Relationship surprises shake up',
                                    'meaning': 'Relationship surprises meet freedom needs',
                                    'life_areas': 'Unconventional attractions',
                                    'themes': 'Unexpected developments in relationships.',
                                    'shadow_aspect': 'Impulsive relationship decisions.',
                                    'grounded_recommendation': 'Embrace authenticity but avoid burning bridges.',
                                    'tone': 'challenging',
                                    'disclaimer': 'Freedom requires both independence and responsibility.'},

            # JUPITER, SATURN, URANUS, NEPTUNE, PLUTO TRANSITS
            'Jupiter_Trine_Sun': {'summary': 'Identity expands gracefully',
                                  'meaning': 'Your essence expands into new possibilities',
                                  'life_areas': 'Personal growth, career opportunities',
                                  'themes': 'Supportive energy helps recognize potential.',
                                  'shadow_aspect': 'Overextension.',
                                  'grounded_recommendation': 'Choose growth paths aligning with core identity.',
                                  'tone': 'harmonious', 'disclaimer': 'Even favorable transits require participation.'},
            'Jupiter_Conjunction_Venus': {'summary': 'Abundance flows freely', 'meaning': 'Abundance meets pleasure',
                                          'life_areas': 'Social expansion, financial opportunities',
                                          'themes': 'Social and romantic opportunities expand.',
                                          'shadow_aspect': 'Overindulgence.',
                                          'grounded_recommendation': 'Share abundance with others.',
                                          'tone': 'harmonious', 'disclaimer': 'Abundance flows best when shared.'},
            'Jupiter_Square_Saturn': {'summary': 'Growth meets limits', 'meaning': 'Growth confronts practical limits',
                                      'life_areas': 'Career ambitions',
                                      'themes': 'Expansive desires meet structural limitations.',
                                      'shadow_aspect': 'Can swing between reckless optimism and pessimism.',
                                      'grounded_recommendation': 'Find the middle path.', 'tone': 'challenging',
                                      'disclaimer': 'This reveals where growth needs structure.'},
            'Jupiter_Opposition_Moon': {'summary': 'Emotional expansion tested',
                                        'meaning': 'Expansive feelings meet emotional boundaries',
                                        'life_areas': 'Emotional growth, family expansion',
                                        'themes': 'Your emotional world expands or confronts limits.',
                                        'shadow_aspect': 'Emotional overextension.',
                                        'grounded_recommendation': 'Expand while honoring need for safety.',
                                        'tone': 'challenging',
                                        'disclaimer': 'Emotional growth happens at edge of comfort.'},
            'Saturn_Square_Moon': {'summary': 'Emotional burden weighs heavy',
                                   'meaning': 'Responsibility weighs on emotional security',
                                   'life_areas': 'Family obligations, emotional burdens',
                                   'themes': 'Emotional needs might feel burdened.',
                                   'shadow_aspect': 'Emotional repression.',
                                   'grounded_recommendation': 'Create structured self-care.', 'tone': 'challenging',
                                   'disclaimer': 'Feeling burdened is information, not failure.'},
            'Saturn_Trine_Venus': {'summary': 'Commitment strengthens love',
                                   'meaning': 'Structure supports lasting love',
                                   'life_areas': 'Committed relationships',
                                   'themes': 'Relationships benefit from maturity.',
                                   'shadow_aspect': 'Can become overly practical.',
                                   'grounded_recommendation': 'Invest in long-term potential.', 'tone': 'harmonious',
                                   'disclaimer': 'Lasting beauty requires patience.'},
            'Saturn_Conjunction_Sun': {'summary': 'Identity matures deeply',
                                       'meaning': 'Your identity meets maturation point',
                                       'life_areas': 'Life direction, career definition',
                                       'themes': 'Major life chapter shift toward maturity.',
                                       'shadow_aspect': 'Resisting necessary maturation.',
                                       'grounded_recommendation': 'Identify what foundations need strengthening.',
                                       'tone': 'neutral',
                                       'disclaimer': 'This works over months; gifts reveal in hindsight.'},
            'Saturn_Trine_Mars': {'summary': 'Discipline meets momentum',
                                  'meaning': 'Disciplined action meets sustained results',
                                  'life_areas': 'Long-term projects',
                                  'themes': 'Actions align with sustainable structures.',
                                  'shadow_aspect': 'Can become overly rigid.',
                                  'grounded_recommendation': 'Build momentum through consistency.',
                                  'tone': 'harmonious',
                                  'disclaimer': 'Lasting results come from consistent application.'},
            'Saturn_Square_Venus': {'summary': 'Love tested by reality', 'meaning': 'Love meets reality testing',
                                    'life_areas': 'Relationship commitments', 'themes': 'Values face reality checks.',
                                    'shadow_aspect': 'Emotional withholding.',
                                    'grounded_recommendation': 'Invest in lasting value.', 'tone': 'challenging',
                                    'disclaimer': 'Enduring love requires both feeling and commitment.'},
            'Uranus_Opposition_Sun': {'summary': 'Identity disrupted',
                                      'meaning': 'Change disrupts established identity',
                                      'life_areas': 'Life direction, freedom needs',
                                      'themes': 'Restlessness with current identity.',
                                      'shadow_aspect': 'Rebellion for its own sake.',
                                      'grounded_recommendation': 'Notice what you\'ve outgrown.', 'tone': 'challenging',
                                      'disclaimer': 'How you navigate change determines the outcome.'},
            'Uranus_Trine_Venus': {'summary': 'Unconventional attraction', 'meaning': 'Innovation meets attraction',
                                   'life_areas': 'Unconventional relationships',
                                   'themes': 'Attraction to unusual people.', 'shadow_aspect': 'Fickleness.',
                                   'grounded_recommendation': 'Stay open to unexpected connections.',
                                   'tone': 'harmonious',
                                   'disclaimer': 'Innovation is exciting but relationships need attention.'},
            'Uranus_Conjunction_Mercury': {'summary': 'Mind revolutionizes',
                                           'meaning': 'Innovative thinking meets breakthroughs',
                                           'life_areas': 'Sudden insights',
                                           'themes': 'Thinking becomes unusually original.',
                                           'shadow_aspect': 'Scattered thinking.',
                                           'grounded_recommendation': 'Capture ideas but structure them.',
                                           'tone': 'neutral',
                                           'disclaimer': 'Brilliant ideas need coherent communication.'},
            'Neptune_Square_Mercury': {'summary': 'Mental fog clouds judgment',
                                       'meaning': 'Dreams cloud logical thinking',
                                       'life_areas': 'Communication clarity', 'themes': 'Facts feel slippery.',
                                       'shadow_aspect': 'Vulnerability to scams.',
                                       'grounded_recommendation': 'Trust gut but verify facts.', 'tone': 'challenging',
                                       'disclaimer': 'Not every confusion is deception.'},
            'Neptune_Trine_Moon': {'summary': 'Intuition deepens emotionally',
                                   'meaning': 'Dreams support emotional depth', 'life_areas': 'Spiritual connection',
                                   'themes': 'Emotions flow with spiritual sensitivity.',
                                   'shadow_aspect': 'Overwhelming empathy.',
                                   'grounded_recommendation': 'Journal dreams and intuitive hits.',
                                   'tone': 'harmonious', 'disclaimer': 'Spiritual sensitivity needs grounding.'},
            'Neptune_Conjunction_Venus': {'summary': 'Love becomes dreamlike',
                                          'meaning': 'Dreamy love meets idealistic values',
                                          'life_areas': 'Romantic idealism', 'themes': 'Values infused with idealism.',
                                          'shadow_aspect': 'Idealization.',
                                          'grounded_recommendation': 'Appreciate beauty with realistic awareness.',
                                          'tone': 'harmonious', 'disclaimer': 'Idealism needs grounding to sustain.'},
            'Pluto_Square_Venus': {'summary': 'Love transformed intensely',
                                   'meaning': 'Transformation through relationships',
                                   'life_areas': 'Relationship power dynamics',
                                   'themes': 'Relationships become crucibles.', 'shadow_aspect': 'Possessive behavior.',
                                   'grounded_recommendation': 'Notice what you cling to from fear.',
                                   'tone': 'challenging', 'disclaimer': 'Transformation is rarely comfortable.'},
            'Pluto_Trine_Sun': {'summary': 'Personal power awakens',
                                'meaning': 'Personal empowerment through transformation',
                                'life_areas': 'Personal power', 'themes': 'Ability to transform limitations.',
                                'shadow_aspect': 'Power trips.',
                                'grounded_recommendation': 'Use this for deep personal work.', 'tone': 'harmonious',
                                'disclaimer': 'True power is sovereignty over yourself.'},
            'Moon_Conjunction_Venus': {'summary': 'Emotional harmony flows',
                                       'meaning': 'Emotional harmony meets relational needs',
                                       'life_areas': 'Comfort in relationships',
                                       'themes': 'Emotional nature aligns with pleasure.',
                                       'shadow_aspect': 'Using comfort as avoidance.',
                                       'grounded_recommendation': 'Indulge in what genuinely nourishes.',
                                       'tone': 'harmonious', 'disclaimer': 'Lasting peace comes from inner security.'},
            'Moon_Opposition_Mars': {'summary': 'Emotional reactivity spikes',
                                     'meaning': 'Emotional reactions meet assertive impulses',
                                     'life_areas': 'Family dynamics', 'themes': 'Feelings surface with intensity.',
                                     'shadow_aspect': 'Watch for emotional outbursts.',
                                     'grounded_recommendation': 'Pause before reacting.', 'tone': 'challenging',
                                     'disclaimer': 'Feelings are signals, not commands.'},
            'Moon_Trine_Mercury': {'summary': 'Feelings and thoughts cooperate',
                                   'meaning': 'Emotions and thoughts cooperate', 'life_areas': 'Emotional intelligence',
                                   'themes': 'Feelings and thoughts support each other.',
                                   'shadow_aspect': 'Over-analysis of feelings.',
                                   'grounded_recommendation': 'Understand patterns without over-intellectualizing.',
                                   'tone': 'harmonious',
                                   'disclaimer': 'Understanding intellectually doesn\'t mean feeling fully.'},
        }

        # Get specific transit or use enhanced generic fallback
        if key in specific_transits:
            transit_info = specific_transits[key]
            return {
                'summary': transit_info.get('summary', f'{transit_planet} {aspect} {natal_planet}'),
                'meaning': transit_info['meaning'],
                'life_areas': transit_info['life_areas'],
                'themes': transit_info['themes'],
                'shadow_aspect': transit_info.get('shadow_aspect', ''),
                'grounded_recommendation': transit_info.get('grounded_recommendation', ''),
                'tone': transit_info['tone'],
                'disclaimer': transit_info.get('disclaimer', '')
            }
        else:
            # ENHANCED GENERIC FALLBACK
            planet_roles = {
                'Sun': 'identity/ego', 'Moon': 'emotions/security', 'Mercury': 'thinking/communication',
                'Venus': 'values/relationships', 'Mars': 'action/desire', 'Jupiter': 'expansion/beliefs',
                'Saturn': 'structure/limits', 'Uranus': 'change/innovation', 'Neptune': 'dreams/intuition',
                'Pluto': 'transformation/power'
            }

            natal_areas = {
                'Sun': 'core identity and self-expression',
                'Moon': 'emotional security and inner world',
                'Mercury': 'communication and daily thinking',
                'Venus': 'relationships and values',
                'Mars': 'drive and physical energy',
                'Jupiter': 'beliefs and growth opportunities',
                'Saturn': 'responsibilities and long-term goals',
                'Uranus': 'independence and sudden changes',
                'Neptune': 'spirituality and creativity',
                'Pluto': 'transformation and power dynamics'
            }

            t_role = planet_roles.get(transit_planet, 'energy')
            n_role = planet_roles.get(natal_planet, 'area')
            natal_area = natal_areas.get(natal_planet, natal_planet)

            # Aspect themes with psychological nuance
            aspect_themes = {
                'Conjunction': {
                    'summary': f'{transit_planet}-{natal_planet} merge intensely',
                    'meaning': f'Intensified focus on {n_role}',
                    'themes': f'{transit_planet} brings concentrated energy to your natal {natal_planet}. This can feel like a spotlight on your {n_role}.',
                    'recommendation': 'Notice where this energy focuses your attention today.',
                    'tone': 'intense'
                },
                'Trine': {
                    'summary': f'{transit_planet}-{natal_planet} flow harmoniously',
                    'meaning': f'Natural flow between {t_role} and {n_role}',
                    'themes': f'{transit_planet} energy supports your natal {natal_planet} with ease. Opportunities may arise naturally.',
                    'recommendation': 'Trust the flow and notice what comes easily.',
                    'tone': 'harmonious'
                },
                'Square': {
                    'summary': f'{transit_planet}-{natal_planet} create friction',
                    'meaning': f'{t_role} challenges {n_role}',
                    'themes': f'{transit_planet} creates friction with your natal {natal_planet}. This tension invites growth through action.',
                    'recommendation': 'Lean into constructive discomfort rather than avoiding it.',
                    'tone': 'challenging'
                },
                'Opposition': {
                    'summary': f'{transit_planet}-{natal_planet} seek balance',
                    'meaning': f'Balancing {t_role} and {n_role}',
                    'themes': f'{transit_planet} creates awareness of opposing needs. You might feel pulled between different priorities.',
                    'recommendation': 'Look for the middle ground between apparent opposites.',
                    'tone': 'dynamic'
                },
                'Sextile': {
                    'summary': f'{transit_planet}-{natal_planet} cooperate',
                    'meaning': f'Opportunity to align {t_role} and {n_role}',
                    'themes': f'{transit_planet} offers supportive energy for your natal {natal_planet}. Doors open with some initiative.',
                    'recommendation': 'Take small steps toward opportunities you notice.',
                    'tone': 'harmonious'
                }
            }

            theme_info = aspect_themes.get(aspect, {
                'summary': f'{transit_planet}-{natal_planet} interact',
                'meaning': f'Interaction between {transit_planet} and {natal_planet}',
                'themes': f'Cosmic energies interact in your chart today. Observe patterns in your {natal_area}.',
                'recommendation': 'Stay curious about how planetary energies manifest in your experience.',
                'tone': 'neutral'
            })

            return {
                'summary': theme_info['summary'],
                'meaning': theme_info['meaning'],
                'life_areas': natal_area,
                'themes': theme_info['themes'],
                'shadow_aspect': 'Every transit offers both gifts and challenges. Notice any resistance or over-attachment.',
                'grounded_recommendation': theme_info['recommendation'],
                'tone': theme_info['tone'],
                'disclaimer': 'Astrology reflects psychological weather patterns. Your awareness shapes how these energies manifest.'
            }

    def _build_daily_overview_prompt(
            self,
            natal_chart: Dict,
            transits: List[Dict],
            current_positions: Dict,
            moon_phase: Dict,
            journal_context: Optional[str] = None
    ) -> str:
        """Build prompt for daily overview reading with enhanced psychological nuance."""

        # Extract key natal info
        natal_sun = next(p for p in natal_chart['planets'] if p['name'] == 'Sun')
        natal_moon = next(p for p in natal_chart['planets'] if p['name'] == 'Moon')

        # Get top 3 transits
        top_transits = transits[:3] if transits else []

        prompt = f"""Create a psychologically nuanced daily astrological reading for the client.

NATAL CORE IDENTITY:
- Sun in {natal_sun['sign']} (how they express vitality and purpose)
- Moon in {natal_moon['sign']} (their emotional nature and needs)
- Dominant Element: {natal_chart['dominant_element']} (their fundamental energy style)
- Dominant Modality: {natal_chart['dominant_modality']} (how they approach change)

TODAY'S SIGNIFICANT TRANSITS:
"""

        if top_transits:
            prompt += "\nPrimary transits activating their natal chart (use these as psychological foundation):\n"
            for transit in top_transits:
                interpretation = self._get_transit_interpretation_context(transit)
                prompt += f"""
Transit: {transit['transit_planet']} in {transit['transit_sign']} {transit['aspect_type']} Natal {transit['natal_planet']} in {transit['natal_sign']}
Summary: {interpretation.get('summary', 'Planetary interaction')}
Core Psychological Meaning: {interpretation['meaning']}
Life Areas Activated: {interpretation['life_areas']}
Key Themes: {interpretation['themes']}
Shadow Aspect to Watch: {interpretation.get('shadow_aspect', 'No specific shadow noted')}
Grounded Recommendation: {interpretation.get('grounded_recommendation', 'Stay mindful and present')}
Overall Tone: {interpretation['tone']}
Astrological Note: {interpretation.get('disclaimer', '')}

"""
        else:
            prompt += "- No major transits today — subtle background energies at play\n"

        prompt += f"""
CURRENT LUNAR RHYTHM:
{moon_phase['phase']} – {moon_phase['description']}

CLIENT'S CURRENT INNER LANDSCAPE (from today's journal):
{journal_context or "No journal reflections shared today."}

PSYCHOLOGICAL FRAMEWORK GUIDANCE:
- Use the transit interpretation as psychological context, not prediction
- Focus on inner experience more than external events
- Weave 'shadow_aspect' and 'grounded_recommendation' naturally into your interpretation
- Remember: transits highlight psychological weather patterns, not fixed destinies

YOUR TASK AS PSYCHOLOGICALLY-MINDED ASTROLOGER:
Write a 2–3 paragraph reading that feels like a compassionate conversation with a trusted guide.

CRITICAL GUIDELINES:
1. VOICE: Warm, wise, grounded. Never generic horoscope language. Acknowledge both light and shadow without fear-mongering.
2. PERSONALIZATION: Weave their natal chart (Sun/Moon/element) naturally into how they experience these transits.
3. PSYCHOLOGICAL DEPTH: Use the transit interpretations as psychological frameworks, not fate. Focus on inner experience more than external events.
4. JOURNAL INTEGRATION: If journal content exists, reflect it back with empathy—"Given what you've been reflecting on..." or "I sense from your reflections..." 
5. PRACTICAL WISDOM: Include one doable suggestion for navigating today's energies consciously.
6. DISCLAIMER INTEGRATION: Naturally incorporate the astrological notes from interpretations without saying "the disclaimer says..."
7. AVOID: Predictions, absolutes ("will happen"), clichés, unsolicited advice.

CONTENT STRUCTURE:
- Paragraph 1: Connect today's primary transit(s) to their natal nature. How might this energy feel for someone with their Sun/Moon combination?
- Paragraph 2: Practical manifestations + journal integration (if available). What might they notice in thoughts, feelings, or interactions?
- Paragraph 3: Conscious navigation + closing insight. Offer one grounded practice or perspective shift.

Remember: Astrology reveals psychological weather patterns, not fixed destinies. Your reading should empower conscious choice, not passive prediction."""

        return prompt

    def _build_transit_focus_prompt(
            self,
            natal_chart: Dict,
            transits: List[Dict],
            journal_context: Optional[str] = None
    ) -> str:
        """Build prompt focusing on specific transits with psychological depth."""

        if not transits:
            prompt = f"""The client is experiencing a transit-quiet day. 

NATAL PSYCHOLOGICAL PATTERNS:
- Dominant Element: {natal_chart['dominant_element']} (their fundamental energy style)
- Dominant Modality: {natal_chart['dominant_modality']} (how they approach change)

CLIENT'S CURRENT INNER WORLD (from today's journal):
{journal_context or "No journal reflections shared today."}

YOUR TASK:
Write a 2–3 paragraph reflection on working with natal strengths during quiet cosmic periods. Focus on psychological integration and self-awareness rather than external events. Be warm, specific, and grounded."""
            return prompt

        top_transit = transits[0]

        # Extract key natal info
        natal_sun = next(p for p in natal_chart['planets'] if p['name'] == 'Sun')
        natal_moon = next(p for p in natal_chart['planets'] if p['name'] == 'Moon')

        # Get interpretation context for this transit
        interpretation = self._get_transit_interpretation_context(top_transit)

        prompt = f"""Provide an in-depth psychological transit interpretation.

NATAL PSYCHOLOGICAL CONTEXT:
- Sun in {natal_sun['sign']} (core identity expression)
- Moon in {natal_moon['sign']} (emotional processing style)
- Dominant Element: {natal_chart['dominant_element']} (fundamental energy approach)
- Dominant Modality: {natal_chart['dominant_modality']} (change adaptation style)

PRIMARY TRANSIT ANALYSIS:
Transit {top_transit['transit_planet']} in {top_transit['transit_sign']} 
{top_transit['aspect_type']} ({top_transit['quality']})
Natal {top_transit['natal_planet']} in {top_transit['natal_sign']}
Orb: {top_transit['orb']}° | Strength: {top_transit['strength']}

TRANSIT PSYCHOLOGICAL FRAMEWORK:
Summary: {interpretation.get('summary', 'Planetary interaction')}
Core Meaning: {interpretation['meaning']}
Life Areas Activated: {interpretation['life_areas']}
Key Themes: {interpretation['themes']}
Shadow Aspect: {interpretation.get('shadow_aspect', 'No specific shadow noted')}
Grounded Recommendation: {interpretation.get('grounded_recommendation', 'Stay mindful and present')}
Astrological Note: {interpretation.get('disclaimer', '')}

CLIENT'S CURRENT INNER EXPERIENCE (from journal):
{journal_context or "No journal reflections shared today."}

PSYCHOLOGICAL FRAMEWORK GUIDANCE:
- Use the transit interpretation as psychological context, not prediction
- Focus on inner experience more than external events
- Weave 'shadow_aspect' and 'grounded_recommendation' naturally into your interpretation
- Remember: transits highlight psychological weather patterns, not fixed destinies

YOUR TASK AS PSYCHOLOGICAL ASTROLOGER:
Write a focused 2–3 paragraph interpretation exploring the inner landscape this transit activates.

CRITICAL APPROACH:
1. PSYCHOLOGICAL, NOT PREDICTIVE: Frame as psychological weather patterns, not fixed events.
2. INTEGRATE NATAL CONTEXT: How does someone with their Sun/Moon/element experience this transit differently?
3. HONOR JOURNAL CONTENT: If journal exists, weave it naturally—"This transit might be coloring your reflections about..."
4. BALANCE: Acknowledge both challenges and opportunities without polarization.
5. PRACTICAL INSIGHT: Offer psychological understanding first, then grounded suggestions.

CONTENT STRUCTURE:
- Opening: The core psychological invitation of this transit for someone with their natal makeup.
- Middle: How this might manifest in thoughts, emotions, and patterns (connect to journal if available).
- Closing: Conscious navigation framework + one practical insight for working with this energy.

Remember: Your role is to illuminate psychological terrain, not predict the future. Empower conscious choice through astrological insight."""

        return prompt

    def _build_element_wisdom_prompt(
            self,
            natal_chart: Dict,
            current_positions: Dict,
            journal_context: Optional[str] = None
    ) -> str:
        """Build prompt focusing on elemental energies."""

        natal_element = natal_chart['dominant_element']
        current_element = current_positions.get('dominant_element', 'Unknown')

        # Extract key natal info
        natal_sun = next(p for p in natal_chart['planets'] if p['name'] == 'Sun')
        natal_moon = next(p for p in natal_chart['planets'] if p['name'] == 'Moon')

        prompt = f"""Create an elemental wisdom reading exploring psychological patterns.

NATAL ELEMENTAL NATURE:
- Sun in {natal_sun['sign']} (core expression style)
- Moon in {natal_moon['sign']} (emotional element)
- Natal Dominant Element: {natal_element} (their fundamental psychological filter)
- Natal Dominant Modality: {natal_chart['dominant_modality']} (change adaptation style)

TODAY'S ELEMENTAL WEATHER:
- Current Dominant Element: {current_element}

CLIENT'S CURRENT INNER LANDSCAPE (from journal):
{journal_context or "No journal reflections shared today."}

ELEMENTAL PSYCHOLOGY (for reference):
- Fire: Will, inspiration, assertion, impulsivity, passion, anger as information
- Earth: Grounding, practicality, sensuality, stubbornness, stability needs
- Air: Intellect, communication, detachment, analysis, mental restlessness
- Water: Emotion, intuition, empathy, overwhelm, deep feeling, psychic sensitivity

PSYCHOLOGICAL FRAMEWORK GUIDANCE:
- Use elemental patterns as psychological context, not prediction
- Focus on inner experience and energetic states
- Remember: elements reflect psychological weather, not fixed destinies

YOUR TASK:
Write a 2–3 paragraph elemental reading exploring psychological patterns, not predicting events.

CRITICAL GUIDELINES:
1. PSYCHOLOGICAL FRAMEWORK: Elements as psychological filters, not fate.
2. NATAL-CURRENT DANCE: How does their natal element interact with today's elemental weather psychologically?
3. JOURNAL INTEGRATION: If journal exists, reflect how elemental patterns might be coloring their experience.
4. BODY-MIND CONNECTION: Include how this elemental interplay might feel physically or energetically.
5. BALANCE SUGGESTION: Offer one practice to harmonize any elemental imbalance.

APPROACH:
- Start with how their natal {natal_element} nature shapes their psychological approach to life.
- Explore the psychological dance between their natal {natal_element} and today's {current_element} energy.
- Connect to journal themes through elemental lens (if available).
- Close with elemental wisdom for conscious navigation.

Voice: Poetic but precise. Evocative but grounded in psychological reality."""

        return prompt

    def _fallback_reading(self, reading_type: str) -> Dict:
        """Fallback reading if AI generation fails."""

        fallback_texts = {
            'daily_overview': "The cosmos whispers gently today. While the stars hold their patterns, remember that your conscious awareness shapes your experience more than any transit. Check in with your inner wisdom—what does your intuition sense about today's energies?",
            'transit_focus': "Current celestial movements invite psychological reflection. Sometimes the most profound transits are the subtle ones that ask for inner listening rather than outward action. What patterns in your thoughts or feelings might be asking for attention?",
            'element_wisdom': "The elements dance in eternal balance. Your dominant elemental nature offers both strengths and learning edges. Today, consider: How can you honor your elemental essence while remaining fluid with changing energies?"
        }

        return {
            'reading_type': reading_type,
            'reading_text': fallback_texts.get(reading_type,
                                               "The stars hold their mysteries today. Your human experience, with all its complexity and choice, remains the most potent astrology of all."),
            'generated_at': datetime.now().isoformat(),
            'is_fallback': True,
            'journal_included': False,
        }


# Convenience function
def generate_reading(natal_chart: Dict, reading_type: str = 'daily_overview', user=None) -> Dict:
    """
    Quick access to AI reading generation with type-specific data returns.

    Usage:
        from deep_dive.services.ai_reading_service import generate_reading

        # Daily Overview - gets cosmic context data
        daily = generate_reading(chart, 'daily_overview', user=request.user)

        # Transit Focus - gets detailed transit summaries
        transits = generate_reading(chart, 'transit_focus', user=request.user)

        # Element Wisdom - gets elemental analysis, NO transits
        elements = generate_reading(chart, 'element_wisdom', user=request.user)
    """
    service = AIReadingService()
    return service.generate_daily_reading(natal_chart, reading_type, user)