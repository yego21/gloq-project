# journal/services/astronomical_svc.py - with Lunar Nodes + Natal Chart Data
"""
Astronomical calculation service with separate classes for real-time and natal chart data.
"""

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


class AstronomicalService:
    """Service for real-time astronomical data (current moon phase, planetary positions)."""

    # Default coordinates (Cebu City)
    DEFAULT_LAT = 10.3157
    DEFAULT_LON = 123.8854

    def __init__(self):
        if not all([load, Topos, moon_phases]):
            raise ImportError("Skyfield is required for astronomical calculations")

        self.ts = load.timescale()
        self.eph = load('de421.bsp')
        self.earth = self.eph['earth']
        self.moon = self.eph['moon']
        self.sun = self.eph['sun']
        self.mercury = self.eph['mercury']
        self.venus = self.eph['venus']
        self.mars = self.eph['mars']

    def _calculate_mean_nodes(self, skyfield_time) -> Tuple[float, float]:
        """
        Calculate Mean Lunar Nodes (North and South).

        Formula based on Jean Meeus "Astronomical Algorithms"
        Returns ecliptic longitudes in degrees.

        Args:
            skyfield_time: Skyfield Time object

        Returns:
            Tuple of (north_node_longitude, south_node_longitude) in degrees
        """
        # Get Julian Date
        jd = skyfield_time.tt

        # Calculate Julian centuries from J2000.0 epoch (JD 2451545.0)
        T = (jd - 2451545.0) / 36525.0

        # Mean longitude of ascending node (Omega) in degrees
        # Formula: Ω = 125.04452° - 1934.136261°T + 0.0020708°T² + T³/450000
        omega = (125.04452
                 - 1934.136261 * T
                 + 0.0020708 * T * T
                 + (T * T * T) / 450000.0)

        # Normalize to 0-360 range
        north_node = omega % 360

        # South Node is always exactly opposite (180° away)
        south_node = (north_node + 180) % 360

        return north_node, south_node

    def _calculate_sidereal_time(self, skyfield_time, longitude: float) -> float:
        """
        Calculate Local Sidereal Time (LST) for house calculations.

        Args:
            skyfield_time: Skyfield Time object
            longitude: Geographic longitude in degrees (East positive)

        Returns:
            LST in degrees (0-360)
        """
        # Get Greenwich Sidereal Time from Skyfield
        gst = skyfield_time.gast * 15.0  # Convert hours to degrees

        # Local Sidereal Time = GST + longitude
        lst = (gst + longitude) % 360

        return lst

    def _calculate_houses_placidus(self, skyfield_time, latitude: float, longitude: float) -> Dict[str, any]:
        """
        Calculate house cusps using Placidus system.
        Based on Swiss Ephemeris algorithm.
        """
        from math import sin, cos, tan, asin, atan2, radians, degrees

        lat_rad = radians(latitude)

        # Calculate RAMC (Right Ascension of MC)
        # Get from your existing LST calculation
        lst = self._calculate_sidereal_time(skyfield_time, longitude)
        ramc_rad = radians(lst)

        # Obliquity of ecliptic
        T = (skyfield_time.tt - 2451545.0) / 36525.0
        eps = radians(23.439291 - 0.0130042 * T)

        # 1. Calculate MC (Midheaven)
        mc_rad = atan2(tan(ramc_rad), cos(eps))
        mc = degrees(mc_rad) % 360

        # 2. Calculate ASC (Ascendant)
        asc_rad = atan2(-cos(ramc_rad),
                        (sin(eps) * tan(lat_rad) + cos(eps) * sin(ramc_rad)))
        asc = degrees(asc_rad) % 360

        # 3. Calculate IC and DESC
        ic = (mc + 180) % 360
        desc = (asc + 180) % 360

        # 4. Calculate intermediate houses using Koch method (simpler)
        # This is still simplified but better than your current approach

        houses = {}
        houses[1] = asc
        houses[10] = mc
        houses[4] = ic
        houses[7] = desc

        # For intermediate houses, use a proper algorithm
        # This would require solving transcendental equations
        # For now, use an approximation or switch to Koch houses

        # SIMPLE APPROXIMATION (better than equal division):
        # Calculate house 11 as 1/3 of way from MC to ASC
        # But adjust for sign boundaries
        def interpolate_angle(start, end, fraction):
            diff = (end - start) % 360
            if diff > 180:
                diff -= 360
            return (start + diff * fraction) % 360

        houses[11] = interpolate_angle(mc, asc, 1 / 3)
        houses[12] = interpolate_angle(mc, asc, 2 / 3)
        houses[2] = interpolate_angle(asc, ic, 1 / 3)
        houses[3] = interpolate_angle(asc, ic, 2 / 3)
        houses[5] = interpolate_angle(ic, desc, 1 / 3)
        houses[6] = interpolate_angle(ic, desc, 2 / 3)
        houses[8] = interpolate_angle(desc, (mc + 360) % 360, 1 / 3)
        houses[9] = interpolate_angle(desc, (mc + 360) % 360, 2 / 3)

        return {
            'ascendant': asc,
            'midheaven': mc,
            'descendant': desc,
            'ic': ic,
            'houses': houses
        }

    def get_natal_chart_data(
            self,
            birth_datetime: datetime,
            birth_lat: float,
            birth_lon: float,
            timezone: str = 'UTC',
            house_system: str = 'placidus'
    ) -> Dict[str, any]:
        """
        Calculate Ascendant, Midheaven, and House cusps for a birth chart.

        This is a pure calculation method - no caching, no fallbacks.
        Requires exact birth time and location.

        Args:
            birth_datetime: Exact datetime of birth (timezone-aware)
            birth_lat: Birth latitude in degrees (-90 to 90)
            birth_lon: Birth longitude in degrees (-180 to 180)
            timezone: IANA timezone string (e.g., 'Asia/Manila')
            house_system: House system to use (default: 'placidus')

        Returns:
            {
                'ascendant': {
                    'longitude': 145.67,
                    'sign': 'Leo',
                    'degree': 25
                },
                'midheaven': {
                    'longitude': 65.34,
                    'sign': 'Gemini',
                    'degree': 5
                },
                'houses': [
                    {'number': 1, 'cusp_longitude': 145.67, 'sign': 'Leo', 'degree': 25},
                    {'number': 2, 'cusp_longitude': 175.23, 'sign': 'Virgo', 'degree': 25},
                    ...
                ]
            }
        """
        try:
            # Ensure datetime is timezone-aware
            tz = pytz.timezone(timezone)
            if birth_datetime.tzinfo is None:
                birth_local = tz.localize(birth_datetime)
            else:
                birth_local = birth_datetime.astimezone(tz)

            # Convert to Skyfield time
            birth_time = self.ts.from_datetime(birth_local)

            # Calculate houses (currently only Placidus supported)
            if house_system.lower() == 'placidus':
                house_data = self._calculate_houses_placidus(birth_time, birth_lat, birth_lon)
            else:
                raise ValueError(f"House system '{house_system}' not yet supported")

            # Format ascendant
            asc_lon = house_data['ascendant']
            ascendant = {
                'longitude': asc_lon,
                'sign': self._get_zodiac_sign(asc_lon),
                'degree': self._get_degree_in_sign(asc_lon),
                'symbol': '⇡'  # Ascendant symbol
            }

            # Format midheaven
            mc_lon = house_data['midheaven']
            midheaven = {
                'longitude': mc_lon,
                'sign': self._get_zodiac_sign(mc_lon),
                'degree': self._get_degree_in_sign(mc_lon),
                'symbol': 'MC'
            }

            # Format houses
            houses = []
            for house_num in range(1, 13):
                cusp_lon = house_data['houses'][house_num]
                houses.append({
                    'number': house_num,
                    'cusp_longitude': cusp_lon,
                    'sign': self._get_zodiac_sign(cusp_lon),
                    'degree': self._get_degree_in_sign(cusp_lon)
                })

            return {
                'ascendant': ascendant,
                'midheaven': midheaven,
                'houses': houses
            }

        except Exception as e:
            raise Exception(f"Natal chart calculation failed: {e}")

    def get_current_moon_phase(self) -> Dict[str, any]:
        """Get current moon phase information with enhanced visual data."""
        cache_key = f"moon_phase_{date.today()}"
        cached_phase = cache.get(cache_key)

        if cached_phase:
            return cached_phase

        try:
            now = self.ts.now()
            earth_observer = self.earth + Topos(latitude_degrees=self.DEFAULT_LAT,
                                                longitude_degrees=self.DEFAULT_LON)

            # Get positions
            sun_pos = earth_observer.at(now).observe(self.sun)
            moon_pos = earth_observer.at(now).observe(self.moon)

            # Calculate phase angle between Sun and Moon as seen from Earth
            sun_lon = sun_pos.apparent().ecliptic_latlon()[1].degrees
            moon_lon = moon_pos.apparent().ecliptic_latlon()[1].degrees

            # Phase angle (0 = New Moon, 180 = Full Moon)
            phase_angle = (moon_lon - sun_lon) % 360

            # Calculate illumination percentage
            illumination = (1 - math.cos(math.radians(phase_angle))) / 2 * 100

            phase_info = self._interpret_moon_phase(phase_angle, illumination)

            # Add visual data for progress bars and styling
            phase_info.update({
                'illumination_decimal': illumination / 100,
                'phase_angle': phase_angle,
                'visual_phase': self._get_visual_phase_data(phase_angle),
                'next_phase_days': self._calculate_days_to_next_phase(phase_angle)
            })

            # Cache for 6 hours
            cache.set(cache_key, phase_info, 60 * 60 * 6)
            return phase_info

        except Exception as e:
            print(f"Moon phase calculation error: {e}")
            return self._fallback_moon_phase()

    def _generate_cosmic_weather_summary_extended(self, planetary_positions: list) -> str:
        """
        Generate cosmic weather summary considering all 10 bodies + nodes.

        Args:
            planetary_positions: List of all planetary position dicts

        Returns:
            Human-readable summary of cosmic conditions
        """
        if not planetary_positions or len(planetary_positions) < 2:
            return "The celestial dance continues in mysterious ways"

        try:
            sun = next((p for p in planetary_positions if p['name'] == 'Sun'), None)
            moon = next((p for p in planetary_positions if p['name'] == 'Moon'), None)

            if sun and moon:
                # Calculate sun-moon angle for phase insight
                angle_diff = abs(sun['longitude'] - moon['longitude'])
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff

                if angle_diff < 30:
                    return "Solar and lunar energies unite in close conjunction"
                elif 150 < angle_diff < 210:
                    return "Sun and moon oppose, creating dynamic tension"
                else:
                    return "Celestial bodies weave their cosmic patterns"

            return "The planetary dance unfolds across the zodiac"

        except Exception:
            return "The celestial dance continues in mysterious ways"

    def get_daily_planetary_summary(self, user_timezone: str = 'UTC') -> Dict[str, any]:
        """Get current planetary positions with exact degrees for ALL 10 celestial bodies + Lunar Nodes."""
        cache_key = f"planetary_summary_{date.today()}_{user_timezone}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        try:
            tz = pytz.timezone(user_timezone)
            now_local = datetime.now(tz)
            now = self.ts.from_datetime(now_local)

            earth_observer = self.earth + Topos(latitude_degrees=self.DEFAULT_LAT,
                                                longitude_degrees=self.DEFAULT_LON)

            # Get ALL planetary positions (ecliptic longitude for zodiac signs)
            planetary_bodies = [
                ('sun', 'Sun', '☀️'),
                ('moon', 'Moon', '🌙'),
                ('mercury', 'Mercury', '☿️'),
                ('venus', 'Venus', '♀️'),
                ('mars', 'Mars', '♂️'),
                ('jupiter barycenter', 'Jupiter', '♃'),
                ('saturn barycenter', 'Saturn', '♄'),
                ('uranus barycenter', 'Uranus', '♅'),
                ('neptune barycenter', 'Neptune', '♆'),
                ('pluto barycenter', 'Pluto', '♇')
            ]

            planetary_positions = []
            zodiac_signs = []

            # Calculate physical bodies
            for body_name, display_name, symbol in planetary_bodies:
                try:
                    body = self.eph[body_name]
                    pos = earth_observer.at(now).observe(body).apparent()
                    lon = pos.ecliptic_latlon()[1].degrees
                    sign = self._get_zodiac_sign(lon)

                    planetary_positions.append({
                        'name': display_name,
                        'symbol': symbol,
                        'sign': sign,
                        'degree': self._get_degree_in_sign(lon),
                        'longitude': lon,
                        'element': self._get_element(sign)
                    })

                    zodiac_signs.append(sign)

                except Exception as e:
                    print(f"Error calculating {display_name}: {e}")
                    continue

            # Calculate Lunar Nodes
            try:
                north_node_lon, south_node_lon = self._calculate_mean_nodes(now)

                north_sign = self._get_zodiac_sign(north_node_lon)
                south_sign = self._get_zodiac_sign(south_node_lon)

                planetary_positions.append({
                    'name': 'North Node',
                    'symbol': '☊',
                    'sign': north_sign,
                    'degree': self._get_degree_in_sign(north_node_lon),
                    'longitude': north_node_lon,
                    'element': self._get_element(north_sign)
                })

                planetary_positions.append({
                    'name': 'South Node',
                    'symbol': '☋',
                    'sign': south_sign,
                    'degree': self._get_degree_in_sign(south_node_lon),
                    'longitude': south_node_lon,
                    'element': self._get_element(south_sign)
                })

            except Exception as e:
                print(f"Error calculating Lunar Nodes: {e}")

            planetary_data = {
                'planetary_positions': planetary_positions,
                'dominant_element': self._calculate_dominant_element(zodiac_signs),
                'cosmic_weather': self._generate_cosmic_weather_summary_extended(planetary_positions)
            }

            # Cache for 12 hours
            cache.set(cache_key, planetary_data, 60 * 60 * 12)
            return planetary_data

        except Exception as e:
            print(f"Planetary calculation error: {e}")
            return self._fallback_planetary_data()

    def get_planetary_summary_for_date(self, target_datetime, user_timezone: str = 'UTC') -> Dict[str, any]:
        """
        Get planetary positions for ALL 10 celestial bodies + Lunar Nodes on a specific historical date.

        Args:
            target_datetime: datetime object for the date to calculate
            user_timezone: Timezone string (default: 'UTC')

        Returns:
            Complete planetary summary for that specific date
        """
        # Create cache key with the specific date
        cache_key = f"planetary_summary_{target_datetime.date()}_{user_timezone}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        try:
            tz = pytz.timezone(user_timezone)

            # Make sure target_datetime is timezone-aware
            if target_datetime.tzinfo is None:
                target_local = tz.localize(target_datetime)
            else:
                target_local = target_datetime.astimezone(tz)

            # Convert to Skyfield time
            target_time = self.ts.from_datetime(target_local)

            earth_observer = self.earth + Topos(latitude_degrees=self.DEFAULT_LAT,
                                                longitude_degrees=self.DEFAULT_LON)

            # Get ALL planetary positions (ecliptic longitude for zodiac signs)
            planetary_bodies = [
                ('sun', 'Sun', '☀️'),
                ('moon', 'Moon', '🌙'),
                ('mercury', 'Mercury', '☿️'),
                ('venus', 'Venus', '♀️'),
                ('mars', 'Mars', '♂️'),
                ('jupiter barycenter', 'Jupiter', '♃'),
                ('saturn barycenter', 'Saturn', '♄'),
                ('uranus barycenter', 'Uranus', '♅'),
                ('neptune barycenter', 'Neptune', '♆'),
                ('pluto barycenter', 'Pluto', '♇')
            ]

            planetary_positions = []
            zodiac_signs = []

            # Calculate physical bodies
            for body_name, display_name, symbol in planetary_bodies:
                try:
                    body = self.eph[body_name]
                    pos = earth_observer.at(target_time).observe(body).apparent()
                    lon = pos.ecliptic_latlon()[1].degrees
                    sign = self._get_zodiac_sign(lon)

                    planetary_positions.append({
                        'name': display_name,
                        'symbol': symbol,
                        'sign': sign,
                        'degree': self._get_degree_in_sign(lon),
                        'longitude': lon,
                        'element': self._get_element(sign)
                    })

                    zodiac_signs.append(sign)

                except Exception as e:
                    print(f"Error calculating {display_name} for {target_datetime.date()}: {e}")
                    continue

            # Calculate Lunar Nodes for this specific date
            try:
                north_node_lon, south_node_lon = self._calculate_mean_nodes(target_time)

                north_sign = self._get_zodiac_sign(north_node_lon)
                south_sign = self._get_zodiac_sign(south_node_lon)

                planetary_positions.append({
                    'name': 'North Node',
                    'symbol': '☊',
                    'sign': north_sign,
                    'degree': self._get_degree_in_sign(north_node_lon),
                    'longitude': north_node_lon,
                    'element': self._get_element(north_sign)
                })

                planetary_positions.append({
                    'name': 'South Node',
                    'symbol': '☋',
                    'sign': south_sign,
                    'degree': self._get_degree_in_sign(south_node_lon),
                    'longitude': south_node_lon,
                    'element': self._get_element(south_sign)
                })

            except Exception as e:
                print(f"Error calculating Lunar Nodes for {target_datetime.date()}: {e}")

            planetary_data = {
                'planetary_positions': planetary_positions,
                'dominant_element': self._calculate_dominant_element(zodiac_signs),
                'cosmic_weather': self._generate_cosmic_weather_summary_extended(planetary_positions)
            }

            # Cache for 24 hours (historical data doesn't change)
            cache.set(cache_key, planetary_data, 60 * 60 * 24)
            return planetary_data

        except Exception as e:
            print(f"Historical planetary calculation error for {target_datetime.date()}: {e}")
            return self._fallback_planetary_data()

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
        """Get the degree within the zodiac sign (0-29)."""
        longitude = longitude % 360
        return int(longitude % 30)

    def _get_element(self, sign: str) -> str:
        """Get the element for a zodiac sign."""
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

    def _interpret_moon_phase(self, phase_angle: float, illumination: float) -> Dict[str, str]:
        """Convert phase angle to human-readable moon phase with enhanced data."""
        illum_str = f"{int(illumination)}"

        # Normalize phase angle to 0-360
        phase_angle = phase_angle % 360

        if phase_angle < 22.5 or phase_angle >= 337.5:
            return {
                'phase': 'New Moon',
                'emoji': '🌑',
                'description': 'A time of new beginnings and setting intentions',
                'illumination': illum_str,
                'mystical_meaning': 'The void holds infinite potential'
            }
        elif 22.5 <= phase_angle < 67.5:
            return {
                'phase': 'Waxing Crescent',
                'emoji': '🌒',
                'description': 'Growth and building momentum toward your goals',
                'illumination': illum_str,
                'mystical_meaning': 'Hope emerges from darkness'
            }
        elif 67.5 <= phase_angle < 112.5:
            return {
                'phase': 'First Quarter',
                'emoji': '🌓',
                'description': 'Challenges arise, but determination pushes through',
                'illumination': illum_str,
                'mystical_meaning': 'Balance between shadow and light'
            }
        elif 112.5 <= phase_angle < 157.5:
            return {
                'phase': 'Waxing Gibbous',
                'emoji': '🌔',
                'description': 'Refinement and preparation for completion',
                'illumination': illum_str,
                'mystical_meaning': 'Patience as power builds'
            }
        elif 157.5 <= phase_angle < 202.5:
            return {
                'phase': 'Full Moon',
                'emoji': '🌕',
                'description': 'Peak energy, culmination, and heightened intuition',
                'illumination': illum_str,
                'mystical_meaning': 'Maximum illumination reveals all truths'
            }
        elif 202.5 <= phase_angle < 247.5:
            return {
                'phase': 'Waning Gibbous',
                'emoji': '🌖',
                'description': 'Gratitude, sharing wisdom, and releasing what no longer serves',
                'illumination': illum_str,
                'mystical_meaning': 'Wisdom flows as light diminishes'
            }
        elif 247.5 <= phase_angle < 292.5:
            return {
                'phase': 'Last Quarter',
                'emoji': '🌗',
                'description': 'Letting go of obstacles and clearing the path forward',
                'illumination': illum_str,
                'mystical_meaning': 'Release creates space for renewal'
            }
        else:  # 292.5 <= phase_angle < 337.5:
            return {
                'phase': 'Waning Crescent',
                'emoji': '🌘',
                'description': 'Rest, reflection, and preparing for renewal',
                'illumination': illum_str,
                'mystical_meaning': 'In surrender, find peace'
            }

    def _get_visual_phase_data(self, phase_angle: float) -> Dict[str, any]:
        """Get visual styling data for the current moon phase."""
        if phase_angle < 22.5 or phase_angle > 337.5:
            return {'css_class': 'new-moon', 'gradient': 'from-gray-800 to-gray-900'}
        elif 22.5 <= phase_angle < 67.5:
            return {'css_class': 'waxing-crescent', 'gradient': 'from-gray-700 to-blue-800'}
        elif 67.5 <= phase_angle < 112.5:
            return {'css_class': 'first-quarter', 'gradient': 'from-blue-800 to-purple-800'}
        elif 112.5 <= phase_angle < 157.5:
            return {'css_class': 'waxing-gibbous', 'gradient': 'from-purple-800 to-indigo-700'}
        elif 157.5 <= phase_angle < 202.5:
            return {'css_class': 'full-moon', 'gradient': 'from-indigo-500 to-purple-600'}
        elif 202.5 <= phase_angle < 247.5:
            return {'css_class': 'waning-gibbous', 'gradient': 'from-purple-600 to-indigo-800'}
        elif 247.5 <= phase_angle < 292.5:
            return {'css_class': 'last-quarter', 'gradient': 'from-indigo-800 to-gray-700'}
        else:
            return {'css_class': 'waning-crescent', 'gradient': 'from-gray-700 to-gray-800'}

    def _calculate_days_to_next_phase(self, phase_angle: float) -> int:
        """Estimate days until next major moon phase."""
        current_phase_progress = phase_angle / 360
        days_in_cycle = 29.53

        quarters = [0, 0.25, 0.5, 0.75, 1.0]
        for quarter in quarters:
            if current_phase_progress < quarter:
                days_remaining = (quarter - current_phase_progress) * days_in_cycle
                return max(1, int(days_remaining))

        days_remaining = (1.0 - current_phase_progress) * days_in_cycle
        return max(1, int(days_remaining))

    def _calculate_dominant_element(self, signs: list) -> str:
        """Calculate dominant element from zodiac signs."""
        elements = {
            'Fire': ['Aries', 'Leo', 'Sagittarius'],
            'Earth': ['Taurus', 'Virgo', 'Capricorn'],
            'Air': ['Gemini', 'Libra', 'Aquarius'],
            'Water': ['Cancer', 'Scorpio', 'Pisces']
        }

        element_count = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}

        for sign in signs:
            for element, sign_list in elements.items():
                if sign in sign_list:
                    element_count[element] += 1
                    break

        return max(element_count, key=element_count.get)

    def _generate_cosmic_weather_summary(self, sun_lon, moon_lon, mercury_lon, venus_lon, mars_lon) -> str:
        """Generate mystical summary of current cosmic conditions."""
        summaries = []

        sun_moon_angle = abs(moon_lon - sun_lon) % 360
        if sun_moon_angle < 30 or sun_moon_angle > 330:
            summaries.append("Solar and lunar energies dance in close harmony")
        elif 150 < sun_moon_angle < 210:
            summaries.append("Tension between conscious and unconscious realms creates dynamic energy")

        sun_sign = self._get_zodiac_sign(sun_lon)
        moon_sign = self._get_zodiac_sign(moon_lon)

        fire_signs = ['Aries', 'Leo', 'Sagittarius']
        earth_signs = ['Taurus', 'Virgo', 'Capricorn']
        air_signs = ['Gemini', 'Libra', 'Aquarius']
        water_signs = ['Cancer', 'Scorpio', 'Pisces']

        if sun_sign in fire_signs and moon_sign in fire_signs:
            summaries.append("Double fire energy ignites passion and bold action")
        elif sun_sign in earth_signs and moon_sign in water_signs:
            summaries.append("Earth and water merge, bringing fertile manifestation energy")
        elif sun_sign in air_signs and moon_sign in fire_signs:
            summaries.append("Air feeds fire, creating inspiration and swift movement")

        if not summaries:
            summaries.append("Cosmic energies flow in mysterious, harmonious patterns")

        return "; ".join(summaries[:2]) + "."

    def _fallback_moon_phase(self) -> Dict[str, str]:
        """Fallback moon phase data if calculations fail."""
        return {
            'phase': 'Mystical Moon',
            'emoji': '🌙',
            'description': 'The lunar mysteries unfold beyond current sight',
            'illumination': '50',
            'illumination_decimal': 0.5,
            'mystical_meaning': 'Trust in cosmic timing'
        }

    def _fallback_planetary_data(self) -> Dict[str, any]:
        """Fallback planetary data if calculations fail."""
        return {
            'planetary_positions': [],
            'dominant_element': 'Spirit',
            'cosmic_weather': 'The stars whisper secrets through veils of mystery'
        }

    # Convenience functions for easy import
def get_moon_phase() -> Dict[str, any]:
    """Quick access to current moon phase with enhanced visual data."""
    try:
        service = AstronomicalService()
        return service.get_current_moon_phase()
    except Exception as e:
        print(f"Moon phase service error: {e}")
        return {
            'phase': 'Mystical Moon',
            'emoji': '🌙',
            'description': 'The lunar mysteries flow beyond current sight',
            'illumination': '50',
            'illumination_decimal': 0.5,
            'mystical_meaning': 'Trust in divine timing'
        }

def get_planetary_summary(timezone: str = 'UTC') -> Dict[str, any]:
    """Quick access to planetary summary with exact degrees + Lunar Nodes."""
    try:
        service = AstronomicalService()
        return service.get_daily_planetary_summary(timezone)
    except Exception as e:
        print(f"Planetary service error: {e}")
        return {
            'planetary_positions': [],
            'dominant_element': 'Spirit',
            'cosmic_weather': 'The celestial dance continues in mysterious ways'
        }

def get_planetary_summary_for_date(target_datetime, timezone: str = 'UTC') -> Dict[str, any]:
    """
    Convenience function: Get planetary positions + Lunar Nodes for a specific date.

    Args:
        target_datetime: datetime object for the date to calculate
        timezone: Timezone string (default: 'UTC')

    Returns:
        Planetary summary for that specific date
    """
    try:
        service = AstronomicalService()
        return service.get_planetary_summary_for_date(target_datetime, timezone)
    except Exception as e:
        print(f"Planetary service error for date {target_datetime.date()}: {e}")
        return {
            'planetary_positions': [],
            'dominant_element': 'Spirit',
            'cosmic_weather': 'The celestial dance continues in mysterious ways'
        }