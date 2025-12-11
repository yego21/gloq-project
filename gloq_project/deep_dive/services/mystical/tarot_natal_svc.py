# deep_dive/tarot_natal_svc.py

from typing import Dict, List
import random


class TarotNatalService:
    """
    Service for generating tarot readings based on natal chart data.
    Integrates natal chart analysis with tarot card selection.
    """

    def __init__(self, natal_chart: Dict):
        self.natal_chart = natal_chart
        self.planets = {p['name']: p for p in natal_chart['planets']}
        self.aspects = natal_chart.get('aspects', [])
        self.dominant_element = natal_chart.get('dominant_element', 'Earth')
        self.dominant_modality = natal_chart.get('dominant_modality', 'Cardinal')

    def get_dominant_planetary_energy(self) -> str:
        """
        Determine dominant planetary energy from:
        1. Dominant element alignment
        2. Planet with most aspects
        3. Sun/Moon emphasis
        4. Stelliums (3+ planets in same sign)

        Returns: planet name (e.g., 'Sun', 'Moon', 'Saturn')
        """

        # Count aspects per planet
        aspect_count = {}
        for aspect in self.aspects:
            planet1 = aspect['planet1']
            planet2 = aspect['planet2']
            aspect_count[planet1] = aspect_count.get(planet1, 0) + 1
            aspect_count[planet2] = aspect_count.get(planet2, 0) + 1

        # Check for stelliums (3+ planets in same sign)
        sign_planets = {}
        for planet in self.natal_chart['planets']:
            sign = planet['sign']
            sign_planets.setdefault(sign, []).append(planet['name'])

        # Find stellium planets if any exist
        stellium_planets = []
        for planets in sign_planets.values():
            if len(planets) >= 3:
                stellium_planets.extend(planets)

        # Get Sun and Moon
        sun = self.planets.get('Sun')
        moon = self.planets.get('Moon')

        # Priority 1: Sun or Moon in dominant element
        if sun and sun['element'] == self.dominant_element:
            return 'Sun'
        if moon and moon['element'] == self.dominant_element:
            return 'Moon'

        # Priority 2: Planet in stellium with most aspects
        if stellium_planets:
            stellium_with_aspects = [
                (p, aspect_count.get(p, 0))
                for p in stellium_planets
            ]
            if stellium_with_aspects:
                return max(stellium_with_aspects, key=lambda x: x[1])[0]

        # Priority 3: Planet with most aspects
        if aspect_count:
            return max(aspect_count, key=aspect_count.get)

        # Fallback to Sun
        return 'Sun'

    def personalize_interpretation(self, base_interpretation: str,
                                   dominant_planet: str) -> str:
        """
        Add natal chart context to card interpretation.
        Weaves in dominant element, Sun/Moon signs, and planetary emphasis.

        Args:
            base_interpretation: Card's generic interpretation
            dominant_planet: Result from get_dominant_planetary_energy()

        Returns:
            Personalized interpretation string
        """

        sun = self.planets.get('Sun', {})
        moon = self.planets.get('Moon', {})
        sun_sign = sun.get('sign', 'Aries')
        moon_sign = moon.get('sign', 'Cancer')

        # Element-based approach suggestions
        element_traits = {
            'Fire': 'bold action and passionate pursuit',
            'Earth': 'grounded wisdom and practical steps',
            'Air': 'mental clarity and open communication',
            'Water': 'emotional depth and intuitive guidance'
        }

        approach = element_traits.get(self.dominant_element, 'mindful awareness')

        # Build personalized ending
        personal_touch = f" With your strong {self.dominant_element} emphasis, approach this through {approach}."

        # Add planetary-specific guidance
        if dominant_planet == 'Sun':
            personal_touch += f" Your {sun_sign} Sun lights the way forward with confidence."
        elif dominant_planet == 'Moon':
            personal_touch += f" Your {moon_sign} Moon guides your emotional compass."
        elif dominant_planet in self.planets:
            planet_data = self.planets[dominant_planet]
            personal_touch += f" Your natal {dominant_planet} in {planet_data['sign']} amplifies this energy."

        return base_interpretation + personal_touch

    def generate_natal_insight(self, selected_card: Dict) -> str:
        """
        Generate specific insight tying card to natal chart.

        Examines:
        - Card's planet rulers vs natal placements
        - Card's element vs dominant element
        - Relevant natal aspects

        Args:
            selected_card: Card dictionary with planets, element, etc.

        Returns:
            Natal insight string
        """

        card_planets = selected_card.get('planets', [])
        card_element = selected_card.get('element', '')

        insights = []

        # Check if user has card's ruling planets prominently placed
        for planet_name in card_planets:
            if planet_name in self.planets:
                natal_planet = self.planets[planet_name]
                insights.append(
                    f"Your natal {planet_name} in {natal_planet['sign']} deeply resonates with this card's essence"
                )

        # Element resonance
        if card_element and card_element == self.dominant_element:
            insights.append(
                f"This card's {card_element} element mirrors your dominant {self.dominant_element} nature, amplifying its message"
            )

        # Check for aspects involving card's planets
        card_planet_aspects = [
            a for a in self.aspects
            if a['planet1'] in card_planets or a['planet2'] in card_planets
        ]

        if card_planet_aspects:
            # Get strongest aspect (smallest orb)
            strongest = min(card_planet_aspects, key=lambda x: x['orb'])
            aspect_quality = {
                'Conjunction': 'intensifies',
                'Trine': 'harmonizes with',
                'Square': 'challenges and activates',
                'Opposition': 'balances',
                'Sextile': 'supports'
            }.get(strongest['aspect_type'], 'connects to')

            insights.append(
                f"Your natal {strongest['aspect_type']} between {strongest['planet1']} and {strongest['planet2']} {aspect_quality} this card's guidance"
            )

        # Return first insight or default
        if insights:
            return insights[0]
        else:
            # Fallback to modality-based insight
            modality_traits = {
                'Cardinal': 'initiating and leading',
                'Fixed': 'maintaining and deepening',
                'Mutable': 'adapting and flowing'
            }
            trait = modality_traits.get(self.dominant_modality, 'experiencing')
            return f"Your {self.dominant_modality} nature supports {trait} with this card's energy"

    def select_card_by_transits(self, transits: List[Dict],
                                deck: List[Dict]) -> Dict:
        """
        Select card based on current transits.
        Matches strongest transit planet to card rulers.

        Args:
            transits: List of current transit aspects (from TransitCalculator)
            deck: List of tarot card dictionaries

        Returns:
            Selected card dictionary
        """

        if not transits:
            return random.choice(deck)

        # Get top 3 transits by strength
        top_transits = transits[:3]

        # Try to match transit planets to card rulers
        for transit in top_transits:
            transit_planet = transit['transit_planet']

            # Find cards ruled by this planet
            matching_cards = [
                card for card in deck
                if transit_planet in card.get('planets', [])
            ]

            if matching_cards:
                # Weight by transit quality
                if transit['quality'] == 'challenging':
                    # Prefer "growth" cards for challenging transits
                    growth_cards = [
                        c for c in matching_cards
                        if 'transformation' in c.get('keywords', '').lower()
                           or 'change' in c.get('keywords', '').lower()
                    ]
                    if growth_cards:
                        return random.choice(growth_cards)

                return random.choice(matching_cards)

        # No matching cards, use element-based selection
        dominant_elem_cards = [
            card for card in deck
            if card.get('element') == self.dominant_element
        ]

        if dominant_elem_cards:
            return random.choice(dominant_elem_cards)

        # Final fallback: random
        return random.choice(deck)

    def generate_astro_context(self, selected_card: Dict,
                               transits: List[Dict] = None) -> str:
        """
        Generate astrological context text for the card.
        Combines transit info with natal chart alignment.
        Now includes aspect quality information.

        Args:
            selected_card: The drawn card
            transits: Optional list of current transits

        Returns:
            Astrological context string
        """

        card_planets = selected_card.get('planets', [])
        energy_type = selected_card.get('energy_type', 'cosmic energy')

        # Base context
        context_parts = []

        # Mention card's planetary rulers
        if card_planets:
            planet_names = ', '.join(card_planets)
            context_parts.append(f"Ruled by {planet_names}")

        # Check if any transits involve card's planets
        if transits:
            relevant_transits = [
                t for t in transits
                if t['transit_planet'] in card_planets or t['natal_planet'] in card_planets
            ]

            if relevant_transits:
                top_transit = relevant_transits[0]
                aspect_type = top_transit.get('aspect_type', '')
                aspect_quality = top_transit.get('quality', '')

                # Describe aspect with appropriate language
                aspect_description = {
                    'Conjunction': 'merging with',
                    'Trine': 'flowing harmoniously with',
                    'Sextile': 'supporting',
                    'Square': 'challenging',
                    'Opposition': 'facing off with'
                }.get(aspect_type, 'connecting to')

                context_parts.append(
                    f"currently {aspect_description} your natal {top_transit['natal_planet']} "
                    f"through {top_transit['transit_planet']} {aspect_type}"
                )

                # Add quality-specific insight
                if aspect_quality == 'challenging' or aspect_type in ['Square', 'Opposition']:
                    context_parts.append("bringing growth through tension")
                elif aspect_quality == 'flowing' or aspect_type in ['Trine', 'Sextile']:
                    context_parts.append("offering smooth integration")
                elif aspect_quality == 'intense' or aspect_type == 'Conjunction':
                    context_parts.append("intensifying this energy")

        # Add energy type
        if not context_parts or len(context_parts) < 2:
            context_parts.append(f"this card resonates with your natural {energy_type}")

        return ', '.join(context_parts) if context_parts else f"This card connects to {energy_type}"


from typing import Dict, List, Tuple
import random


class ThreeCardSpreadService:
    """
    Generates cosmically-aligned Past/Present/Future spreads.
    Each position draws from different astrological energies.
    """

    def __init__(self, natal_chart: Dict, transits: List[Dict], user_intention: str = ''):
        self.natal_chart = natal_chart
        self.transits = transits
        self.user_intention = user_intention  # NEW
        self.planets = {p['name']: p for p in natal_chart['planets']}
        self.dominant_element = natal_chart.get('dominant_element', 'Earth')

    def generate_spread(self, deck: List[Dict]) -> Tuple[Dict, Dict, Dict]:
        """
        Generate a three-card spread with cosmic intelligence.
        Intention influences the present card selection.

        Returns:
            (past_card, present_card, future_card)
        """

        past_card = self._draw_past_card(deck)
        present_card = self._draw_present_card(deck, exclude=[past_card])
        future_card = self._draw_future_card(deck, exclude=[past_card, present_card])

        return (past_card, present_card, future_card)


    def _draw_past_card(self, deck: List[Dict]) -> Dict:
        """
        PAST: Foundation, roots, what brought you here.

        Strategy:
        - 60%: Natal chart emphasis (Saturn, Sun, Moon)
        - 30%: Dominant element cards
        - 10%: Major Arcana (archetypal foundation)
        """

        roll = random.random()

        # ═══════════════════════════════════════════════════════════
        # PATH 1: Natal Chart Foundation (60%)
        # ═══════════════════════════════════════════════════════════
        if roll < 0.60:
            # Focus on slow-moving natal planets (structure, identity)
            foundation_planets = ['Saturn', 'Sun', 'Moon', 'Jupiter']

            for planet_name in foundation_planets:
                if planet_name in self.planets:
                    matching_cards = [
                        card for card in deck
                        if planet_name in card.get('planets', [])
                    ]
                    if matching_cards:
                        return random.choice(matching_cards)

        # ═══════════════════════════════════════════════════════════
        # PATH 2: Dominant Element (30%)
        # ═══════════════════════════════════════════════════════════
        elif roll < 0.90:
            elem_cards = [
                card for card in deck
                if card.get('element') == self.dominant_element
            ]
            if elem_cards:
                return random.choice(elem_cards)

        # ═══════════════════════════════════════════════════════════
        # PATH 3: Major Arcana (10%)
        # ═══════════════════════════════════════════════════════════
        major_arcana = self._get_major_arcana(deck)
        if major_arcana:
            return random.choice(major_arcana)

        return random.choice(deck)

    def _draw_present_card(self, deck: List[Dict], exclude: List[Dict] = None) -> Dict:
        """
        PRESENT: Current activation, what's happening now.

        If user has set an intention, the card selection is influenced by keywords.

        Strategy:
        - 70%: Current transits (fast-moving planets prioritized)
        - 20%: Wild draw (serendipity)
        - 10%: Challenging aspects (what needs attention)
        - OVERRIDE: If intention has strong keywords, weight toward matching themes
        """

        available_deck = [c for c in deck if c not in (exclude or [])]

        # ═══════════════════════════════════════════════════════════
        # INTENTION OVERRIDE: If user asked about specific themes
        # ═══════════════════════════════════════════════════════════
        if self.user_intention:
            intention_lower = self.user_intention.lower()

            # Map common question themes to card themes
            theme_keywords = {
                'career': ['ambition', 'achievement', 'mastery', 'work', 'success'],
                'love': ['love', 'relationship', 'partnership', 'union', 'connection'],
                'growth': ['growth', 'learning', 'wisdom', 'evolution', 'expansion'],
                'change': ['transformation', 'change', 'transition', 'breakthrough'],
                'decision': ['choice', 'decision', 'clarity', 'balance', 'judgment'],
                'challenge': ['challenge', 'conflict', 'tension', 'obstacle', 'test'],
            }

            # Check if intention matches any theme
            for theme, keywords in theme_keywords.items():
                if any(word in intention_lower for word in [theme]):
                    matching_cards = [
                        card for card in available_deck
                        if any(kw in card.get('keywords', '').lower() for kw in keywords)
                    ]
                    if matching_cards:
                        # 50% chance to use intention-matched card
                        if random.random() < 0.5:
                            return random.choice(matching_cards)

        # Continue with normal logic if no intention match
        roll = random.random()

        # [Rest of the original _draw_present_card logic remains the same]
        if roll < 0.70 and self.transits:
            fast_planets = ['Mars', 'Venus', 'Mercury', 'Moon']

            for transit in self.transits:
                if transit['transit_planet'] in fast_planets:
                    matching_cards = [
                        card for card in available_deck
                        if transit['transit_planet'] in card.get('planets', [])
                    ]
                    if matching_cards:
                        aspect_quality = transit.get('quality', 'flowing')
                        aspect_type = transit.get('aspect_type', '')

                        if aspect_quality in ['challenging', 'dynamic'] or aspect_type == 'Opposition':
                            intense = [c for c in matching_cards
                                       if any(k in c.get('keywords', '').lower()
                                              for k in ['tension', 'conflict', 'power', 'intensity'])]
                            if intense:
                                return random.choice(intense)

                        return random.choice(matching_cards)

            for transit in self.transits[:3]:
                matching_cards = [
                    card for card in available_deck
                    if transit['transit_planet'] in card.get('planets', [])
                ]
                if matching_cards:
                    return random.choice(matching_cards)

        elif roll < 0.90:
            return random.choice(available_deck)

        if self.transits:
            challenging = [
                t for t in self.transits
                if t.get('quality') in ['challenging', 'dynamic']
                   or t.get('aspect_type') in ['Square', 'Opposition']
            ]
            if challenging:
                growth_cards = [
                    card for card in available_deck
                    if any(k in card.get('keywords', '').lower()
                           for k in ['transformation', 'change', 'breakthrough', 'challenge'])
                ]
                if growth_cards:
                    return random.choice(growth_cards)

        return random.choice(available_deck)

    def _draw_future_card(self, deck: List[Dict], exclude: List[Dict] = None) -> Dict:
        """
        FUTURE: Potential, where energy is flowing, aspirations.

        Strategy:
        - 40%: Outer planets (Uranus, Neptune, Pluto - transformation)
        - 30%: Growth-oriented cards (positive keywords)
        - 30%: Wild draw (unknown future, serendipity)
        """

        available_deck = [c for c in deck if c not in (exclude or [])]
        roll = random.random()

        # ═══════════════════════════════════════════════════════════
        # PATH 1: Outer Planets (40%) - Transformational future
        # ═══════════════════════════════════════════════════════════
        if roll < 0.40:
            outer_planets = ['Uranus', 'Neptune', 'Pluto']

            for planet_name in outer_planets:
                if planet_name in self.planets:
                    matching_cards = [
                        card for card in available_deck
                        if planet_name in card.get('planets', [])
                    ]
                    if matching_cards:
                        return random.choice(matching_cards)

            # If no outer planet cards, look for transformation theme
            transformation_cards = [
                card for card in available_deck
                if any(k in card.get('keywords', '').lower()
                       for k in ['transformation', 'awakening', 'evolution', 'change'])
            ]
            if transformation_cards:
                return random.choice(transformation_cards)

        # ═══════════════════════════════════════════════════════════
        # PATH 2: Growth & Aspiration (30%)
        # ═══════════════════════════════════════════════════════════
        elif roll < 0.70:
            growth_cards = [
                card for card in available_deck
                if any(k in card.get('keywords', '').lower()
                       for k in ['growth', 'potential', 'opportunity', 'abundance',
                                 'expansion', 'wisdom', 'mastery', 'achievement'])
            ]
            if growth_cards:
                return random.choice(growth_cards)

        # ═══════════════════════════════════════════════════════════
        # PATH 3: Wild Draw (30%) - Unknown future
        # ═══════════════════════════════════════════════════════════
        return random.choice(available_deck)

    def _get_major_arcana(self, deck: List[Dict]) -> List[Dict]:
        """Helper: Get Major Arcana cards"""
        return [
            card for card in deck
            if '-' in card.get('card_number', '')
               and not any(suit in card.get('card_number', '')
                           for suit in ['Wands', 'Cups', 'Swords', 'Pentacles'])
        ]

    def generate_spread_narrative(self, past: Dict, present: Dict, future: Dict) -> str:
        """
        Generate cohesive narrative connecting the three cards.
        Uses natal chart themes and user intention to weave story.
        """

        dominant_elem = self.dominant_element

        narrative_styles = {
            'Fire': f"Your {past['title']} foundation ignites into {present['title']}'s passionate action, "
                    f"blazing toward {future['title']}'s bold potential.",

            'Earth': f"From {past['title']}'s stable ground, you build {present['title']}'s practical reality, "
                     f"cultivating {future['title']}'s tangible future.",

            'Air': f"The ideas of {past['title']} crystallize into {present['title']}'s clear communication, "
                   f"flowing toward {future['title']}'s intellectual expansion.",

            'Water': f"The emotional depths of {past['title']} merge with {present['title']}'s intuitive currents, "
                     f"leading to {future['title']}'s profound transformation."
        }

        base_narrative = narrative_styles.get(
            dominant_elem,
            f"From {past['title']} through {present['title']} toward {future['title']}, "
            f"your journey unfolds with cosmic precision."
        )

        if self.transits:
            top_transit = self.transits[0]
            base_narrative += f" Current {top_transit['transit_planet']} {top_transit['aspect_type']} " \
                              f"to your natal {top_transit['natal_planet']} activates this timeline."

        return base_narrative
