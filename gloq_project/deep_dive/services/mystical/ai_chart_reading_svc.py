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
            reading_type: str = 'daily_overview',
            user=None  # Add user parameter
    ) -> Dict:
        """
        Generate an AI reading based on natal chart and current transits.

        Args:
            natal_chart: User's natal chart data
            reading_type: Type of reading (daily_overview, transit_focus, element_focus)
            user: User object to fetch journal entries

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

            # Generate transit summaries for display
            transit_summaries = []
            for transit in transits[:3]:  # Top 3 transits
                interpretation = self._get_transit_interpretation_context(transit)
                summary = {
                    'transit_planet': transit['transit_planet'],
                    'transit_sign': transit['transit_sign'],
                    'aspect_type': transit['aspect_type'],
                    'natal_planet': transit['natal_planet'],
                    'natal_sign': transit['natal_sign'],
                    'orb': transit['orb'],
                    'quality': transit['quality'],
                    'meaning': interpretation['meaning'],
                    'life_areas': interpretation['life_areas'],
                    'themes': interpretation['themes'],
                    'tone': interpretation['tone']
                }
                transit_summaries.append(summary)

            return {
                'reading_type': reading_type,
                'reading_text': reading_text,
                'generated_at': datetime.now().isoformat(),
                'transits_analyzed': len(transits),
                'top_transits': transits[:3],
                'transit_summaries': transit_summaries,  # New: formatted summaries with meanings
                'moon_phase': current_moon['phase'],
                'cosmic_weather': current_positions.get('cosmic_weather', ''),
                'journal_included': journal_context is not None,
            }

        except Exception as e:
            print(f"AI reading generation error: {e}")
            return self._fallback_reading(reading_type)

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
            from journal.models import JournalEntry  # Adjust import path as needed

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
        Returns a dict with general meaning, life areas affected, and practical themes.
        """
        transit_planet = transit['transit_planet']
        natal_planet = transit['natal_planet']
        aspect = transit['aspect_type']
        quality = transit['quality']

        # Transit planet energies
        planet_meanings = {
            'Sun': 'identity, vitality, purpose, ego',
            'Moon': 'emotions, instincts, comfort, past patterns',
            'Mercury': 'communication, thinking, learning, daily tasks',
            'Venus': 'relationships, values, pleasure, aesthetics',
            'Mars': 'action, desire, conflict, assertion',
            'Jupiter': 'expansion, optimism, beliefs, opportunity',
            'Saturn': 'structure, limits, responsibility, reality checks',
            'Uranus': 'change, rebellion, innovation, disruption',
            'Neptune': 'dreams, illusions, spirituality, dissolution',
            'Pluto': 'transformation, power, depth, letting go'
        }

        # Life areas and themes based on natal planet
        natal_planet_areas = {
            'Sun': 'core identity, life direction, self-expression, vitality',
            'Moon': 'emotional security, home life, family, inner world',
            'Mercury': 'communication style, learning, daily routines, siblings',
            'Venus': 'relationships, self-worth, money, pleasure, creativity',
            'Mars': 'drive, sexuality, conflict style, physical energy',
            'Jupiter': 'beliefs, growth, opportunities, philosophy, travel',
            'Saturn': 'responsibilities, career, discipline, long-term goals',
            'Uranus': 'independence, originality, sudden changes, technology',
            'Neptune': 'spirituality, dreams, creativity, boundaries',
            'Pluto': 'power dynamics, transformation, deep psychology, endings'
        }

        transit_energy = planet_meanings.get(transit_planet, transit_planet)
        natal_area = natal_planet_areas.get(natal_planet, natal_planet)

        # Build base interpretation
        base_meaning = f"{transit_planet} ({transit_energy}) activating your natal {natal_planet} ({natal_area})"

        # Get specific interpretations with life areas and practical themes
        key = f"{transit_planet}_{aspect}_{natal_planet}"

        # Comprehensive transit dictionary with life areas and themes
        specific_transits = {
            # Mars transits
            'Mars_Opposition_Saturn': {
                'meaning': 'Tension between drive and discipline',
                'life_areas': 'Career, authority figures, long-term goals',
                'themes': 'May feel blocked or frustrated; patience required with obstacles',
                'tone': 'challenging'
            },
            'Mars_Square_Saturn': {
                'meaning': 'Friction between action and restraint',
                'life_areas': 'Work responsibilities, physical energy, ambitions',
                'themes': 'Effort feels harder; test of perseverance and strategic patience',
                'tone': 'challenging'
            },
            'Mars_Conjunction_Venus': {
                'meaning': 'Passion meets desire',
                'life_areas': 'Relationships, creativity, money, pleasure',
                'themes': 'Magnetic energy; favorable for romance and creative projects',
                'tone': 'harmonious'
            },
            'Mars_Trine_Jupiter': {
                'meaning': 'Confident action meets opportunity',
                'life_areas': 'Growth, adventure, risk-taking, optimism',
                'themes': 'Favorable for bold moves; energy and luck align',
                'tone': 'harmonious'
            },

            # Sun transits
            'Sun_Trine_Moon': {
                'meaning': 'Inner harmony between identity and emotions',
                'life_areas': 'Self-expression, emotional security, relationships',
                'themes': 'Auspicious for personal matters; alignment of head and heart',
                'tone': 'harmonious'
            },
            'Sun_Conjunction_Venus': {
                'meaning': 'Self-expression feels attractive and valued',
                'life_areas': 'Relationships, self-worth, social connections, creativity',
                'themes': 'Favorable for love and social situations; charm and magnetism',
                'tone': 'harmonious'
            },
            'Sun_Square_Saturn': {
                'meaning': 'Identity confronts limitations',
                'life_areas': 'Career, self-esteem, authority, responsibilities',
                'themes': 'Reality check moment; patience with delays or criticism',
                'tone': 'challenging'
            },
            'Sun_Opposition_Pluto': {
                'meaning': 'Ego confronts power dynamics',
                'life_areas': 'Control issues, transformation, deep psychology',
                'themes': 'Power struggles possible; need to release what no longer serves',
                'tone': 'challenging'
            },

            # Mercury transits
            'Mercury_Square_Neptune': {
                'meaning': 'Logic meets fog',
                'life_areas': 'Communication, decision-making, contracts, learning',
                'themes': 'Confusion or miscommunication likely; trust intuition over logic',
                'tone': 'challenging'
            },
            'Mercury_Trine_Jupiter': {
                'meaning': 'Mind expands with optimism',
                'life_areas': 'Learning, communication, travel, teaching',
                'themes': 'Favorable for learning and big-picture thinking; mental clarity',
                'tone': 'harmonious'
            },
            'Mercury_Conjunction_Mars': {
                'meaning': 'Sharp words and quick decisions',
                'life_areas': 'Communication, debates, mental energy, assertions',
                'themes': 'Direct communication; watch for arguments or hasty choices',
                'tone': 'neutral'
            },

            # Venus transits
            'Venus_Opposition_Mars': {
                'meaning': 'Desire meets assertion',
                'life_areas': 'Relationships, sexual dynamics, values vs. actions',
                'themes': 'Tension between what you want and what you do; relationship sparks',
                'tone': 'challenging'
            },
            'Venus_Trine_Saturn': {
                'meaning': 'Love meets commitment',
                'life_areas': 'Relationships, finances, long-term values, stability',
                'themes': 'Favorable for serious commitments and financial planning',
                'tone': 'harmonious'
            },
            'Venus_Square_Pluto': {
                'meaning': 'Love confronts intensity',
                'life_areas': 'Relationships, money, obsession, transformation',
                'themes': 'Deep feelings surface; power dynamics in relationships',
                'tone': 'challenging'
            },

            # Jupiter transits
            'Jupiter_Trine_Sun': {
                'meaning': 'Expansion meets identity',
                'life_areas': 'Personal growth, opportunities, confidence, purpose',
                'themes': 'Auspicious for career and personal development; doors open',
                'tone': 'harmonious'
            },
            'Jupiter_Conjunction_Venus': {
                'meaning': 'Abundance meets pleasure',
                'life_areas': 'Relationships, money, joy, social life',
                'themes': 'Favorable for love and finances; generosity and enjoyment',
                'tone': 'harmonious'
            },
            'Jupiter_Square_Saturn': {
                'meaning': 'Growth confronts limits',
                'life_areas': 'Career, ambitions, responsibilities vs. opportunities',
                'themes': 'Balancing expansion with reality; patience with timing',
                'tone': 'challenging'
            },

            # Saturn transits
            'Saturn_Square_Moon': {
                'meaning': 'Responsibility weighs on feelings',
                'life_areas': 'Emotional security, home, family, inner peace',
                'themes': 'Emotional heaviness or isolation; need for self-care structure',
                'tone': 'challenging'
            },
            'Saturn_Trine_Venus': {
                'meaning': 'Structure supports love',
                'life_areas': 'Relationships, finances, commitments, values',
                'themes': 'Favorable for serious commitments and financial stability',
                'tone': 'harmonious'
            },
            'Saturn_Conjunction_Sun': {
                'meaning': 'Reality tests identity',
                'life_areas': 'Life direction, career, self-definition, maturity',
                'themes': 'Important life evaluation; time to build solid foundations',
                'tone': 'neutral'
            },

            # Uranus transits
            'Uranus_Opposition_Sun': {
                'meaning': 'Change disrupts identity',
                'life_areas': 'Life direction, freedom, independence, sudden shifts',
                'themes': 'Restlessness; urge to break free from routine or constraints',
                'tone': 'challenging'
            },
            'Uranus_Trine_Venus': {
                'meaning': 'Innovation meets pleasure',
                'life_areas': 'Relationships, creativity, finances, excitement',
                'themes': 'Favorable for new connections and creative breakthroughs',
                'tone': 'harmonious'
            },

            # Neptune transits
            'Neptune_Square_Mercury': {
                'meaning': 'Illusion clouds logic',
                'life_areas': 'Communication, clarity, boundaries, perception',
                'themes': 'Confusion or deception possible; heightened intuition but fuzzy facts',
                'tone': 'challenging'
            },
            'Neptune_Trine_Moon': {
                'meaning': 'Dreams support emotions',
                'life_areas': 'Spirituality, creativity, compassion, inner world',
                'themes': 'Favorable for artistic work and spiritual connection',
                'tone': 'harmonious'
            },

            # Pluto transits
            'Pluto_Square_Venus': {
                'meaning': 'Transformation through relationships',
                'life_areas': 'Love, values, money, power dynamics',
                'themes': 'Intense relationship experiences; deep change in what you value',
                'tone': 'challenging'
            },
            'Pluto_Trine_Sun': {
                'meaning': 'Personal empowerment',
                'life_areas': 'Identity, power, purpose, transformation',
                'themes': 'Favorable for deep personal growth and claiming your power',
                'tone': 'harmonious'
            },
        }

        # Get specific transit info or create generic one
        if key in specific_transits:
            transit_info = specific_transits[key]
            return {
                'summary': base_meaning,
                'meaning': transit_info['meaning'],
                'life_areas': transit_info['life_areas'],
                'themes': transit_info['themes'],
                'tone': transit_info['tone']
            }
        else:
            # Generic interpretation based on aspect type
            aspect_effects = {
                'Conjunction': ('merging energies', 'Intensity and new beginnings in this area', 'neutral'),
                'Trine': ('flowing support', 'Natural ease and opportunities', 'harmonious'),
                'Sextile': ('cooperative potential', 'Opportunities with some effort required', 'harmonious'),
                'Opposition': ('tension and balance', 'Need to integrate opposing forces', 'challenging'),
                'Square': ('dynamic friction', 'Growth through challenge and action', 'challenging'),
                'Quincunx': ('awkward adjustment', 'Need for adaptation and recalibration', 'challenging')
            }

            effect_desc, theme, tone = aspect_effects.get(aspect,
                                                          ('interaction', 'Planetary energies combining', 'neutral'))

            return {
                'summary': base_meaning,
                'meaning': f'{effect_desc.capitalize()} between {transit_planet} and {natal_planet}',
                'life_areas': natal_area.capitalize(),
                'themes': theme,
                'tone': tone
            }

    def _build_daily_overview_prompt(
            self,
            natal_chart: Dict,
            transits: List[Dict],
            current_positions: Dict,
            moon_phase: Dict,
            journal_context: Optional[str] = None
    ) -> str:
        """Build prompt for daily overview reading."""

        # Extract key natal info
        natal_sun = next(p for p in natal_chart['planets'] if p['name'] == 'Sun')
        natal_moon = next(p for p in natal_chart['planets'] if p['name'] == 'Moon')

        # Get top 3 transits
        top_transits = transits[:3] if transits else []

        prompt = f"""Create a daily astrological reading for the client based on the following information.

NATAL CHART:
- Sun in {natal_sun['sign']} (core identity, life purpose)
- Moon in {natal_moon['sign']} (emotional inner landscape)
- Dominant Element: {natal_chart['dominant_element']}
- Dominant Modality: {natal_chart['dominant_modality']}

TODAY'S TRANSITS ACTIVATING THEIR NATAL CHART:
"""

        if top_transits:
            prompt += "\nNotable transits and their general meanings:\n"
            for transit in top_transits:
                basic_info = f"- Transit {transit['transit_planet']} in {transit['transit_sign']} {transit['aspect_type']} Natal {transit['natal_planet']} in {transit['natal_sign']} (orb: {transit['orb']}°)"
                interpretation = self._get_transit_interpretation_context(transit)
                prompt += f"{basic_info}\n"
                prompt += f"  MEANING: {interpretation['meaning']}\n"
                prompt += f"  LIFE AREAS: {interpretation['life_areas']}\n"
                prompt += f"  THEMES: {interpretation['themes']}\n\n"
        else:
            prompt += "- No major transits today — subtle background energies at play\n"

        prompt += f"""
CURRENT MOON PHASE:
{moon_phase['phase']} – {moon_phase['description']}

CLIENT'S CURRENT INNER WORLD (from today's journal):
{journal_context or "No journal reflections shared today."}

YOUR TASK:
Write a concise 2–3 paragraph daily reading that feels personal, grounded, and emotionally intelligent — as if you are an experienced astrologer speaking directly to a returning client. Be brief but resonant.

Tone & Style:
- Warm, wise, gently mystical, and human.
- Avoid generic horoscope language or platitudes.
- Bring nuance: include both supportive energies AND subtle challenges or tensions.
- Offer reflections that feel specific to the transits, the natal chart, and the journal context.
- If the journal reveals emotional tone, fears, hopes, or confusion, acknowledge it with empathy and weave it into the interpretation.
- Use concrete examples ("you may notice…", "you might feel pulled between…") instead of vague generalities.

CONTENT REQUIREMENTS:
1. Begin by briefly honoring their core nature (Sun/Moon + element/modality) in a way that feels truly seen.
2. Focus primarily on the MOST important transit — use the general meaning as a foundation, then interpret how it shows up specifically for them today based on their chart and journal context.
3. If the journal reveals current emotional weather, weave it naturally into the transit interpretation.
4. Offer one practical, doable suggestion for navigating today.
5. End with a brief, steady insight that feels earned.

Keep it warm, specific, and concise. Each paragraph should carry weight. Avoid fluff and generic statements."""

        return prompt

    def _build_transit_focus_prompt(
            self,
            natal_chart: Dict,
            transits: List[Dict],
            journal_context: Optional[str] = None
    ) -> str:
        """Build prompt focusing on specific transits."""

        if not transits:
            prompt = f"""The client is experiencing a transit-quiet day. 

NATAL CHART CONTEXT:
- Dominant Element: {natal_chart['dominant_element']}
- Dominant Modality: {natal_chart['dominant_modality']}

CLIENT'S CURRENT INNER WORLD (from today's journal):
{journal_context or "No journal reflections shared today."}

YOUR TASK:
Write a 2–3 paragraph reflection on working with their natal strengths during quiet cosmic periods. Acknowledge any journal themes. Offer grounded wisdom about integration, rest, or preparation. Be warm and specific, not generic."""
            return prompt

        top_transit = transits[0]

        # Extract key natal info
        natal_sun = next(p for p in natal_chart['planets'] if p['name'] == 'Sun')
        natal_moon = next(p for p in natal_chart['planets'] if p['name'] == 'Moon')

        # Get interpretation context for this transit
        interpretation = self._get_transit_interpretation_context(top_transit)

        prompt = f"""Provide an in-depth transit interpretation for the client based on the following information.

NATAL CHART CONTEXT:
- Sun in {natal_sun['sign']} (core identity)
- Moon in {natal_moon['sign']} (emotional nature)
- Dominant Element: {natal_chart['dominant_element']}
- Dominant Modality: {natal_chart['dominant_modality']}

PRIMARY TRANSIT BEING ANALYZED:
Transit {top_transit['transit_planet']} in {top_transit['transit_sign']} 
{top_transit['aspect_type']} ({top_transit['quality']})
Natal {top_transit['natal_planet']} in {top_transit['natal_sign']}
Orb: {top_transit['orb']}° | Strength: {top_transit['strength']}

GENERAL MEANING OF THIS TRANSIT:
Meaning: {interpretation['meaning']}
Life Areas: {interpretation['life_areas']}
Themes: {interpretation['themes']}

CLIENT'S CURRENT INNER WORLD (from today's journal):
{journal_context or "No journal reflections shared today."}

YOUR TASK:
Write a focused 2–3 paragraph transit interpretation that cuts through to what matters. Use the general transit meaning as your foundation, then personalize it deeply based on their natal chart and current experience.

Tone & Style:
- Grounded wisdom with a mystical edge.
- Acknowledge both gifts and tensions within this transit.
- Speak to how this energy may actually manifest in daily life — thoughts, feelings, interactions, choices.
- If journal content reveals current struggles or questions, relate the transit interpretation directly to what they're experiencing.
- Use concrete language: "You might find yourself…", "This can show up as…", "Watch for moments when…"

CONTENT REQUIREMENTS:
1. Start with the core psychological and practical meaning of this transit — what it's fundamentally asking of them.
2. Connect it directly to their natal chart (Sun/Moon, element, modality) — how does this transit interact with who they are?
3. Identify the specific life area being activated and how this might show up in thoughts, feelings, or situations.
4. If journal content reveals struggles or themes, name how the transit connects to what they're living through.
5. Offer 1–2 concrete, actionable suggestions for working with this energy consciously.
6. Include a brief awareness point about potential shadow or tension (realistic, not fearful).
7. Close with a grounded insight about what this transit is building toward.

Be clear, resonant, and emotionally intelligent. Each sentence should earn its place."""

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

        prompt = f"""Create an elemental wisdom reading for the client based on the following information.

NATAL CHART:
- Sun in {natal_sun['sign']} (core identity)
- Moon in {natal_moon['sign']} (emotional nature)
- Natal Dominant Element: {natal_element}
- Natal Dominant Modality: {natal_chart['dominant_modality']}

TODAY'S ELEMENTAL WEATHER:
- Current Dominant Element: {current_element}

CLIENT'S CURRENT INNER WORLD (from today's journal):
{journal_context or "No journal reflections shared today."}

ELEMENTAL CORRESPONDENCES (for reference):
- Fire: action, passion, willpower, initiative, anger, inspiration, restlessness
- Earth: manifestation, grounding, stability, sensuality, stubbornness, patience, material focus
- Air: thought, communication, perspective, detachment, scattered energy, curiosity, mental buzz
- Water: emotion, intuition, depth, empathy, overwhelm, sensitivity, flow

YOUR TASK:
Write a 2–3 paragraph elemental wisdom reading that feels like sitting across from a trusted astrologer who sees you clearly. Be warm, specific, and concise.

Tone & Style:
- Poetic but not purple prose — evocative without being vague.
- Speak to how their natal element shows up in their personality, needs, and patterns.
- Interpret the dance between their natal element and today's dominant elemental weather — where's the harmony? Where's the friction?
- If the journal reveals emotional tone or life circumstances, name how the elemental interplay might be showing up in that experience.
- Offer both affirmation and gentle challenge.

CONTENT REQUIREMENTS:
1. Begin by naming how their natal {natal_element} nature shows up in who they are — make it feel specific and seen.
2. Interpret the dance between their natal element and today's {current_element} energy — where's the support? Where's the tension? How might this feel in their body or mood today?
3. If the journal reveals emotional weather, connect it to the elemental interplay.
4. Offer one embodied, practical suggestion for balance or grounding.
5. Close with elemental wisdom they can carry through the day.

Use sensory, felt language. Be concise but resonant."""

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
            'is_fallback': True,
            'journal_included': False,
        }


# Convenience function
def generate_reading(natal_chart: Dict, reading_type: str = 'daily_overview', user=None) -> Dict:
    """
    Quick access to AI reading generation.

    Usage:
        from deep_dive.services.ai_reading_service import generate_reading
        reading = generate_reading(user_natal_chart, 'daily_overview')
    """
    service = AIReadingService()
    return service.generate_daily_reading(natal_chart, reading_type, user)