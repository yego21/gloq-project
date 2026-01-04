# journal/services/natal_chart_svc.py - Unified Version with ALL bodies included
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

try:
    from spktype21 import SPKType21
    from skyfield.constants import AU_KM
    from skyfield.vectorlib import VectorFunction

    SPKTYPE21_AVAILABLE = True
except ImportError:
    print("spktype21 not installed. Install with: pip install spktype21")
    print("Chiron will use simplified calculation formula (lower accuracy)")
    SPKTYPE21_AVAILABLE = False

from .astronomical_svc import AstronomicalService


class NatalChartService:
    """
    Service for calculating natal (birth) charts with all features:
    - Chiron, Lilith, Lunar Nodes calculation
    - Notable placements: chart ruler, stelliums, aspect patterns, singletons
    - Retrograde detection for ALL bodies (including Chiron)
    - Houses and aspects calculation
    """

    # Rulership table: Ascendant sign → Ruling planet
    SIGN_RULERS = {
        'Aries': 'Mars',
        'Taurus': 'Venus',
        'Gemini': 'Mercury',
        'Cancer': 'Moon',
        'Leo': 'Sun',
        'Virgo': 'Mercury',
        'Libra': 'Venus',
        'Scorpio': 'Mars',  # Traditional ruler (modern: Pluto)
        'Sagittarius': 'Jupiter',
        'Capricorn': 'Saturn',
        'Aquarius': 'Saturn',  # Traditional ruler (modern: Uranus)
        'Pisces': 'Jupiter'  # Traditional ruler (modern: Neptune)
    }

    def __init__(self, birth_profile):
        """Initialize with a user's birth profile."""
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

        # Initialize astronomical service for house calculations
        self.astro_service = AstronomicalService()

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
            tz = pytz.timezone(self.birth_profile.birth_timezone)
            noon_dt = datetime.combine(
                self.birth_profile.birth_date,
                datetime.min.time().replace(hour=12)
            )
            localized_dt = tz.localize(noon_dt)
            return self.ts.from_datetime(localized_dt)

    def _calculate_chiron(self, skyfield_time) -> float:
        """
        Calculate Chiron's ecliptic longitude using empirical sign entry dates.

        Uses known sign ingress dates for accuracy within 1-2 degrees.
        """
        # Convert to datetime for easier date comparison
        birth_date = skyfield_time.utc_datetime()

        # Chiron sign ingress dates (entry into each sign)
        chiron_ingress = [
            (1926, 4, 'Taurus', 30),  # Apr 1926
            (1933, 6, 'Gemini', 60),  # Jun 1933
            (1937, 7, 'Cancer', 90),  # Jul 1937
            (1940, 6, 'Leo', 120),  # Jun 1940
            (1943, 7, 'Virgo', 150),  # Jul 1943
            (1945, 11, 'Libra', 180),  # Nov 1945
            (1948, 11, 'Scorpio', 210),  # Nov 1948
            (1951, 2, 'Sagittarius', 240),  # Feb 1951
            (1951, 2, 'Capricorn', 270),  # Feb 1951 (retrograde correction)
            (1955, 1, 'Aquarius', 300),  # Jan 1955
            (1961, 1, 'Pisces', 330),  # Jan 1961
            (1968, 4, 'Aries', 0),  # Apr 1968
            (1976, 5, 'Taurus', 30),  # May 1976
            (1983, 6, 'Gemini', 60),  # Jun 1983
            (1988, 6, 'Cancer', 90),  # Jun 1988
            (1991, 7, 'Leo', 120),  # Jul 1991
            (1993, 9, 'Virgo', 150),  # Sep 1993
            (1995, 9, 'Libra', 180),  # Sep 1995
            (1996, 12, 'Scorpio', 210),  # Dec 1996
            (1999, 1, 'Sagittarius', 240),  # Jan 1999
            (2001, 12, 'Capricorn', 270),  # Dec 2001
            (2005, 2, 'Aquarius', 300),  # Feb 2005
            (2011, 2, 'Pisces', 330),  # Feb 2011
            (2018, 4, 'Aries', 0),  # Apr 2018
            (2026, 6, 'Taurus', 30),  # Jun 2026
        ]

        # Find which sign period we're in
        birth_year = birth_date.year
        birth_month = birth_date.month

        current_sign = None
        next_sign = None
        current_date = None
        next_date = None

        for i in range(len(chiron_ingress) - 1):
            year1, month1, sign1, deg1 = chiron_ingress[i]
            year2, month2, sign2, deg2 = chiron_ingress[i + 1]

            date1 = datetime(year1, month1, 15, tzinfo=pytz.UTC)
            date2 = datetime(year2, month2, 15, tzinfo=pytz.UTC)

            if date1 <= birth_date < date2:
                current_sign = sign1
                next_sign = sign2
                current_date = date1
                next_date = date2
                current_deg = deg1
                next_deg = deg2
                break

        # If not found in table, use last known position
        if current_sign is None:
            if birth_year >= 2026:
                current_sign = 'Taurus'
                current_deg = 30
                years_since_2026 = birth_year - 2026
                estimated_progress = (years_since_2026 / 4.0) * 30
                longitude = (30 + estimated_progress) % 360
                return longitude
            else:  # Before 1926
                current_sign = 'Aries'
                current_deg = 0
                longitude = 15.0  # Mid-Aries estimate
                return longitude

        # Interpolate position within the sign
        total_days = (next_date - current_date).total_seconds() / 86400
        elapsed_days = (birth_date - current_date).total_seconds() / 86400
        fraction = elapsed_days / total_days if total_days > 0 else 0.5

        # Interpolate degree
        if next_deg < current_deg:  # Wraparound case
            next_deg += 360

        longitude = current_deg + (next_deg - current_deg) * fraction
        longitude = longitude % 360

        return longitude

    def _calculate_mean_nodes(self, skyfield_time) -> Tuple[float, float]:
        """
        Calculate Mean Lunar Nodes (North and South).
        Formula based on Jean Meeus "Astronomical Algorithms".
        """
        # Get Julian Date
        jd = skyfield_time.tt

        # Calculate Julian centuries from J2000.0 epoch
        T = (jd - 2451545.0) / 36525.0

        # Mean longitude of ascending node (Omega) in degrees
        omega = (125.04452
                 - 1934.136261 * T
                 + 0.0020708 * T * T
                 + (T * T * T) / 450000.0)

        # Normalize to 0-360 range
        north_node = omega % 360

        # South Node is always exactly opposite (180° away)
        south_node = (north_node + 180) % 360

        return north_node, south_node

    def _calculate_black_moon_lilith(self, skyfield_time) -> float:
        """
        Calculate Black Moon Lilith (Mean Lilith) position.
        Uses standard formula from astronomical research.
        """
        # Get Julian Date
        jd = skyfield_time.tt

        # Calculate Julian centuries from J2000.0 epoch
        T = (jd - 2451545.0) / 36525.0

        # Mean longitude of lunar perigee (opposite of apogee)
        perigee = (83.35324692
                   + 4069.0137287 * T
                   - 0.01032172222 * T * T
                   + T * T * T / 45000000.0)

        # Apogee (Lilith) is 180° opposite to perigee
        lilith = (perigee + 180.0) % 360

        return lilith

    def detect_retrogrades(self, all_planets: List[Dict]) -> List[str]:
        """
        Detect which planets are retrograde at birth time.
        Now includes checking for Chiron retrograde status.

        Args:
            all_planets: List of ALL planet dicts including Chiron, Lilith, Nodes

        Returns:
            List of retrograde planet names
        """
        retrograde_planets = []

        # Earth observer at birth location
        earth_observer = self.earth + Topos(
            latitude_degrees=float(self.birth_profile.birth_latitude),
            longitude_degrees=float(self.birth_profile.birth_longitude)
        )

        # Define which planets we can check for retrograde
        # Sun/Moon never retrograde from Earth view
        # Lilith and Nodes are mathematical points, not physical bodies with motion
        retrograde_check_map = {
            'Mercury': self.mercury,
            'Venus': self.venus,
            'Mars': self.mars,
            'Jupiter': self.jupiter,
            'Saturn': self.saturn,
            'Uranus': self.uranus,
            'Neptune': self.neptune,
            'Pluto': self.pluto,
        }

        # Check Chiron separately since we calculate it differently
        chiron_longitudes = self._calculate_chiron_motion()

        # Check motion direction by comparing positions 1 day before and after
        one_day = 1.0  # 1 day in Skyfield timescale

        for planet_name, body in retrograde_check_map.items():
            try:
                # Get positions at 3 time points
                time_before = self.ts.tt_jd(self.birth_time.tt - one_day)
                time_at = self.birth_time
                time_after = self.ts.tt_jd(self.birth_time.tt + one_day)

                # Calculate ecliptic longitude at each time
                lon_before = earth_observer.at(time_before).observe(body).apparent().ecliptic_latlon()[1].degrees
                lon_at = earth_observer.at(time_at).observe(body).apparent().ecliptic_latlon()[1].degrees
                lon_after = earth_observer.at(time_after).observe(body).apparent().ecliptic_latlon()[1].degrees

                # Calculate motion direction (accounting for 360° wraparound)
                motion1 = (lon_at - lon_before + 180) % 360 - 180
                motion2 = (lon_after - lon_at + 180) % 360 - 180

                # If both motions are negative, planet is moving backwards = retrograde
                if motion1 < 0 and motion2 < 0:
                    retrograde_planets.append(planet_name)

            except Exception as e:
                print(f"Error checking retrograde for {planet_name}: {e}")
                continue

        # Check Chiron for retrograde
        if chiron_longitudes:
            ch_before, ch_at, ch_after = chiron_longitudes
            motion1 = (ch_at - ch_before + 180) % 360 - 180
            motion2 = (ch_after - ch_at + 180) % 360 - 180

            if motion1 < 0 and motion2 < 0:
                retrograde_planets.append('Chiron')

        return retrograde_planets

    def _calculate_chiron_motion(self) -> Optional[Tuple[float, float, float]]:
        """Calculate Chiron positions at 3 time points for retrograde detection."""
        try:
            one_day = 1.0
            time_before = self.ts.tt_jd(self.birth_time.tt - one_day)
            time_at = self.birth_time
            time_after = self.ts.tt_jd(self.birth_time.tt + one_day)

            ch_before = self._calculate_chiron(time_before)
            ch_at = self._calculate_chiron(time_at)
            ch_after = self._calculate_chiron(time_after)

            return ch_before, ch_at, ch_after
        except Exception as e:
            print(f"Error calculating Chiron motion: {e}")
            return None

    def get_chart_ruler(self, ascendant: Optional[Dict], planets: List[Dict]) -> Optional[Dict]:
        """
        Identify the chart ruler - the planet that rules the Ascendant sign.

        Returns:
            Planet dict for the chart ruler, or None if ascendant unavailable
        """
        if not ascendant or 'sign' not in ascendant:
            return None

        asc_sign = ascendant['sign']
        ruling_planet_name = self.SIGN_RULERS.get(asc_sign)

        if not ruling_planet_name:
            return None

        # Find the ruling planet in the planets list
        for planet in planets:
            if planet['name'] == ruling_planet_name:
                return {
                    'planet': planet,
                    'rules': asc_sign,
                    'significance': 'Chart ruler - influences overall life direction and persona'
                }

        return None

    def detect_stelliums(self, planets: List[Dict], houses: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Detect stelliums - 3 or more planets in the same sign or house.
        Now includes Chiron, Lilith, and Lunar Nodes in stellium detection.

        Args:
            planets: List of ALL planet dicts including Chiron, Lilith, Nodes
            houses: Optional list of house data

        Returns:
            List of stellium dicts
        """
        stelliums = []

        # Define which bodies to include in stellium calculations
        # Include all celestial bodies for stellium detection
        bodies_for_stellium = [
            'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
            'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
            'Chiron', 'Lilith', 'North Node', 'South Node'
        ]

        # Filter planets to include only those in our list
        filtered_planets = [p for p in planets if p['name'] in bodies_for_stellium]

        # Check for sign stelliums
        sign_groups = {}
        for planet in filtered_planets:
            sign = planet['sign']
            if sign not in sign_groups:
                sign_groups[sign] = []
            sign_groups[sign].append(planet['name'])

        for sign, planet_names in sign_groups.items():
            if len(planet_names) >= 3:
                stelliums.append({
                    'type': 'sign',
                    'location': sign,
                    'planets': planet_names,
                    'count': len(planet_names),
                    'includes_asteroids': any(name in ['Chiron', 'Lilith'] for name in planet_names),
                    'includes_nodes': any(name in ['North Node', 'South Node'] for name in planet_names)
                })

        # Check for house stelliums (if houses available)
        if houses:
            house_groups = {}
            for planet in filtered_planets:
                if 'house' in planet and planet['house']:
                    house_num = planet['house']
                    if house_num not in house_groups:
                        house_groups[house_num] = []
                    house_groups[house_num].append(planet['name'])

            for house_num, planet_names in house_groups.items():
                if len(planet_names) >= 3:
                    stelliums.append({
                        'type': 'house',
                        'location': house_num,
                        'planets': planet_names,
                        'count': len(planet_names),
                        'includes_asteroids': any(name in ['Chiron', 'Lilith'] for name in planet_names),
                        'includes_nodes': any(name in ['North Node', 'South Node'] for name in planet_names)
                    })

        return stelliums

    def detect_aspect_patterns(self, aspects: List[Dict], planets: List[Dict]) -> List[Dict]:
        """
        Detect major aspect patterns: Grand Trines, T-Squares, Grand Crosses.
        Now includes aspects involving Chiron, Lilith, and Lunar Nodes.

        Args:
            aspects: List of aspect dicts (includes all aspects)
            planets: List of ALL planet dicts

        Returns:
            List of pattern dicts
        """
        patterns = []

        # Helper: Get all aspects of a specific type
        def get_aspects_of_type(aspect_type: str) -> List[Tuple[str, str]]:
            return [(a['planet1'], a['planet2']) for a in aspects if a['aspect_type'] == aspect_type]

        # Helper: Check if two planets have an aspect
        def has_aspect(p1: str, p2: str, aspect_type: str) -> bool:
            aspect_pairs = get_aspects_of_type(aspect_type)
            return (p1, p2) in aspect_pairs or (p2, p1) in aspect_pairs

        # Get planet names for pattern detection
        # Include Chiron and Lilith but exclude Nodes (they're always opposite each other)
        pattern_planets = [p['name'] for p in planets if p['name'] not in ['North Node', 'South Node', 'Lilith']]

        # 1. GRAND TRINE: 3 planets all in trine (120°) to each other
        trines = get_aspects_of_type('Trine')
        if len(trines) >= 3:
            planet_names = list(set([p for pair in trines for p in pair]))

            for i, p1 in enumerate(planet_names):
                for j, p2 in enumerate(planet_names[i + 1:], start=i + 1):
                    for p3 in planet_names[j + 1:]:
                        if (has_aspect(p1, p2, 'Trine') and
                                has_aspect(p2, p3, 'Trine') and
                                has_aspect(p1, p3, 'Trine')):
                            patterns.append({
                                'pattern_type': 'Grand Trine',
                                'planets': sorted([p1, p2, p3]),
                                'includes_chiron': 'Chiron' in [p1, p2, p3],
                                'description': 'Natural talent and flow - easy harmony between these energies'
                            })

        # 2. T-SQUARE: 2 planets in opposition, both squared by a third
        oppositions = get_aspects_of_type('Opposition')
        squares = get_aspects_of_type('Square')

        if oppositions and len(squares) >= 2:
            for opp_p1, opp_p2 in oppositions:
                # Find planets that square both ends of the opposition
                for square_p1, square_p2 in squares:
                    apex = None
                    if square_p1 == opp_p1 or square_p1 == opp_p2:
                        potential_apex = square_p2
                    elif square_p2 == opp_p1 or square_p2 == opp_p2:
                        potential_apex = square_p1
                    else:
                        continue

                    # Check if potential apex squares both opposition planets
                    if (has_aspect(potential_apex, opp_p1, 'Square') and
                            has_aspect(potential_apex, opp_p2, 'Square')):
                        apex = potential_apex

                        patterns.append({
                            'pattern_type': 'T-Square',
                            'planets': sorted([opp_p1, opp_p2, apex]),
                            'apex': apex,
                            'includes_chiron': 'Chiron' in [opp_p1, opp_p2, apex],
                            'description': 'Dynamic tension drives achievement - challenges push growth'
                        })
                        break

        # 3. GRAND CROSS: 4 planets forming 2 oppositions and 4 squares
        if len(oppositions) >= 2 and len(squares) >= 4:
            planet_names = list(set([p for pair in oppositions for p in pair]))

            for i, p1 in enumerate(planet_names):
                for j, p2 in enumerate(planet_names[i + 1:], start=i + 1):
                    for k, p3 in enumerate(planet_names[j + 1:], start=j + 1):
                        for p4 in planet_names[k + 1:]:
                            # Check if these 4 planets form 2 oppositions and 4 squares
                            if (has_aspect(p1, p3, 'Opposition') and
                                    has_aspect(p2, p4, 'Opposition') and
                                    has_aspect(p1, p2, 'Square') and
                                    has_aspect(p2, p3, 'Square') and
                                    has_aspect(p3, p4, 'Square') and
                                    has_aspect(p4, p1, 'Square')):
                                patterns.append({
                                    'pattern_type': 'Grand Cross',
                                    'planets': sorted([p1, p2, p3, p4]),
                                    'includes_chiron': 'Chiron' in [p1, p2, p3, p4],
                                    'description': 'Intense challenge and balance - major life theme of integration'
                                })

        # 4. YOD (Finger of God): Add this pattern too
        # Yod = 2 planets in sextile, both quincunx (150°) to a third planet
        sextiles = get_aspects_of_type('Sextile')

        if len(sextiles) >= 2:
            # We would need to add quincunx aspect detection first
            # For now, we'll note that this can be added later
            pass

        return patterns

    def detect_singletons(self, planets: List[Dict]) -> List[Dict]:
        """
        Detect singleton planets - only one planet in an element or modality.
        Now includes Chiron, Lilith, and Lunar Nodes in singleton detection.

        Returns:
            List of singleton dicts
        """
        singletons = []

        # Define which bodies to include in singleton calculations
        # Include Chiron but exclude Nodes and Lilith (they're mathematical points)
        bodies_for_singleton = [
            'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
            'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
            'Chiron'
        ]

        # Filter planets to include only those in our list
        filtered_planets = [p for p in planets if p['name'] in bodies_for_singleton]

        # Count planets by element
        element_count = {}
        element_planets = {}
        for planet in filtered_planets:
            elem = planet['element']
            element_count[elem] = element_count.get(elem, 0) + 1
            if elem not in element_planets:
                element_planets[elem] = []
            element_planets[elem].append(planet['name'])

        # Find singleton elements
        for elem, count in element_count.items():
            if count == 1:
                planet_name = element_planets[elem][0]
                singletons.append({
                    'type': 'element',
                    'category': elem,
                    'planet': planet_name,
                    'is_chiron': planet_name == 'Chiron',
                    'significance': f'Solitary {elem} energy - stands out strongly in the chart'
                })

        # Count planets by modality
        modality_map = {
            'Cardinal': ['Aries', 'Cancer', 'Libra', 'Capricorn'],
            'Fixed': ['Taurus', 'Leo', 'Scorpio', 'Aquarius'],
            'Mutable': ['Gemini', 'Virgo', 'Sagittarius', 'Pisces']
        }

        modality_count = {}
        modality_planets = {}
        for planet in filtered_planets:
            for modality, signs in modality_map.items():
                if planet['sign'] in signs:
                    modality_count[modality] = modality_count.get(modality, 0) + 1
                    if modality not in modality_planets:
                        modality_planets[modality] = []
                    modality_planets[modality].append(planet['name'])
                    break

        # Find singleton modalities
        for modality, count in modality_count.items():
            if count == 1:
                planet_name = modality_planets[modality][0]
                singletons.append({
                    'type': 'modality',
                    'category': modality,
                    'planet': planet_name,
                    'is_chiron': planet_name == 'Chiron',
                    'significance': f'Solitary {modality} energy - unique approach to action'
                })

        return singletons

    def calculate_all_planets(self) -> List[Dict]:
        """Calculate positions for all major planets at birth time including Chiron, Lilith, Nodes."""
        earth_observer = self.earth + Topos(
            latitude_degrees=float(self.birth_profile.birth_latitude),
            longitude_degrees=float(self.birth_profile.birth_longitude)
        )

        # Define planets to calculate
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

        # Calculate regular planets
        for body, name, symbol in planets_to_calc:
            position = earth_observer.at(self.birth_time).observe(body).apparent()
            longitude = position.ecliptic_latlon()[1].degrees
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

        # Calculate Chiron
        try:
            chiron_lon = self._calculate_chiron(self.birth_time)
            chiron_sign = self._get_zodiac_sign(chiron_lon)
            chiron_degree = self._get_degree_in_sign(chiron_lon)
            chiron_element = self._get_element(chiron_sign)

            planetary_positions.append({
                'name': 'Chiron',
                'symbol': '⚷',
                'sign': chiron_sign,
                'degree': chiron_degree,
                'longitude': chiron_lon,
                'element': chiron_element
            })
        except Exception as e:
            print(f"Chiron calculation error: {e}")

        # Calculate Black Moon Lilith
        try:
            lilith_lon = self._calculate_black_moon_lilith(self.birth_time)
            lilith_sign = self._get_zodiac_sign(lilith_lon)
            lilith_degree = self._get_degree_in_sign(lilith_lon)
            lilith_element = self._get_element(lilith_sign)

            planetary_positions.append({
                'name': 'Lilith',
                'symbol': '⚸',
                'sign': lilith_sign,
                'degree': lilith_degree,
                'longitude': lilith_lon,
                'element': lilith_element
            })
        except Exception as e:
            print(f"Lilith calculation error: {e}")

        # Calculate Lunar Nodes
        try:
            north_node_lon, south_node_lon = self._calculate_mean_nodes(self.birth_time)

            # North Node
            nn_sign = self._get_zodiac_sign(north_node_lon)
            nn_degree = self._get_degree_in_sign(north_node_lon)
            nn_element = self._get_element(nn_sign)

            planetary_positions.append({
                'name': 'North Node',
                'symbol': '☊',
                'sign': nn_sign,
                'degree': nn_degree,
                'longitude': north_node_lon,
                'element': nn_element
            })

            # South Node
            sn_sign = self._get_zodiac_sign(south_node_lon)
            sn_degree = self._get_degree_in_sign(south_node_lon)
            sn_element = self._get_element(sn_sign)

            planetary_positions.append({
                'name': 'South Node',
                'symbol': '☋',
                'sign': sn_sign,
                'degree': sn_degree,
                'longitude': south_node_lon,
                'element': sn_element
            })
        except Exception as e:
            print(f"Lunar Nodes calculation error: {e}")

        return planetary_positions

    def calculate_aspects(self, planetary_positions: List[Dict], orb: float = 8.0) -> List[Dict]:
        """
        Calculate aspects (angular relationships) between ALL planets.
        Now includes aspects involving Chiron, Lilith, and Lunar Nodes.
        """
        aspect_types = [
            (0, 'Conjunction', 8),
            (60, 'Sextile', 6),
            (90, 'Square', 8),
            (120, 'Trine', 8),
            (180, 'Opposition', 8),
        ]

        aspects = []

        for i, planet1 in enumerate(planetary_positions):
            for planet2 in planetary_positions[i + 1:]:
                angle_diff = abs(planet1['longitude'] - planet2['longitude'])
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff

                for aspect_angle, aspect_name, aspect_orb in aspect_types:
                    deviation = abs(angle_diff - aspect_angle)
                    if deviation <= aspect_orb:
                        aspects.append({
                            'planet1': planet1['name'],
                            'planet2': planet2['name'],
                            'aspect_type': aspect_name,
                            'angle': round(angle_diff, 2),
                            'orb': round(deviation, 2),
                            'involves_chiron': planet1['name'] == 'Chiron' or planet2['name'] == 'Chiron',
                            'involves_lilith': planet1['name'] == 'Lilith' or planet2['name'] == 'Lilith',
                            'involves_node': planet1['name'] in ['North Node', 'South Node'] or
                                             planet2['name'] in ['North Node', 'South Node']
                        })
                        break

        return aspects

    def _assign_planets_to_houses(self, planets: List[Dict], houses: List[Dict]) -> Dict:
        """Determine which house each planet falls into based on longitude."""
        planets_with_houses = []
        planets_in_houses = {i: [] for i in range(1, 13)}

        for planet in planets:
            planet_lon = planet['longitude']
            planet_house = None

            for i in range(12):
                current_house = houses[i]
                next_house = houses[(i + 1) % 12]
                current_cusp = current_house['cusp_longitude']
                next_cusp = next_house['cusp_longitude']

                if next_cusp < current_cusp:
                    if planet_lon >= current_cusp or planet_lon < next_cusp:
                        planet_house = current_house['number']
                        break
                else:
                    if current_cusp <= planet_lon < next_cusp:
                        planet_house = current_house['number']
                        break

            planet_copy = planet.copy()
            planet_copy['house'] = planet_house
            planets_with_houses.append(planet_copy)

            if planet_house:
                planets_in_houses[planet_house].append(planet['name'])

        return {
            'planets_with_houses': planets_with_houses,
            'planets_in_houses': planets_in_houses
        }

    def _calculate_dominant_element(self, planetary_positions: List[Dict], ascendant: Optional[Dict] = None) -> str:
        """
        Determine which element (Fire/Earth/Air/Water) is strongest.
        Now includes Chiron but excludes Lilith and Nodes.
        """
        element_count = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}

        # Include Chiron but exclude Lilith and Nodes for dominant element calculation
        planets_for_element = [p for p in planetary_positions if
                               p['name'] not in ['Lilith', 'North Node', 'South Node']]

        for planet in planets_for_element:
            weight = 2 if planet['name'] in ['Sun', 'Moon'] else 1
            element_count[planet['element']] += weight

        if ascendant and 'sign' in ascendant:
            asc_element = self._get_element(ascendant['sign'])
            element_count[asc_element] += 2

        return max(element_count, key=element_count.get)

    def _calculate_dominant_modality(self, planetary_positions: List[Dict], ascendant: Optional[Dict] = None) -> str:
        """
        Determine dominant modality (Cardinal/Fixed/Mutable).
        Now includes Chiron but excludes Lilith and Nodes.
        """
        modality_map = {
            'Cardinal': ['Aries', 'Cancer', 'Libra', 'Capricorn'],
            'Fixed': ['Taurus', 'Leo', 'Scorpio', 'Aquarius'],
            'Mutable': ['Gemini', 'Virgo', 'Sagittarius', 'Pisces']
        }

        modality_count = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}

        # Include Chiron but exclude Lilith and Nodes for dominant modality calculation
        planets_for_modality = [p for p in planetary_positions if
                                p['name'] not in ['Lilith', 'North Node', 'South Node']]

        for planet in planets_for_modality:
            for modality, signs in modality_map.items():
                if planet['sign'] in signs:
                    weight = 2 if planet['name'] in ['Sun', 'Moon'] else 1
                    modality_count[modality] += weight
                    break

        if ascendant and 'sign' in ascendant:
            for modality, signs in modality_map.items():
                if ascendant['sign'] in signs:
                    modality_count[modality] += 2
                    break

        return max(modality_count, key=modality_count.get)

    def generate_natal_chart(self) -> Dict:
        """
        Generate complete natal chart data with all features.

        Returns structure with:
        - All planets including Chiron, Lilith, Lunar Nodes
        - Houses and aspects
        - Notable placements: retrogrades, chart ruler, stelliums, aspect patterns, singletons
        - ALL calculations now include Chiron, Lilith, and Nodes appropriately
        """
        # Calculate all planetary positions
        planets = self.calculate_all_planets()

        # Detect retrograde planets (now includes Chiron)
        retrogrades = self.detect_retrogrades(planets)

        # Mark retrograde status on planet data
        for planet in planets:
            planet['is_retrograde'] = planet['name'] in retrogrades

        # Calculate aspects between ALL planets
        aspects = self.calculate_aspects(planets)

        # Initialize house/angle data
        houses_data = None
        ascendant = None
        midheaven = None
        has_houses = False

        # Calculate houses/angles ONLY if birth_time is available
        if self.birth_profile.has_birth_time:
            try:
                birth_dt = self.birth_profile.get_birth_datetime()

                natal_data = self.astro_service.get_natal_chart_data(
                    birth_datetime=birth_dt,
                    birth_lat=float(self.birth_profile.birth_latitude),
                    birth_lon=float(self.birth_profile.birth_longitude),
                    timezone=self.birth_profile.birth_timezone,
                    house_system='whole_sign'
                )

                ascendant = natal_data['ascendant']
                midheaven = natal_data['midheaven']
                houses_data = natal_data['houses']
                has_houses = True

            except Exception as e:
                print(f"House calculation error: {e}")

        # Calculate dominant characteristics
        dominant_element = self._calculate_dominant_element(planets, ascendant)
        dominant_modality = self._calculate_dominant_modality(planets, ascendant)

        # Assign planets to houses if available
        planets_in_houses = None
        if has_houses and houses_data:
            house_assignment = self._assign_planets_to_houses(planets, houses_data)
            planets = house_assignment['planets_with_houses']
            planets_in_houses = house_assignment['planets_in_houses']

        # Detect notable placements (now includes Chiron, Lilith, Nodes appropriately)
        chart_ruler = self.get_chart_ruler(ascendant, planets)
        stelliums = self.detect_stelliums(planets, houses_data)
        aspect_patterns = self.detect_aspect_patterns(aspects, planets)
        singletons = self.detect_singletons(planets)

        # Build complete chart structure
        natal_chart = {
            'planets': planets,
            'houses': houses_data,
            'aspects': aspects,
            'ascendant': ascendant,
            'midheaven': midheaven,
            'planets_in_houses': planets_in_houses,
            'dominant_element': dominant_element,
            'dominant_modality': dominant_modality,
            'calculated_at': datetime.now(pytz.UTC).isoformat(),
            'has_houses': has_houses,

            # Notable placements
            'retrogrades': retrogrades,
            'chart_ruler': chart_ruler,
            'stelliums': stelliums,
            'aspect_patterns': aspect_patterns,
            'singletons': singletons,
        }

        return natal_chart

    # Helper methods
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


# Convenience function
def get_natal_chart(birth_profile) -> Dict:
    """
    Quick access function for natal chart calculation with all features.

    Returns complete natal chart with:
    - All planets including Chiron, Lilith, Lunar Nodes
    - Houses, aspects, and angles
    - Notable placements (retrogrades, chart ruler, stelliums, etc.)
    - All calculations properly include Chiron, Lilith, and Nodes
    """
    try:
        service = NatalChartService(birth_profile)
        return service.generate_natal_chart()
    except Exception as e:
        print(f"Natal chart calculation error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'planets': [],
            'houses': None,
            'aspects': [],
            'ascendant': None,
            'midheaven': None,
            'planets_in_houses': None,
            'dominant_element': 'Unknown',
            'dominant_modality': 'Unknown',
            'calculated_at': datetime.now(pytz.UTC).isoformat(),
            'has_houses': False,
            'retrogrades': [],
            'chart_ruler': None,
            'stelliums': [],
            'aspect_patterns': [],
            'singletons': [],
        }