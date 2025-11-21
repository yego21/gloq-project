from datetime import datetime, date
from typing import Dict, Optional, Tuple, List
import pytz
from django.core.cache import cache
import math

try:
    from skyfield.api import load, Topos
    from skyfield.almanac import find_discrete, moon_phases
    from skyfield import almanac
    import numpy as np
except ImportError:
    print("Skyfield not installed. Install with: pip install skyfield")
    load = Topos = moon_phases = almanac = np = None

class NatalChartService:
    """
    Service for calculating natal (birth) charts.

    Architecture:
    - Uses Skyfield for accurate planetary positions
    - Calculates aspects (planetary relationships)
    - NO house calculations (future enhancement)
    - Returns structured data matching NatalChartSchema

    Usage:
        from journal.models import BirthProfile
        birth_profile = BirthProfile.objects.get(user=user)
        service = NatalChartService(birth_profile)
        chart = service.generate_natal_chart()
    """

    def __init__(self, birth_profile):
        """
        Initialize with a user's birth profile.

        Args:
            birth_profile: BirthProfile model instance
        """
        if not all([load, Topos, moon_phases]):
            raise ImportError("Skyfield is required for natal chart calculations")

        self.birth_profile = birth_profile
        self.ts = load.timescale()
        self.eph = load('de421.bsp')

        # Store celestial bodies
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

        # Convert birth datetime to Skyfield time
        self.birth_time = self._get_birth_time()

    def _get_birth_time(self):
        """
        Convert birth profile data to Skyfield time object.

        Handles timezone conversion properly.
        Returns noon UTC if exact time unknown.
        """
        birth_dt = self.birth_profile.get_birth_datetime()

        if birth_dt:
            # User provided exact birth time
            return self.ts.from_datetime(birth_dt)
        else:
            # No exact time - use noon on birth date
            # Noon gives best "average" planetary positions for the day
            tz = pytz.timezone(self.birth_profile.birth_timezone)
            noon_dt = datetime.combine(
                self.birth_profile.birth_date,
                datetime.min.time().replace(hour=12)
            )
            localized_dt = tz.localize(noon_dt)
            return self.ts.from_datetime(localized_dt)

    def calculate_all_planets(self) -> List[Dict]:
        """
        Calculate positions for all major planets at birth time.

        Returns list of planet dictionaries matching PlanetPositionSchema:
        {
            'name': 'Sun',
            'symbol': '☀️',
            'sign': 'Leo',
            'degree': 15,
            'longitude': 135.5,
            'element': 'Fire'
        }
        """
        # Earth observer at birth location
        earth_observer = self.earth + Topos(
            latitude_degrees=float(self.birth_profile.birth_latitude),
            longitude_degrees=float(self.birth_profile.birth_longitude)
        )

        # Define planets to calculate
        # Each tuple: (body_object, name, symbol)
        planets_to_calc = [
            (self.sun, 'Sun', '☀️'),
            (self.moon, 'Moon', '🌙'),
            (self.mercury, 'Mercury', '☿️'),
            (self.venus, 'Venus', '♀️'),
            (self.mars, 'Mars', '♂️'),
            (self.jupiter, 'Jupiter', '♃'),
            (self.saturn, 'Saturn', '♄'),
            (self.uranus, 'Uranus', '♅'),
            (self.neptune, 'Neptune', '♆'),
            (self.pluto, 'Pluto', '♇'),
        ]

        planetary_positions = []

        for body, name, symbol in planets_to_calc:
            # Get position at birth time
            position = earth_observer.at(self.birth_time).observe(body).apparent()

            # Get ecliptic longitude (0-360 degrees)
            longitude = position.ecliptic_latlon()[1].degrees

            # Convert to zodiac sign and degree
            sign = self._get_zodiac_sign(longitude)
            degree = self._get_degree_in_sign(longitude)
            element = self._get_element(sign)

            planetary_positions.append({
                'name': name,
                'symbol': symbol,
                'sign': sign,
                'degree': degree,
                'longitude': longitude,
                'element': element
            })

        return planetary_positions

    def calculate_aspects(self, planetary_positions: List[Dict], orb: float = 8.0) -> List[Dict]:
        """
        Calculate aspects (angular relationships) between planets.

        Aspects:
        - Conjunction: 0° (same position)
        - Sextile: 60° (harmonious)
        - Square: 90° (tension)
        - Trine: 120° (flow)
        - Opposition: 180° (polarity)

        Args:
            planetary_positions: List of planet position dicts
            orb: Allowable deviation in degrees (default 8°)

        Returns:
            List of aspect dictionaries matching AspectSchema
        """
        # Define major aspects with their angles
        aspect_types = [
            (0, 'Conjunction', 8),  # Tight orb for conjunctions
            (60, 'Sextile', 6),
            (90, 'Square', 8),
            (120, 'Trine', 8),
            (180, 'Opposition', 8),
        ]

        aspects = []

        # Compare each planet to every other planet
        for i, planet1 in enumerate(planetary_positions):
            for planet2 in planetary_positions[i + 1:]:  # Avoid duplicates
                # Calculate angular separation
                angle_diff = abs(planet1['longitude'] - planet2['longitude'])

                # Normalize to 0-180 range
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff

                # Check each aspect type
                for aspect_angle, aspect_name, aspect_orb in aspect_types:
                    # How far from exact aspect?
                    deviation = abs(angle_diff - aspect_angle)

                    # Within orb?
                    if deviation <= aspect_orb:
                        aspects.append({
                            'planet1': planet1['name'],
                            'planet2': planet2['name'],
                            'aspect_type': aspect_name,
                            'angle': round(angle_diff, 2),
                            'orb': round(deviation, 2)
                        })
                        break  # Found an aspect, move to next planet pair

        return aspects

    def _calculate_dominant_element(self, planetary_positions: List[Dict]) -> str:
        """
        Determine which element (Fire/Earth/Air/Water) is strongest.
        Based on planetary distribution across signs.
        """
        element_count = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}

        # Count planets in each element
        # Give extra weight to Sun, Moon, and Rising (when we add it)
        for planet in planetary_positions:
            weight = 2 if planet['name'] in ['Sun', 'Moon'] else 1
            element_count[planet['element']] += weight

        # Return dominant element
        return max(element_count, key=element_count.get)

    def _calculate_dominant_modality(self, planetary_positions: List[Dict]) -> str:
        """
        Determine dominant modality (Cardinal/Fixed/Mutable).

        Modalities:
        - Cardinal: Aries, Cancer, Libra, Capricorn (initiating)
        - Fixed: Taurus, Leo, Scorpio, Aquarius (sustaining)
        - Mutable: Gemini, Virgo, Sagittarius, Pisces (adapting)
        """
        modality_map = {
            'Cardinal': ['Aries', 'Cancer', 'Libra', 'Capricorn'],
            'Fixed': ['Taurus', 'Leo', 'Scorpio', 'Aquarius'],
            'Mutable': ['Gemini', 'Virgo', 'Sagittarius', 'Pisces']
        }

        modality_count = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}

        for planet in planetary_positions:
            for modality, signs in modality_map.items():
                if planet['sign'] in signs:
                    weight = 2 if planet['name'] in ['Sun', 'Moon'] else 1
                    modality_count[modality] += weight
                    break

        return max(modality_count, key=modality_count.get)

    def generate_natal_chart(self) -> Dict:
        """
        Generate complete natal chart data.

        This is the main method called by your API endpoint.
        Returns structure matching NatalChartSchema.
        """
        # Calculate all planetary positions
        planets = self.calculate_all_planets()

        # Calculate aspects between planets
        aspects = self.calculate_aspects(planets)

        # Calculate dominant characteristics
        dominant_element = self._calculate_dominant_element(planets)
        dominant_modality = self._calculate_dominant_modality(planets)

        # Build complete chart structure
        natal_chart = {
            'planets': planets,
            'houses': None,  # Future enhancement
            'aspects': aspects,
            'ascendant': None,  # Requires birth time + house calculations
            'midheaven': None,  # Requires birth time + house calculations
            'dominant_element': dominant_element,
            'dominant_modality': dominant_modality,
            'calculated_at': datetime.now(pytz.UTC).isoformat(),
            'has_houses': False  # Will be True when we add house support
        }

        return natal_chart

    # Helper methods (reuse from AstronomicalService)
    def _get_zodiac_sign(self, longitude: float) -> str:
        """Convert celestial longitude to zodiac sign."""
        signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer',
            'Leo', 'Virgo', 'Libra', 'Scorpio',
            'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        longitude = longitude % 360
        sign_index = int(longitude // 30)
        return signs[sign_index]

    def _get_degree_in_sign(self, longitude: float) -> int:
        """Get degree within zodiac sign (0-29)."""
        longitude = longitude % 360
        return int(longitude % 30)

    def _get_element(self, sign: str) -> str:
        """Get element for a zodiac sign."""
        elements = {
            'Fire': ['Aries', 'Leo', 'Sagittarius'],
            'Earth': ['Taurus', 'Virgo', 'Capricorn'],
            'Air': ['Gemini', 'Libra', 'Aquarius'],
            'Water': ['Cancer', 'Scorpio', 'Pisces']
        }

        for element, sign_list in elements.items():
            if sign in sign_list:
                return element
        return 'Unknown'



# Convenience function for easy import
def get_natal_chart(birth_profile) -> Dict:
    """
    Quick access function for natal chart calculation.

    Args:
        birth_profile: BirthProfile model instance

    Returns:
        Complete natal chart dictionary

    Usage:
        from journal.services.astronomical_svc import get_natal_chart
        chart = get_natal_chart(user.birth_profile)
    """
    try:
        service = NatalChartService(birth_profile)
        return service.generate_natal_chart()
    except Exception as e:
        print(f"Natal chart calculation error: {e}")
        # Return minimal fallback structure
        return {
            'planets': [],
            'houses': None,
            'aspects': [],
            'dominant_element': 'Unknown',
            'dominant_modality': 'Unknown',
            'calculated_at': datetime.now(pytz.UTC).isoformat(),
            'has_houses': False
        }

# def get_natal_chart(birth_datetime: datetime, latitude: float, longitude: float) -> Dict[str, any]:
#     """Calculate complete natal chart for given birth data."""
#     try:
#         service = NatalChartService(birth_datetime, latitude, longitude)
#         return service.generate_natal_chart()
#     except Exception as e:
#         print(f"Natal chart service error: {e}")
#         return {
#             'birth_info': {'error': 'Unable to calculate chart'},
#             'planets': [],
#             'houses': [],
#             'aspects': [],
#             'chart_patterns': ['Mystical Configuration'],
#             'element_distribution': {'Fire': 2, 'Earth': 2, 'Air': 3, 'Water': 3},
#             'modality_distribution': {'Cardinal': 3, 'Fixed': 4, 'Mutable': 3},
#             'interpretation': {
#                 'overall_theme': 'Your cosmic blueprint holds mysteries beyond current calculation'
#             }
#         }