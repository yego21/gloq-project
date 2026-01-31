# deep_dive/services/planetary_journal_insight_svc.py
"""
Planetary-Emotion Correlation Analyzer

Analyzes relationship between planetary positions and emotional states.
Reveals which cosmic configurations trigger which feelings.
"""

from django.utils import timezone
from datetime import timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
from skyfield.api import load, Topos


class PlanetaryEmotionCorrelator:
    """
    Correlates planetary positions with emotional journal tags.
    Answers: "Which planets influence which emotions?"
    """

    PLANET_MEANINGS = {
        'Sun': {'focus': 'identity, vitality, ego', 'emoji': '☀️'},
        'Moon': {'focus': 'emotions, instincts, subconscious', 'emoji': '🌙'},
        'Mercury': {'focus': 'communication, thought, processing', 'emoji': '☿️'},
        'Venus': {'focus': 'love, pleasure, values', 'emoji': '♀️'},
        'Mars': {'focus': 'action, desire, frustration', 'emoji': '♂️'},
        'Jupiter': {'focus': 'expansion, optimism, growth', 'emoji': '♃'},
        'Saturn': {'focus': 'structure, discipline, limitation', 'emoji': '♄'},
        'Uranus': {'focus': 'change, rebellion, innovation', 'emoji': '♅'},
        'Neptune': {'focus': 'dreams, confusion, spirituality', 'emoji': '♆'},
        'Pluto': {'focus': 'transformation, power, depth', 'emoji': '♇'},
    }

    def __init__(self, user, days_back: int = 90):
        self.user = user
        self.days_back = days_back
        self.now = timezone.now()
        self.cutoff = self.now - timedelta(days=days_back)

        # Check if user has birth chart
        self.has_birth_chart = (
                hasattr(user, 'birth_profile') and
                user.birth_profile.cached_chart_data
        )

        # Import here to avoid circular imports
        from journal.models import JournalEntry

        # Fetch entries with tags
        self.entries = JournalEntry.objects.filter(
            user=user,
            created_at__gte=self.cutoff
        ).prefetch_related('tags').order_by('created_at')

        self.entry_count = self.entries.count()

        # Initialize Skyfield
        if self.entry_count > 0:
            self.ts = load.timescale()
            self.eph = load('de421.bsp')
            self._init_celestial_bodies()

    def _init_celestial_bodies(self):
        """Initialize planetary ephemeris objects"""
        self.sun = self.eph['sun']
        self.moon = self.eph['moon']
        self.mercury = self.eph['mercury']
        self.venus = self.eph['venus']
        self.mars = self.eph['mars']
        self.jupiter = self.eph['jupiter barycenter']
        self.saturn = self.eph['saturn barycenter']
        self.uranus = self.eph['uranus barycenter']
        self.neptune = self.eph['neptune barycenter']
        self.pluto = self.eph['pluto barycenter']
        self.earth = self.eph['earth']

    def analyze(self) -> Dict:
        """
        Main analysis method.
        Returns planetary-emotion correlations.
        """
        if self.entry_count < 5:
            return self._minimal_analysis()

        # Calculate planetary positions for each entry
        entries_with_planets = self._calculate_entry_planets()

        # Find correlations between planets and emotional intensity
        planet_element_map = self._correlate_planets_emotions(entries_with_planets)

        # Find strongest correlations
        top_correlations = self._find_top_correlations(planet_element_map)

        # Generate insights
        insights = self._generate_insights(planet_element_map)

        return {
            'has_data': True,
            'total_entries': self.entry_count,
            'planet_element_map': planet_element_map,
            'top_correlations': top_correlations,
            'insights': insights,
            'has_birth_chart': self.has_birth_chart
        }

    def _calculate_entry_planets(self) -> List[Dict]:
        """
        Calculate planetary positions for each journal entry.
        Returns list of entries with their planetary data.
        """
        from skyfield.api import utc

        entries_data = []

        for entry in self.entries:
            # Convert entry datetime to UTC for Skyfield
            entry_dt = entry.created_at
            if entry_dt.tzinfo is None:
                entry_dt = entry_dt.replace(tzinfo=utc)
            else:
                entry_dt = entry_dt.astimezone(utc).replace(tzinfo=utc)

            # Create Skyfield time
            entry_time = self.ts.from_datetime(entry_dt)

            # Calculate planetary positions
            planets = self._calculate_planets_at_time(entry_time)

            # Get entry tags with sentiment
            tags = [
                {
                    'name': tag.name,
                    'sentiment': tag.sentiment_score,
                    'emoji': tag.emoji
                }
                for tag in entry.tags.all()
            ]

            entries_data.append({
                'entry': entry,
                'planets': planets,
                'tags': tags,
                'date': entry.created_at
            })

        return entries_data

    def _calculate_planets_at_time(self, skyfield_time) -> Dict:
        """Calculate all planetary positions at a specific time"""
        earth_observer = self.earth

        planets_to_calc = [
            (self.sun, 'Sun'),
            (self.moon, 'Moon'),
            (self.mercury, 'Mercury'),
            (self.venus, 'Venus'),
            (self.mars, 'Mars'),
            (self.jupiter, 'Jupiter'),
            (self.saturn, 'Saturn'),
            (self.uranus, 'Uranus'),
            (self.neptune, 'Neptune'),
            (self.pluto, 'Pluto'),
        ]

        planetary_data = {}

        for body, name in planets_to_calc:
            try:
                position = earth_observer.at(skyfield_time).observe(body).apparent()
                longitude = position.ecliptic_latlon()[1].degrees
                sign = self._get_zodiac_sign(longitude)
                element = self._get_element(sign)

                planetary_data[name] = {
                    'sign': sign,
                    'element': element,
                    'longitude': longitude
                }
            except Exception as e:
                print(f"Error calculating {name}: {e}")
                continue

        return planetary_data

    def _get_zodiac_sign(self, longitude: float) -> str:
        """Convert ecliptic longitude to zodiac sign"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        sign_index = int(longitude / 30)
        return signs[sign_index % 12]

    def _get_element(self, sign: str) -> str:
        """Get element for a zodiac sign"""
        elements = {
            'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
            'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
            'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
            'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
        }
        return elements.get(sign, 'Unknown')

    def _correlate_planets_emotions(self, entries_data: List[Dict]) -> Dict:
        """
        Find correlations between planetary positions and emotional intensity.
        Uses sentiment scores to measure emotional impact.

        Returns structure:
        {
            'Mars': {
                'Fire': {
                    'sentiments': [-0.8, -0.6, -0.7],
                    'emotions': ['frustration', 'stress'],
                    'avg_sentiment': -0.7,
                    'count': 3
                }
            }
        }
        """
        planet_element_correlations = defaultdict(lambda: defaultdict(lambda: {
            'sentiments': [],
            'emotions': Counter(),
            'dates': []
        }))

        for entry_data in entries_data:
            planets = entry_data['planets']
            tags = entry_data['tags']

            # Calculate average sentiment for this entry
            if tags:
                entry_sentiment = sum(tag['sentiment'] for tag in tags) / len(tags)

                # For each planet, track sentiment when it's in each element
                for planet_name, planet_data in planets.items():
                    element = planet_data['element']
                    sign = planet_data['sign']

                    planet_element_correlations[planet_name][element]['sentiments'].append(entry_sentiment)
                    planet_element_correlations[planet_name][element]['dates'].append(entry_data['date'])

                    # Track which emotions appear
                    for tag in tags:
                        planet_element_correlations[planet_name][element]['emotions'][tag['name']] += 1

        # Calculate averages
        result = {}
        for planet, elements in planet_element_correlations.items():
            result[planet] = {}
            for element, data in elements.items():
                if data['sentiments']:
                    result[planet][element] = {
                        'avg_sentiment': sum(data['sentiments']) / len(data['sentiments']),
                        'sentiment_range': (min(data['sentiments']), max(data['sentiments'])),
                        'count': len(data['sentiments']),
                        'top_emotions': data['emotions'].most_common(3),
                        'dates': data['dates']
                    }

        return result

    def _find_top_correlations(self, planet_element_map: Dict) -> List[Dict]:
        """
        Find the strongest planet-element-sentiment correlations.
        Returns top 8 most significant patterns.
        """
        correlations = []

        # Calculate baseline sentiment (across all entries)
        all_sentiments = []
        for planet_data in planet_element_map.values():
            for element_data in planet_data.values():
                all_sentiments.extend([element_data['avg_sentiment']] * element_data['count'])

        baseline_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0

        for planet, elements in planet_element_map.items():
            for element, data in elements.items():
                avg_sentiment = data['avg_sentiment']
                count = data['count']

                # Calculate deviation from baseline
                sentiment_shift = avg_sentiment - baseline_sentiment
                shift_percentage = (sentiment_shift / (abs(baseline_sentiment) + 0.1)) * 100  # Avoid div by 0

                # Only include significant patterns (5+ occurrences)
                if count >= 5:
                    top_emotion = data['top_emotions'][0] if data['top_emotions'] else ('mixed', 0)

                    correlations.append({
                        'planet': planet,
                        'element': element,
                        'avg_sentiment': avg_sentiment,
                        'baseline_sentiment': baseline_sentiment,
                        'sentiment_shift': sentiment_shift,
                        'shift_percentage': shift_percentage,
                        'count': count,
                        'top_emotion': top_emotion[0],
                        'sentiment_range': data['sentiment_range']
                    })

        # Sort by absolute sentiment shift (most impactful)
        correlations.sort(key=lambda x: abs(x['sentiment_shift']) * x['count'], reverse=True)
        return correlations[:8]

    def _generate_insights(self, planet_element_map: Dict) -> List[str]:
        """Generate human-readable insights from sentiment-based correlations"""
        insights = []

        # Calculate baseline
        all_sentiments = []
        for planet_data in planet_element_map.values():
            for element_data in planet_data.values():
                all_sentiments.extend([element_data['avg_sentiment']] * element_data['count'])

        baseline = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0

        # Find most impactful planet-element combos
        impact_list = []
        for planet, elements in planet_element_map.items():
            for element, data in elements.items():
                if data['count'] >= 5:  # Significant sample size
                    shift = data['avg_sentiment'] - baseline
                    impact_list.append(
                        (planet, element, shift, data['count'], data['top_emotions'], data['avg_sentiment']))

        # Sort by absolute impact
        impact_list.sort(key=lambda x: abs(x[2]) * x[3], reverse=True)

        # Generate insights from top patterns with better phrasing
        for planet, element, shift, count, top_emotions, avg_sent in impact_list[:6]:
            emotion = top_emotions[0][0] if top_emotions else "mixed emotions"

            # Use descriptive labels instead of percentages
            if avg_sent < -0.3:
                label = "significantly challenging"
            elif avg_sent < -0.1:
                label = "mildly challenging"
            elif avg_sent < 0.1:
                label = "neutral"
            elif avg_sent < 0.3:
                label = "slightly uplifting"
            else:
                label = "significantly uplifting"

            if shift < -0.02:  # Negative shift
                insights.append(
                    f"{planet} in {element} signs correlates with {label} emotions "
                    f"(avg: {avg_sent:+.2f}, often '{emotion}')"
                )
            elif shift > 0.02:  # Positive shift
                insights.append(
                    f"{planet} in {element} signs correlates with {label} emotions "
                    f"(avg: {avg_sent:+.2f}, often '{emotion}')"
                )

        return insights[:5] if insights else ["Continue journaling to build stronger planetary-emotion patterns"]

    def _minimal_analysis(self) -> Dict:
        """Return minimal data when not enough entries"""
        return {
            'has_data': False,
            'total_entries': self.entry_count,
            'message': f"Need at least 5 entries to detect planetary-emotion patterns (you have {self.entry_count})",
            'planet_emotion_map': {},
            'top_correlations': [],
            'insights': []
        }