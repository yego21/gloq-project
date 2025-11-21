# deep_dive/services/ai_chart_reading_svc.py
"""
AI-powered astrological reading service.
Calculates transits and generates personalized interpretations.
"""

from datetime import datetime, date
from typing import Dict, List, Optional
import json
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


class AIReadingService:
    """
    Generates AI-powered astrological readings using Groq.
    """

    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.astro_service = AstronomicalService()

    def generate_daily_reading(
            self,
            natal_chart: Dict,
            reading_type: str = 'daily_overview'
    ) -> Dict:
        """
        Generate an AI reading based on natal chart and current transits.

        Args:
            natal_chart: User's natal chart data
            reading_type: Type of reading (daily_overview, transit_focus, element_focus)

        Returns:
            Dict with reading content and metadata
        """
        # Get current planetary positions
        current_positions = self.astro_service.get_daily_planetary_summary()
        current_moon = self.astro_service.get_current_moon_phase()

        # Calculate transits
        transit_calc = TransitCalculator(natal_chart)
        transits = transit_calc.calculate_transits(
            current_positions['planetary_positions']
        )

        # Build prompt based on reading type
        if reading_type == 'daily_overview':
            prompt = self._build_daily_overview_prompt(
                natal_chart, transits, current_positions, current_moon
            )
            max_tokens = 400
        elif reading_type == 'transit_focus':
            prompt = self._build_transit_focus_prompt(
                natal_chart, transits
            )
            max_tokens = 500
        elif reading_type == 'element_wisdom':
            prompt = self._build_element_wisdom_prompt(
                natal_chart, current_positions
            )
            max_tokens = 300
        else:
            raise ValueError(f"Unknown reading type: {reading_type}")

        # Call Groq API
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skilled astrologer providing insightful, empowering interpretations. Be mystical yet practical, poetic yet clear. Focus on growth and possibility."
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

            return {
                'reading_type': reading_type,
                'reading_text': reading_text,
                'generated_at': datetime.now().isoformat(),
                'transits_analyzed': len(transits),
                'top_transits': transits[:3],  # Store top 3 for reference
                'moon_phase': current_moon['phase'],
                'cosmic_weather': current_positions.get('cosmic_weather', ''),
            }

        except Exception as e:
            print(f"AI reading generation error: {e}")
            return self._fallback_reading(reading_type)

    def _build_daily_overview_prompt(
            self,
            natal_chart: Dict,
            transits: List[Dict],
            current_positions: Dict,
            moon_phase: Dict
    ) -> str:
        """Build prompt for daily overview reading."""

        # Extract key natal info
        natal_sun = next(p for p in natal_chart['planets'] if p['name'] == 'Sun')
        natal_moon = next(p for p in natal_chart['planets'] if p['name'] == 'Moon')

        # Get top 3 transits
        top_transits = transits[:3] if transits else []

        prompt = f"""Create a brief daily astrological reading for someone with:

NATAL CHART:
- Sun in {natal_sun['sign']} (core identity, life purpose)
- Moon in {natal_moon['sign']} (emotional nature, inner world)
- Dominant Element: {natal_chart['dominant_element']}
- Dominant Modality: {natal_chart['dominant_modality']}

TODAY'S TRANSITS (Current planets activating natal chart):
"""

        if top_transits:
            for transit in top_transits:
                prompt += f"\n- Transit {transit['transit_planet']} in {transit['transit_sign']} {transit['aspect_type']} Natal {transit['natal_planet']} in {transit['natal_sign']} (orb: {transit['orb']}°)"
        else:
            prompt += "\n- No major transits today - subtle energies flow"

        prompt += f"""

CURRENT MOON: {moon_phase['phase']} - {moon_phase['description']}

Write a 2-3 paragraph reading that:
1. Acknowledges their core nature (natal Sun/Moon)
2. Interprets the most significant transit (if any)
3. Offers practical guidance for today
4. Ends with an empowering insight

Keep it mystical, warm, and actionable. No fluff."""

        return prompt

    def _build_transit_focus_prompt(
            self,
            natal_chart: Dict,
            transits: List[Dict]
    ) -> str:
        """Build prompt focusing on specific transits."""

        if not transits:
            return "No major transits today. Focus on your natal strengths and inner wisdom."

        top_transit = transits[0]

        prompt = f"""Interpret this astrological transit in depth:

TRANSIT: {top_transit['transit_planet']} in {top_transit['transit_sign']} 
ASPECT: {top_transit['aspect_type']} ({top_transit['quality']})
TO: Natal {top_transit['natal_planet']} in {top_transit['natal_sign']}
ORB: {top_transit['orb']}° (Strength: {top_transit['strength']})

NATAL CHART CONTEXT:
- Dominant Element: {natal_chart['dominant_element']}
- Dominant Modality: {natal_chart['dominant_modality']}

Provide a detailed interpretation covering:
1. What this transit means psychologically and practically
2. How it interacts with their natal chart themes
3. Specific areas of life being activated
4. Timing and duration insights
5. Actionable advice for working with this energy

Be thorough yet accessible. Use vivid, evocative language."""

        return prompt

    def _build_element_wisdom_prompt(
            self,
            natal_chart: Dict,
            current_positions: Dict
    ) -> str:
        """Build prompt focusing on elemental energies."""

        natal_element = natal_chart['dominant_element']
        current_element = current_positions.get('dominant_element', 'Unknown')

        prompt = f"""Create an elemental wisdom reading:

NATAL DOMINANT ELEMENT: {natal_element}
TODAY'S DOMINANT ELEMENT: {current_element}

Write a brief reading about:
1. How their natal {natal_element} nature expresses today
2. The interaction between natal and current elemental energies
3. Elemental guidance for balance and flow

Keep it poetic, insightful, and grounded in elemental wisdom (Fire=action/passion, Earth=manifestation/grounding, Air=thought/communication, Water=emotion/intuition)."""

        return prompt

    def _fallback_reading(self, reading_type: str) -> Dict:
        """Fallback reading if AI generation fails."""

        fallback_texts = {
            'daily_overview': "The cosmos whispers gently today. Trust your inner wisdom and the rhythms of your natal chart. Your path unfolds in perfect timing.",
            'transit_focus': "Current celestial movements invite reflection on your journey. Look within for guidance as the stars align in mysterious ways.",
            'element_wisdom': "The elements dance in eternal balance. Honor your dominant nature while remaining open to cosmic flow."
        }

        return {
            'reading_type': reading_type,
            'reading_text': fallback_texts.get(reading_type,
                                               "The stars hold their secrets today. Trust your inner knowing."),
            'generated_at': datetime.now().isoformat(),
            'transits_analyzed': 0,
            'top_transits': [],
            'is_fallback': True
        }


# Convenience function
def generate_reading(natal_chart: Dict, reading_type: str = 'daily_overview') -> Dict:
    """
    Quick access to AI reading generation.

    Usage:
        from deep_dive.services.ai_reading_service import generate_reading
        reading = generate_reading(user_natal_chart, 'daily_overview')
    """
    service = AIReadingService()
    return service.generate_daily_reading(natal_chart, reading_type)