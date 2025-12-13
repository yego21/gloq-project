# deep_dive/services/ai_chart_reading_svc.py
"""
AI-powered astrological reading service.
Enhanced with psychologically nuanced transit interpretations and human-sounding guidance.
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
    Enhanced with psychologically nuanced transit interpretations.
    """

    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.astro_service = AstronomicalService()

    def generate_daily_reading(
            self,
            natal_chart: Dict,
            reading_type: str = 'daily_overview',
            user=None
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

            # Generate enhanced transit summaries for display
            transit_summaries = []
            for transit in transits[:3]:  # Top 3 transits
                interpretation = self._get_transit_interpretation_context(transit)
                summary = {
                    'transit_planet': transit['transit_planet'],
                    'transit_sign': transit['transit_sign'],
                    'aspect_type': transit['aspect_type'],
                    'natal_planet': transit['natal_planet'],
                    'natal_sign': transit['natal_sign'],
                    'orb': float(transit['orb']),
                    'quality': transit['quality'],
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
                'reading_type': reading_type,
                'reading_text': reading_text,
                'generated_at': datetime.now().isoformat(),
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
                'transit_summaries': transit_summaries,
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

        # COMPREHENSIVE TRANSIT DICTIONARY
        specific_transits = {
            # MARS TRANSITS - Action and Drive
            'Mars_Opposition_Saturn': {
                'summary': 'Drive meets resistance—patience under pressure',
                'meaning': 'The tension between your drive and life\'s limitations',
                'life_areas': 'Career ambitions, authority dynamics, long-term structures, disciplined action',
                'themes': 'A reality check moment where your willpower meets external constraints. This isn\'t about failure but strategic patience—like pushing against a door that will open at the right time, not when you demand it.',
                'shadow_aspect': 'Watch for resentment toward authority or turning frustration inward as self-criticism.',
                'grounded_recommendation': 'Instead of forcing outcomes, identify which walls are meant to be climbed and which redirect your path.',
                'tone': 'challenging',
                'disclaimer': 'This transit highlights existing tensions rather than creating new ones. The friction you feel is often life pointing toward where you need more strategic patience.'
            },
            'Mars_Square_Saturn': {
                'summary': 'Action meets obstacles—strategic recalibration',
                'meaning': 'Friction between immediate action and necessary restraint',
                'life_areas': 'Work ethic, physical energy management, ambitious projects facing delays',
                'themes': 'Your drive meets tangible obstacles asking for recalibration rather than brute force. Like a climber encountering unexpected rockfall, this asks you to reassess your route without abandoning the ascent.',
                'shadow_aspect': 'Avoid giving up entirely or pushing so hard you break something important.',
                'grounded_recommendation': 'Focus on preparation rather than propulsion. What foundations need shoring up?',
                'tone': 'challenging',
                'disclaimer': 'These obstacles aren\'t personal failures but timing mechanisms.'
            },
            'Mars_Conjunction_Venus': {
                'summary': 'Passion and pleasure unite—magnetic attraction',
                'meaning': 'Passion and desire dance together',
                'life_areas': 'Romantic connections, creative expression, financial initiatives',
                'themes': 'Your actions naturally align with what brings pleasure and connection. Magnetic energy draws people and opportunities toward you.',
                'shadow_aspect': 'Be mindful of impulsive relationship decisions or spending.',
                'grounded_recommendation': 'Channel this harmonious energy into projects blending beauty and action.',
                'tone': 'harmonious',
                'disclaimer': 'While this supports new beginnings, lasting connections require building trust over time.'
            },
            'Mars_Trine_Jupiter': {
                'summary': 'Confident action meets opportunity—favorable momentum',
                'meaning': 'Confident action meets expansive opportunity',
                'life_areas': 'Risk-taking, athletic pursuits, entrepreneurial ventures',
                'themes': 'Your actions are supported by luck and timing. Doors seem to open more easily.',
                'shadow_aspect': 'Overconfidence can lead to overlooking important details.',
                'grounded_recommendation': 'Trust intuition about when to act boldly, but maintain awareness.',
                'tone': 'harmonious',
                'disclaimer': 'Even favorable transits don\'t eliminate all obstacles—they simply improve odds.'
            },
            'Mars_Trine_Pluto': {
                'summary': 'Focused power surges—strategic intensity',
                'meaning': 'Focused action meets transformative power',
                'life_areas': 'Strategic initiatives, intense activity, psychological breakthroughs',
                'themes': 'Your actions carry extra power and focus. You might tackle difficult tasks with unusual determination.',
                'shadow_aspect': 'Power struggles or manipulative behavior can emerge if not conscious.',
                'grounded_recommendation': 'Channel this intense energy into constructive transformation.',
                'tone': 'harmonious',
                'disclaimer': 'True power transforms without needing to dominate.'
            },
            'Mars_Opposition_Jupiter': {
                'summary': 'Bold action meets wisdom—confidence calibrated',
                'meaning': 'Expansive action meets wise restraint',
                'life_areas': 'Risk assessment, entrepreneurial decisions, balancing confidence',
                'themes': 'Your drive for expansion meets the need for wise boundaries. You might feel torn between bold action and practical limitations.',
                'shadow_aspect': 'Overconfidence leading to overextension or unnecessary risks.',
                'grounded_recommendation': 'Think big, start small. Test assumptions before full commitment.',
                'tone': 'challenging',
                'disclaimer': 'Growth requires both expansion and discernment.'
            },

            # SUN TRANSITS - Identity and Vitality
            'Sun_Trine_Moon': {
                'summary': 'Heart and mind harmonize—inner alignment',
                'meaning': 'Inner harmony between identity and emotions',
                'life_areas': 'Self-expression, emotional security, relationship harmony',
                'themes': 'Your conscious self and emotional nature align easily. Feelings and actions cooperate rather than conflict.',
                'shadow_aspect': 'Possible complacency—growth sometimes requires healthy tension.',
                'grounded_recommendation': 'Use this harmonious energy to heal old emotional patterns.',
                'tone': 'harmonious',
                'disclaimer': 'This alignment supports emotional intelligence but doesn\'t exempt you from inner work.'
            },
            'Sun_Conjunction_Venus': {
                'summary': 'Charm and magnetism amplified—social grace',
                'meaning': 'Self-expression feels attractive and valued',
                'life_areas': 'Relationships, self-worth, social connections',
                'themes': 'Your personal charm and social appeal are heightened. Others respond positively to your presence.',
                'shadow_aspect': 'Vanity or over-reliance on external validation can emerge.',
                'grounded_recommendation': 'Share your authentic self in social situations.',
                'tone': 'harmonious',
                'disclaimer': 'This transit enhances existing qualities—it doesn\'t fundamentally change who you are.'
            },
            'Sun_Square_Saturn': {
                'summary': 'Identity tested by reality—maturation point',
                'meaning': 'Your identity meets reality\'s boundaries',
                'life_areas': 'Career progress, authority relationships, self-esteem tests',
                'themes': 'This often feels like a "prove yourself" moment where capabilities or commitment are tested.',
                'shadow_aspect': 'Beware of shrinking from challenges or becoming rigidly defensive.',
                'grounded_recommendation': 'Focus on what you can control: preparation, response to feedback, commitment.',
                'tone': 'challenging',
                'disclaimer': 'These tests build lasting structures. The most solid foundations are built slowly.'
            },
            'Sun_Opposition_Pluto': {
                'summary': 'Power dynamics surface—transformative confrontation',
                'meaning': 'Ego confronts transformative power dynamics',
                'life_areas': 'Control issues, personal transformation, power struggles',
                'themes': 'This intense transit brings power dynamics to the surface. You might encounter situations revealing where power is wielded unconsciously.',
                'shadow_aspect': 'Power struggles, manipulation, or obsessive behavior can emerge.',
                'grounded_recommendation': 'Notice where you\'re giving power away or clinging too tightly to control.',
                'tone': 'challenging',
                'disclaimer': 'This transit reveals existing power dynamics; your response determines the outcome.'
            },
            'Sun_Conjunction_Mercury': {
                'summary': 'Identity and mind unite—clear expression',
                'meaning': 'Identity and mind align',
                'life_areas': 'Self-expression, communication, mental clarity about purpose',
                'themes': 'Your thoughts and identity work in harmony. You might feel clear about who you are and able to express it effectively.',
                'shadow_aspect': 'Can become overly identified with opinions or intellectually rigid.',
                'grounded_recommendation': 'Express your truth while remaining open to others\' perspectives.',
                'tone': 'neutral',
                'disclaimer': 'Clarity of thought supports, but doesn\'t replace, wisdom of heart.'
            },

            # MERCURY TRANSITS - Communication and Thinking
            'Mercury_Square_Neptune': {
                'summary': 'Mental fog descends—clarity requires patience',
                'meaning': 'Clarity meets confusion at the crossroads',
                'life_areas': 'Communication, decision-making, contracts',
                'themes': 'Information may feel fuzzy, misleading, or emotionally charged. Classic aspect for misunderstandings.',
                'shadow_aspect': 'Important details may be overlooked, or assumptions mistaken for facts.',
                'grounded_recommendation': 'Double-check information, get confirmations in writing.',
                'tone': 'challenging',
                'disclaimer': 'Not every confusing moment signals deception—sometimes understanding requires time.'
            },
            'Mercury_Trine_Jupiter': {
                'summary': 'Mind expands optimistically—learning flows',
                'meaning': 'Mind expands with optimism and perspective',
                'life_areas': 'Learning, communication, travel planning, teaching',
                'themes': 'Your thinking becomes more expansive and optimistic. You might find it easier to grasp complex concepts.',
                'shadow_aspect': 'Overconfidence in opinions or overlooking practical details.',
                'grounded_recommendation': 'Use this mental clarity for learning something new.',
                'tone': 'harmonious',
                'disclaimer': 'Expansive thinking is valuable, but grounding ideas makes them actionable.'
            },
            'Mercury_Conjunction_Mars': {
                'summary': 'Sharp mind, sharper words—mental intensity',
                'meaning': 'Sharp words and quick decisions',
                'life_areas': 'Communication, debates, mental energy, assertive expression',
                'themes': 'Your mind works quickly, and you might feel compelled to speak directly. Mental energy is high.',
                'shadow_aspect': 'Tendency toward argumentativeness or speaking without thinking.',
                'grounded_recommendation': 'Channel this mental energy into productive debates or writing.',
                'tone': 'neutral',
                'disclaimer': 'Direct communication is powerful, but timing determines whether it builds bridges.'
            },
            'Mercury_Square_Uranus': {
                'summary': 'Mental electricity sparks—brilliant disruption',
                'meaning': 'Mental breakthroughs meet disruptive insights',
                'life_areas': 'Sudden ideas, technological disruptions, unconventional thinking',
                'themes': 'Your thinking might feel electric or scattered. Sudden insights or disruptive thoughts could surface.',
                'shadow_aspect': 'Mental restlessness can lead to scattered attention or impulsive communication.',
                'grounded_recommendation': 'Capture brilliant ideas when they come, but wait before acting on them.',
                'tone': 'challenging',
                'disclaimer': 'Revolutionary ideas need time to mature before implementation.'
            },
            'Mercury_Trine_Neptune': {
                'summary': 'Intuition guides thought—creative flow',
                'meaning': 'Intuitive thinking meets creative flow',
                'life_areas': 'Creative writing, spiritual insights, compassionate communication',
                'themes': 'Your thinking connects easily with intuition and imagination. Words may flow poetically.',
                'shadow_aspect': 'Facts might feel less important than feelings, potentially leading to misunderstandings.',
                'grounded_recommendation': 'Trust intuitive hits but verify important details.',
                'tone': 'harmonious',
                'disclaimer': 'Intuition illuminates, but practical steps bring dreams to earth.'
            },

            # VENUS TRANSITS - Relationships and Values
            'Venus_Opposition_Mars': {
                'summary': 'Desire meets harmony—passionate tension',
                'meaning': 'The delicate dance between what you desire and how you pursue it',
                'life_areas': 'Relationship dynamics, sexual chemistry, values in conflict',
                'themes': 'Often manifests as a pull between harmony and assertion—wanting connection but also wanting your way.',
                'shadow_aspect': 'Watch for passive-aggression or expressing wants as demands.',
                'grounded_recommendation': 'Practice stating desires clearly while remaining open to others\' perspectives.',
                'tone': 'challenging',
                'disclaimer': 'This highlights where you need balance between assertion and receptivity.'
            },
            'Venus_Trine_Saturn': {
                'summary': 'Love meets commitment—stable foundations',
                'meaning': 'Love meets commitment and stability',
                'life_areas': 'Long-term relationships, financial planning, serious commitments',
                'themes': 'Relationship energies feel more serious and grounded. Excellent for making commitments.',
                'shadow_aspect': 'Can feel overly serious or practical, missing spontaneous joy.',
                'grounded_recommendation': 'Use this energy to strengthen existing commitments.',
                'tone': 'harmonious',
                'disclaimer': 'Stability is valuable, but relationships also need flexibility.'
            },
            'Venus_Square_Pluto': {
                'summary': 'Love confronts intensity—transformative depths',
                'meaning': 'Love confronts transformative intensity',
                'life_areas': 'Relationship power dynamics, shared resources, obsessions',
                'themes': 'Intense feelings surface in relationships or financial matters. You might encounter hidden power dynamics.',
                'shadow_aspect': 'Possessiveness, jealousy, or power struggles can emerge.',
                'grounded_recommendation': 'Notice what you\'re clinging to and why.',
                'tone': 'challenging',
                'disclaimer': 'Intense feelings are signals, not commands.'
            },
            'Venus_Conjunction_Jupiter': {
                'summary': 'Love expands abundantly—social magnetism',
                'meaning': 'Expansive love meets abundant connection',
                'life_areas': 'Social opportunities, romantic possibilities, financial generosity',
                'themes': 'Your social and romantic appeal expands. You might attract positive attention or feel unusually generous.',
                'shadow_aspect': 'Over-optimism in relationships or financial overextension.',
                'grounded_recommendation': 'Enjoy social abundance but maintain reasonable boundaries.',
                'tone': 'harmonious',
                'disclaimer': 'Abundance flows best when shared responsibly.'
            },
            'Venus_Square_Uranus': {
                'summary': 'Relationship surprises shake up—freedom calls',
                'meaning': 'Relationship surprises meet freedom needs',
                'life_areas': 'Unconventional attractions, sudden relationship changes',
                'themes': 'Unexpected developments in relationships or finances. You might feel restless with routine.',
                'shadow_aspect': 'Impulsive relationship decisions or financial risks.',
                'grounded_recommendation': 'Embrace authentic connections but avoid burning bridges.',
                'tone': 'challenging',
                'disclaimer': 'Freedom in relationships requires both independence and responsibility.'
            },

            # JUPITER TRANSITS - Expansion and Beliefs
            'Jupiter_Trine_Sun': {
                'summary': 'Identity expands gracefully—opportunities arise',
                'meaning': 'Your essence expands into new possibilities',
                'life_areas': 'Personal growth, career opportunities, confidence',
                'themes': 'Supportive energy helps recognize and step into potential. Opportunities may arrive with surprising ease.',
                'shadow_aspect': 'Overextension—saying yes to too many opportunities dilutes energy.',
                'grounded_recommendation': 'Choose growth paths aligning with core identity.',
                'tone': 'harmonious',
                'disclaimer': 'Even favorable transits require participation.'
            },
            'Jupiter_Conjunction_Venus': {
                'summary': 'Abundance flows freely—social expansion',
                'meaning': 'Abundance meets pleasure and connection',
                'life_areas': 'Social expansion, financial opportunities, romantic possibilities',
                'themes': 'Social and romantic opportunities expand. Financial luck or generous impulses might surface.',
                'shadow_aspect': 'Overindulgence or spreading resources too thin.',
                'grounded_recommendation': 'Share abundance with others.',
                'tone': 'harmonious',
                'disclaimer': 'Abundance flows best when shared, not hoarded.'
            },
            'Jupiter_Square_Saturn': {
                'summary': 'Growth meets limits—wise expansion',
                'meaning': 'Growth confronts practical limits',
                'life_areas': 'Career ambitions, philosophical beliefs versus reality',
                'themes': 'Expansive desires meet structural limitations. You might feel torn between risk and safety.',
                'shadow_aspect': 'Can swing between reckless optimism and pessimistic restriction.',
                'grounded_recommendation': 'Look for the middle path—ambitious enough to grow, practical enough to sustain.',
                'tone': 'challenging',
                'disclaimer': 'This tension reveals where growth needs more structure or structures need flexibility.'
            },
            'Jupiter_Opposition_Moon': {
                'summary': 'Emotional expansion tested—growth vs. security',
                'meaning': 'Expansive feelings meet emotional boundaries',
                'life_areas': 'Emotional growth, family expansion, comfort zone stretching',
                'themes': 'Your emotional world expands or confronts its limits. You might feel pulled between security needs and growth.',
                'shadow_aspect': 'Emotional overextension or using optimism to avoid real feelings.',
                'grounded_recommendation': 'Expand your emotional repertoire while honoring your need for safety.',
                'tone': 'challenging',
                'disclaimer': 'Emotional growth happens at the edge of comfort, not far beyond it.'
            },

            # SATURN TRANSITS - Structure and Responsibility
            'Saturn_Square_Moon': {
                'summary': 'Emotional burden weighs heavy—boundaries needed',
                'meaning': 'Responsibility weighs on emotional security',
                'life_areas': 'Family obligations, emotional burdens, home responsibilities',
                'themes': 'Emotional needs might feel burdened by responsibilities. You could experience loneliness even when busy.',
                'shadow_aspect': 'Emotional repression or using busyness to avoid feelings.',
                'grounded_recommendation': 'Create structured self-care. Emotional health needs scheduling too.',
                'tone': 'challenging',
                'disclaimer': 'Feeling emotionally burdened is information, not failure.'
            },
            'Saturn_Trine_Venus': {
                'summary': 'Commitment strengthens love—lasting value',
                'meaning': 'Structure supports lasting love and values',
                'life_areas': 'Committed relationships, financial stability, artistic discipline',
                'themes': 'Relationships benefit from maturity and commitment. Financial decisions made now tend to have lasting positive effects.',
                'shadow_aspect': 'Can become overly practical or cautious in matters of heart.',
                'grounded_recommendation': 'Invest in relationships and projects with long-term potential.',
                'tone': 'harmonious',
                'disclaimer': 'Lasting beauty often requires patience—what\'s built slowly often endures.'
            },
            'Saturn_Conjunction_Sun': {
                'summary': 'Identity matures deeply—defining moment',
                'meaning': 'Your identity meets its maturation point',
                'life_areas': 'Life direction, career definition, adult responsibilities',
                'themes': 'Significant transit marking a major life chapter shift toward greater maturity and definition.',
                'shadow_aspect': 'Resisting necessary maturation or clinging to outgrown identities.',
                'grounded_recommendation': 'Identify what foundations need strengthening.',
                'tone': 'neutral',
                'disclaimer': 'This transit works over months, not days. Its gifts often reveal themselves in hindsight.'
            },
            'Saturn_Trine_Mars': {
                'summary': 'Discipline meets momentum—sustained results',
                'meaning': 'Disciplined action meets sustained results',
                'life_areas': 'Long-term projects, career advancement, physical discipline',
                'themes': 'Your actions align with sustainable structures. You might find it easier to persist with difficult tasks.',
                'shadow_aspect': 'Can become overly rigid or perfectionistic about progress.',
                'grounded_recommendation': 'Build momentum through consistent, sustainable effort.',
                'tone': 'harmonious',
                'disclaimer': 'Lasting results come from consistent application, not sporadic intensity.'
            },
            'Saturn_Square_Venus': {
                'summary': 'Love tested by reality—value alignment',
                'meaning': 'Love meets reality testing',
                'life_areas': 'Relationship commitments, financial responsibilities, value tests',
                'themes': 'Your values and relationships face reality checks. You might encounter limitations requiring mature handling.',
                'shadow_aspect': 'Emotional withholding or using practicality to avoid intimacy.',
                'grounded_recommendation': 'Invest in what has lasting value, not just immediate pleasure.',
                'tone': 'challenging',
                'disclaimer': 'Enduring love requires both feeling and commitment.'
            },

            # URANUS TRANSITS - Change and Innovation
            'Uranus_Opposition_Sun': {
                'summary': 'Identity disrupted—liberation calls',
                'meaning': 'Change disrupts established identity',
                'life_areas': 'Life direction, freedom needs, independence',
                'themes': 'Restlessness with current identity or life structure. Sudden realizations about what no longer fits.',
                'shadow_aspect': 'Rebellion for its own sake or burning bridges prematurely.',
                'grounded_recommendation': 'Notice what feels authentically you versus what you\'ve outgrown.',
                'tone': 'challenging',
                'disclaimer': 'Change is inevitable, but how you navigate it determines the outcome.'
            },
            'Uranus_Trine_Venus': {
                'summary': 'Unconventional attraction—creative innovation',
                'meaning': 'Innovation meets attraction and values',
                'life_areas': 'Unconventional relationships, creative breakthroughs, financial opportunities',
                'themes': 'Attraction to unusual people or situations. Creative inspiration strikes unexpectedly.',
                'shadow_aspect': 'Fickleness in relationships or financial decisions.',
                'grounded_recommendation': 'Stay open to unexpected connections and creative ideas.',
                'tone': 'harmonious',
                'disclaimer': 'Innovation is exciting, but lasting relationships still require consistent attention.'
            },
            'Uranus_Conjunction_Mercury': {
                'summary': 'Mind revolutionizes—breakthrough thinking',
                'meaning': 'Innovative thinking meets communication breakthroughs',
                'life_areas': 'Sudden insights, technological communication, unconventional ideas',
                'themes': 'Your thinking becomes unusually original or disruptive. Sudden insights or breakthroughs may occur.',
                'shadow_aspect': 'Scattered thinking or communication that confuses rather than clarifies.',
                'grounded_recommendation': 'Capture innovative ideas but structure them before sharing widely.',
                'tone': 'neutral',
                'disclaimer': 'Brilliant ideas need coherent communication to have impact.'
            },

            # NEPTUNE TRANSITS - Dreams and Spirituality
            'Neptune_Square_Mercury': {
                'summary': 'Mental fog clouds judgment—intuition vs. facts',
                'meaning': 'Dreams cloud logical thinking',
                'life_areas': 'Communication clarity, decision-making, boundaries',
                'themes': 'Facts feel slippery, and intuition may override logic. Important to double-check information.',
                'shadow_aspect': 'Vulnerability to scams, gossip, or confusing situations.',
                'grounded_recommendation': 'Trust gut feelings but verify facts.',
                'tone': 'challenging',
                'disclaimer': 'Not every confusing message is deceptive—sometimes it\'s incomplete.'
            },
            'Neptune_Trine_Moon': {
                'summary': 'Intuition deepens emotionally—spiritual sensitivity',
                'meaning': 'Dreams and intuition support emotional depth',
                'life_areas': 'Spiritual connection, creative inspiration, compassionate relationships',
                'themes': 'Emotions flow with spiritual sensitivity. Dreams may be vivid or prophetic.',
                'shadow_aspect': 'Overwhelming empathy or difficulty distinguishing your feelings from others\'.',
                'grounded_recommendation': 'Journal dreams and intuitive hits.',
                'tone': 'harmonious',
                'disclaimer': 'Spiritual sensitivity is a gift, but grounding maintains healthy boundaries.'
            },
            'Neptune_Conjunction_Venus': {
                'summary': 'Love becomes dreamlike—idealistic connection',
                'meaning': 'Dreamy love meets idealistic values',
                'life_areas': 'Romantic idealism, creative inspiration, spiritual values',
                'themes': 'Your values become infused with idealism and compassion. Relationships take on a dreamy, soulful quality.',
                'shadow_aspect': 'Idealization of people/situations or unclear boundaries.',
                'grounded_recommendation': 'Appreciate beauty and connection while maintaining realistic awareness.',
                'tone': 'harmonious',
                'disclaimer': 'Idealism enriches life but needs grounding in reality to sustain.'
            },

            # PLUTO TRANSITS - Transformation and Power
            'Pluto_Square_Venus': {
                'summary': 'Love transformed intensely—power purges',
                'meaning': 'Transformation through relationships and values',
                'life_areas': 'Relationship power dynamics, shared resources, value transformation',
                'themes': 'Relationships become crucibles for transformation. You might attract intense connections revealing shadow aspects.',
                'shadow_aspect': 'Possessive behavior, power struggles, or manipulative dynamics.',
                'grounded_recommendation': 'Notice what relationships or values you\'re clinging to out of fear.',
                'tone': 'challenging',
                'disclaimer': 'Transformation is rarely comfortable, but what emerges is often more authentic.'
            },
            'Pluto_Trine_Sun': {
                'summary': 'Personal power awakens—deep transformation',
                'meaning': 'Personal empowerment through deep transformation',
                'life_areas': 'Personal power, psychological depth, career transformation',
                'themes': 'Ability to transform limitations into strengths. Psychological insights come more easily.',
                'shadow_aspect': 'Power trips or using transformation as excuse for controlling behavior.',
                'grounded_recommendation': 'Use this energy for deep personal work or strategic career moves.',
                'tone': 'harmonious',
                'disclaimer': 'True power isn\'t control over others but sovereignty over yourself.'
            },

            # MOON TRANSITS - Emotional Flow
            'Moon_Conjunction_Venus': {
                'summary': 'Emotional harmony flows—nurturing connection',
                'meaning': 'Emotional harmony meets relational needs',
                'life_areas': 'Comfort in relationships, self-care, nurturing connections',
                'themes': 'Your emotional nature aligns with what brings pleasure and connection. You might feel especially affectionate.',
                'shadow_aspect': 'Avoid using comfort as avoidance of necessary growth.',
                'grounded_recommendation': 'Indulge in what genuinely nourishes your soul.',
                'tone': 'harmonious',
                'disclaimer': 'Emotional harmony is wonderful, but lasting peace comes from inner security.'
            },
            'Moon_Opposition_Mars': {
                'summary': 'Emotional reactivity spikes—feelings run hot',
                'meaning': 'Emotional reactions meet assertive impulses',
                'life_areas': 'Family dynamics, emotional reactivity, conflict with loved ones',
                'themes': 'Feelings might surface with unexpected intensity. You could experience quick emotional reactions.',
                'shadow_aspect': 'Watch for emotional outbursts or taking things too personally.',
                'grounded_recommendation': 'Pause before reacting. Name the feeling before expressing it.',
                'tone': 'challenging',
                'disclaimer': 'Intense feelings are signals, not commands. Your response determines the outcome.'
            },
            'Moon_Trine_Mercury': {
                'summary': 'Feelings and thoughts cooperate—emotional intelligence',
                'meaning': 'Emotions and thoughts cooperate',
                'life_areas': 'Emotional intelligence, intuitive thinking, compassionate communication',
                'themes': 'Your feelings and thoughts support each other naturally. You might find it easy to articulate emotions.',
                'shadow_aspect': 'Over-analysis of feelings or emotional attachment to ideas.',
                'grounded_recommendation': 'Use this clarity to understand emotional patterns without over-intellectualizing.',
                'tone': 'harmonious',
                'disclaimer': 'Understanding emotions intellectually doesn\'t always translate to feeling them fully.'
            },
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
            # ENHANCED GENERIC FALLBACK with psychological depth
            planet_roles = {
                'Sun': 'identity/ego', 'Moon': 'emotions/security', 'Mercury': 'thinking/communication',
                'Venus': 'values/relationships', 'Mars': 'action/desire', 'Jupiter': 'expansion/beliefs',
                'Saturn': 'structure/limits', 'Uranus': 'change/innovation', 'Neptune': 'dreams/intuition',
                'Pluto': 'transformation/power'
            }

            planet_meanings = {
                'Sun': 'identity, vitality, purpose',
                'Moon': 'emotions, instincts, comfort',
                'Mercury': 'communication, thinking, learning',
                'Venus': 'relationships, values, pleasure',
                'Mars': 'action, desire, assertion',
                'Jupiter': 'expansion, optimism, beliefs',
                'Saturn': 'structure, limits, responsibility',
                'Uranus': 'change, innovation, disruption',
                'Neptune': 'dreams, spirituality, intuition',
                'Pluto': 'transformation, power, depth'
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
            transit_energy = planet_meanings.get(transit_planet, transit_planet)
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

            # Get aspect theme or default
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
            'transits_analyzed': 0,
            'top_transits': [],
            'transit_summaries': [],
            'is_fallback': True,
            'journal_included': False,
        }


# Convenience function
def generate_reading(natal_chart: Dict, reading_type: str = 'daily_overview', user=None) -> Dict:
    """
    Quick access to AI reading generation.

    Usage:
        from deep_dive.services.ai_reading_service import generate_reading
        reading = generate_reading(user_natal_chart, 'daily_overview', user=request.user)
    """
    service = AIReadingService()
    return service.generate_daily_reading(natal_chart, reading_type, user)