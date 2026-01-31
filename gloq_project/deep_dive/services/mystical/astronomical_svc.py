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

    def _calculate_houses_whole_sign(self, ascendant: float, mc: float) -> Dict[str, any]:
        """
        Calculate house cusps using Whole Sign system.

        Whole Sign is the oldest and simplest house system.
        Each house = one complete zodiac sign, starting from the Ascendant's sign.

        Args:
            ascendant: Ascendant longitude in degrees
            mc: Midheaven longitude in degrees

        Returns:
            Dictionary with house cusps (all at 0° of their respective signs)
        """
        # Find which sign the Ascendant is in
        # Round down to the start of that sign (0°, 30°, 60°, etc.)
        asc_sign_start = (int(ascendant // 30) * 30)

        # Build houses - each house starts at 0° of the next sign
        houses = {}
        for house_num in range(1, 13):
            houses[house_num] = (asc_sign_start + (house_num - 1) * 30) % 360

        # Descendant and IC are simply opposite the angles
        descendant = (ascendant + 180) % 360
        ic = (mc + 180) % 360

        return {
            'ascendant': ascendant,
            'midheaven': mc,
            'descendant': descendant,
            'ic': ic,
            'houses': houses
        }

    def _calculate_houses_placidus(self, skyfield_time, latitude: float, longitude: float) -> Dict[str, any]:
        """
        Calculate house cusps using Placidus system.

        Placidus divides the diurnal and nocturnal semi-arcs proportionally.
        This implementation uses iterative methods for intermediate cusps.

        Args:
            skyfield_time: Skyfield Time object
            latitude: Geographic latitude in degrees
            longitude: Geographic longitude in degrees

        Returns:
            Dictionary with ascendant, midheaven, and 12 house cusps
        """
        # Calculate Local Sidereal Time
        lst = self._calculate_sidereal_time(skyfield_time, longitude)

        # Convert to radians for trig calculations
        lat_rad = math.radians(latitude)

        # Calculate obliquity of ecliptic (Earth's axial tilt)
        T = (skyfield_time.tt - 2451545.0) / 36525.0
        epsilon = 23.439291 - 0.0130042 * T  # degrees
        epsilon_rad = math.radians(epsilon)

        # RAMC (Right Ascension of MC) = LST in degrees
        ramc = lst
        ramc_rad = math.radians(ramc)

        # MIDHEAVEN (10th house cusp)
        # Convert RAMC to ecliptic longitude
        mc_numerator = math.sin(ramc_rad)
        mc_denominator = math.cos(ramc_rad) * math.cos(epsilon_rad)
        mc = math.degrees(math.atan2(mc_numerator, mc_denominator)) % 360

        # ASCENDANT (1st house cusp)
        asc_numerator = math.cos(ramc_rad)
        asc_denominator = -math.sin(ramc_rad) * math.cos(epsilon_rad) - math.tan(lat_rad) * math.sin(epsilon_rad)
        ascendant = math.degrees(math.atan2(asc_numerator, asc_denominator)) % 360

        # DESCENDANT (7th house) and IC (4th house) - opposite points
        descendant = (ascendant + 180) % 360
        ic = (mc + 180) % 360

        # Calculate intermediate cusps using Placidus semi-arc division
        houses = {}
        houses[1] = ascendant
        houses[4] = ic
        houses[7] = descendant
        houses[10] = mc

        # For Placidus intermediate cusps, we need to calculate cusps based on
        # trisecting the semi-arcs of diurnal/nocturnal motion

        # Houses 11, 12 (between MC and ASC - nocturnal arc)
        houses[11] = self._placidus_cusp(ramc, latitude, epsilon, 30)  # 1/3 of arc
        houses[12] = self._placidus_cusp(ramc, latitude, epsilon, 60)  # 2/3 of arc

        # Houses 2, 3 (between ASC and IC - diurnal arc below horizon)
        houses[2] = self._placidus_cusp(ramc, latitude, epsilon, 120)  # 1/3 after ASC
        houses[3] = self._placidus_cusp(ramc, latitude, epsilon, 150)  # 2/3 after ASC

        # Houses 5, 6 (between IC and DESC - nocturnal arc below)
        houses[5] = self._placidus_cusp(ramc, latitude, epsilon, 210)  # 1/3 after IC
        houses[6] = self._placidus_cusp(ramc, latitude, epsilon, 240)  # 2/3 after IC

        # Houses 8, 9 (between DESC and MC - diurnal arc)
        houses[8] = self._placidus_cusp(ramc, latitude, epsilon, 300)  # 1/3 after DESC
        houses[9] = self._placidus_cusp(ramc, latitude, epsilon, 330)  # 2/3 after DESC

        return {
            'ascendant': ascendant,
            'midheaven': mc,
            'descendant': descendant,
            'ic': ic,
            'houses': houses
        }

    def _placidus_cusp(self, ramc: float, latitude: float, epsilon: float, house_md: float) -> float:
        """
        Calculate a single Placidus house cusp using iterative method.

        Args:
            ramc: Right Ascension of Midheaven in degrees
            latitude: Geographic latitude in degrees
            epsilon: Obliquity of ecliptic in degrees
            house_md: Meridian distance of house cusp in degrees (0-360)
                     11th=30, 12th=60, 2nd=120, 3rd=150, etc.

        Returns:
            Ecliptic longitude of the house cusp in degrees
        """
        lat_rad = math.radians(latitude)
        eps_rad = math.radians(epsilon)

        # Calculate RA of the house cusp point
        # RA = RAMC + MD (meridian distance)
        ra_cusp = (ramc + house_md) % 360
        ra_cusp_rad = math.radians(ra_cusp)

        # For Placidus, we need to find the ecliptic longitude that corresponds
        # to this RA at the appropriate altitude above/below horizon

        # Determine the "pole elevation" based on which quadrant
        # This accounts for the semi-arc division
        if 0 <= house_md < 90:  # Houses 11, 12 (upper quadrant, nocturnal)
            # MD from MC to ASC
            pole_elevation_factor = (90 - house_md) / 90.0
        elif 90 <= house_md < 180:  # Houses 2, 3 (lower quadrant, diurnal)
            # MD from ASC to IC
            pole_elevation_factor = -(house_md - 90) / 90.0
        elif 180 <= house_md < 270:  # Houses 5, 6 (lower quadrant, nocturnal)
            # MD from IC to DESC
            pole_elevation_factor = -(270 - house_md) / 90.0
        else:  # Houses 8, 9 (upper quadrant, diurnal)
            # MD from DESC to MC
            pole_elevation_factor = (house_md - 270) / 90.0

        # Calculate the declination adjustment for this cusp
        # This is the key to Placidus - each cusp has different altitude
        decl_adjustment = pole_elevation_factor * latitude
        decl_adj_rad = math.radians(decl_adjustment)

        # Use iterative method to find ecliptic longitude
        # Start with a reasonable guess based on RA
        lambda_guess = ra_cusp

        # Newton-Raphson iteration to refine
        for iteration in range(20):  # Usually converges in 3-5 iterations
            lambda_rad = math.radians(lambda_guess)

            # Calculate declination at this ecliptic longitude
            sin_decl = math.sin(lambda_rad) * math.sin(eps_rad)
            decl = math.asin(sin_decl)

            # Calculate RA at this ecliptic longitude
            y = math.sin(lambda_rad) * math.cos(eps_rad)
            x = math.cos(lambda_rad)
            ra_calc = math.degrees(math.atan2(y, x)) % 360

            # For Placidus, we need to account for the altitude adjustment
            # Calculate the adjusted RA based on declination and latitude
            try:
                # Semi-diurnal arc calculation
                tan_lat_tan_decl = math.tan(lat_rad) * math.tan(decl)

                # Check if the point is circumpolar or never rises
                if tan_lat_tan_decl >= 1:
                    # Circumpolar - use simple RA
                    ra_adjusted = ra_calc
                elif tan_lat_tan_decl <= -1:
                    # Never rises - use simple RA
                    ra_adjusted = ra_calc
                else:
                    # Calculate hour angle at the adjusted altitude
                    cos_ha = -tan_lat_tan_decl * pole_elevation_factor

                    # Clamp to valid range
                    cos_ha = max(-1, min(1, cos_ha))

                    ha = math.degrees(math.acos(cos_ha))

                    # Adjusted RA based on which side of meridian
                    if 0 <= house_md < 180:
                        # Eastern side (rising)
                        ra_adjusted = (ra_calc - ha * pole_elevation_factor) % 360
                    else:
                        # Western side (setting)
                        ra_adjusted = (ra_calc + ha * pole_elevation_factor) % 360
            except (ValueError, ZeroDivisionError):
                ra_adjusted = ra_calc

            # Error between target RA and calculated RA
            ra_error = (ra_cusp - ra_adjusted + 180) % 360 - 180

            # Check convergence
            if abs(ra_error) < 0.0001:  # Converged to ~0.36 arcseconds
                break

            # Newton-Raphson step: adjust lambda
            # Derivative approximation
            dlambda = 0.01  # Small increment
            lambda_test = lambda_guess + dlambda
            lambda_test_rad = math.radians(lambda_test)

            y_test = math.sin(lambda_test_rad) * math.cos(eps_rad)
            x_test = math.cos(lambda_test_rad)
            ra_test = math.degrees(math.atan2(y_test, x_test)) % 360

            dra_dlambda = ((ra_test - ra_calc + 180) % 360 - 180) / dlambda

            if abs(dra_dlambda) > 0.0001:
                lambda_guess = (lambda_guess + ra_error / dra_dlambda) % 360
            else:
                # Derivative too small, use small step
                lambda_guess = (lambda_guess + ra_error * 0.5) % 360

        return lambda_guess % 360

    def get_natal_chart_data(
            self,
            birth_datetime: datetime,
            birth_lat: float,
            birth_lon: float,
            timezone: str = 'UTC',
            house_system: str = 'whole_sign'
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
            house_system: House system to use ('whole_sign' or 'placidus')

        Returns:
            {
                'ascendant': {...},
                'midheaven': {...},
                'houses': [...]
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

            # Calculate Local Sidereal Time and basic angles first
            lst = self._calculate_sidereal_time(birth_time, birth_lon)

            # Calculate obliquity
            T = (birth_time.tt - 2451545.0) / 36525.0
            epsilon = 23.439291 - 0.0130042 * T
            epsilon_rad = math.radians(epsilon)

            # Calculate MC and ASC
            ramc = lst
            ramc_rad = math.radians(ramc)
            lat_rad = math.radians(birth_lat)

            # MIDHEAVEN
            mc_numerator = math.sin(ramc_rad)
            mc_denominator = math.cos(ramc_rad) * math.cos(epsilon_rad)
            mc = math.degrees(math.atan2(mc_numerator, mc_denominator)) % 360

            # ASCENDANT
            asc_numerator = math.cos(ramc_rad)
            asc_denominator = -math.sin(ramc_rad) * math.cos(epsilon_rad) - math.tan(lat_rad) * math.sin(epsilon_rad)
            ascendant = math.degrees(math.atan2(asc_numerator, asc_denominator)) % 360

            # Calculate houses based on selected system
            if house_system.lower() == 'whole_sign':
                house_data = self._calculate_houses_whole_sign(ascendant, mc)
            elif house_system.lower() == 'placidus':
                house_data = self._calculate_houses_placidus(birth_time, birth_lat, birth_lon)
            else:
                raise ValueError(f"House system '{house_system}' not supported. Use 'whole_sign' or 'placidus'")

            # Format ascendant
            asc_lon = house_data['ascendant']
            ascendant_formatted = {
                'longitude': asc_lon,
                'sign': self._get_zodiac_sign(asc_lon),
                'degree': self._get_degree_in_sign(asc_lon),
                'symbol': '⇡'
            }

            # Format midheaven
            mc_lon = house_data['midheaven']
            midheaven_formatted = {
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
                'ascendant': ascendant_formatted,
                'midheaven': midheaven_formatted,
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
        cache_key = f"planetary_summary_{target_datetime}_{user_timezone}"

        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        try:
            tz = pytz.timezone(user_timezone)
            if isinstance(target_datetime, date) and not isinstance(target_datetime, datetime):
                target_datetime = datetime.combine(target_datetime, datetime.min.time())

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
            print(f"Historical planetary calculation error for {target_datetime}: {e}")
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