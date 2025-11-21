# deep_dive/services/mystical/cosmic_alignments_service.py
"""
Cosmic Alignments Analyzer - Cross-Referenced Mystical Insights

Analyzes supplementary mystical patterns that combine multiple data sources:
- Tarot draw patterns + Journal sentiment
- Element energy + Emotional themes
- Moon-Planet cross-correlations
- Sacred milestones and synchronicities

This is the "Advanced Insights" mystical layer - not repeating what's
already shown in Moon/Planetary correlation sections.
"""

from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict, Counter
from typing import Dict, List, Optional


class CosmicAlignmentsAnalyzer:
    """
    Analyzes cross-referenced mystical patterns across journal, tarot, and cosmos.

    Usage:
        analyzer = CosmicAlignmentsAnalyzer(user)
        alignments = analyzer.analyze()
    """

    def __init__(self, user, days_back: int = 90):
        self.user = user
        self.days_back = days_back
        self.now = timezone.now()
        # Use start of day for cutoff to include all of today
        self.cutoff = (self.now - timedelta(days=days_back)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Import models
        from journal.models import JournalEntry
        from deep_dive.models import TarotCardDraw

        # Fetch data (including today)
        self.entries = JournalEntry.objects.filter(
            user=user,
            created_at__gte=self.cutoff
        ).prefetch_related('tags').order_by('created_at')

        self.tarot_draws = TarotCardDraw.objects.filter(
            user=user,
            drawn_at__gte=self.cutoff
        ).order_by('drawn_at')

        self.entry_count = self.entries.count()
        self.tarot_count = self.tarot_draws.count()

    def analyze(self) -> Dict:
        """
        Main analysis method.
        Returns different insights based on available data.
        """
        if self.entry_count < 3:
            return {
                'has_data': False,
                'message': 'Start journaling to unlock cosmic alignment insights'
            }

        return {
            'has_data': True,
            'tarot_journal_sync': self._analyze_tarot_journal_sync(),
            'sentiment_cosmic_patterns': self._analyze_sentiment_cosmic(),
            'cross_correlations': self._analyze_cross_correlations(),
            'sacred_milestones': self._get_sacred_milestones(),
            'insights': self._generate_insights()
        }

    # ========================================
    # TAROT-JOURNAL SYNCHRONICITY
    # ========================================

    def _analyze_tarot_journal_sync(self) -> Dict:
        if self.tarot_count == 0:
            return {
                'has_tarot': False,
                'message': 'Draw daily tarot cards to see synchronicities'
            }

        journal_dates = set(entry.created_at.date() for entry in self.entries)
        tarot_dates = set(draw.drawn_at.date() for draw in self.tarot_draws)
        both_dates = journal_dates & tarot_dates

        sync_rate = len(both_dates) / len(tarot_dates) if tarot_dates else 0
        sync_percentage = sync_rate * 100

        all_card_distribution = self._get_all_card_distribution()
        card_sentiment = self._get_card_sentiment_correlation()
        archetype_dist = self._get_archetype_distribution()

        return {
            'has_tarot': True,
            'total_draws': self.tarot_count,
            'total_entries': self.entry_count,
            'sync_days': len(both_dates),
            'sync_rate': sync_rate,
            'sync_percentage': int(sync_percentage),
            'sync_description': f"{len(both_dates)} of {len(tarot_dates)} tarot draws happened on journal days",
            'all_card_distribution': all_card_distribution,
            'card_sentiment': card_sentiment,
            'archetype_distribution': archetype_dist
        }
    def _get_all_card_distribution(self) -> Dict:
        """Get distribution of ALL tarot cards drawn, regardless of journal entries"""
        card_counts = {
            'major_arcana': 0,
            'cups': 0,
            'wands': 0,
            'swords': 0,
            'pentacles': 0
        }

        for draw in self.tarot_draws:
            card_type = self._categorize_card(draw.card_name, draw.card_number)
            if card_type in card_counts:
                card_counts[card_type] += 1

        return {
            card_type: {
                'count': count,
                'emoji': {
                    'major_arcana': '🎴',
                    'cups': '💧',
                    'wands': '🔥',
                    'swords': '⚔️',
                    'pentacles': '🪙'
                }.get(card_type, '✨')
            }
            for card_type, count in card_counts.items()
            if count > 0
        }

    def _get_card_sentiment_correlation(self) -> Dict:
        """
        Correlate tarot cards with journal sentiment on same day.

        Sentiment scale: -0.9 (very negative) to +0.9 (very positive)
        Based on Tag.sentiment_score range
        """
        correlations = {
            'major_arcana': [],
            'cups': [],
            'wands': [],
            'swords': [],
            'pentacles': []
        }

        for draw in self.tarot_draws:
            # Get journal entry from same day
            same_day_entries = self.entries.filter(
                created_at__date=draw.drawn_at.date()
            )

            if not same_day_entries.exists():
                continue

            # Calculate sentiment for that day's entries
            day_sentiment = self._calculate_entries_sentiment(same_day_entries)

            # Categorize card
            card_type = self._categorize_card(draw.card_name, draw.card_number)
            if card_type in correlations:
                correlations[card_type].append(day_sentiment)

        # Calculate averages (only include types with meaningful sample size)
        MINIMUM_SAMPLE_SIZE = 3  # Need at least 3 cards to draw conclusions

        return {
            card_type: {
                'avg_sentiment': sum(sentiments) / len(sentiments) if sentiments else 0,
                'count': len(sentiments),
                'has_meaningful_data': len(sentiments) >= MINIMUM_SAMPLE_SIZE
            }
            for card_type, sentiments in correlations.items()
            if sentiments  # Only include types with data
        }

    def _categorize_card(self, card_name: str, card_number: str) -> str:
        """
        Categorize tarot card by type.

        Major Arcana: Cards 0-21 (Roman numerals or special names)
        Minor Arcana Suits: Based on card name
        """
        # Normalize strings for comparison
        name_lower = card_name.lower()
        number_upper = card_number.upper().strip()

        # Major Arcana - Check card number first (most reliable)
        major_indicators = ['0', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII',
                            'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV',
                            'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX', 'XXI']

        # Also check for special Major Arcana names
        major_names = ['fool', 'magician', 'high priestess', 'empress', 'emperor',
                       'hierophant', 'lovers', 'chariot', 'strength', 'hermit',
                       'wheel of fortune', 'justice', 'hanged man', 'death',
                       'temperance', 'devil', 'tower', 'star', 'moon', 'sun',
                       'judgement', 'world']

        if any(number_upper == m or number_upper.startswith(m + ' ') for m in major_indicators):
            return 'major_arcana'

        if any(major in name_lower for major in major_names):
            return 'major_arcana'

        # Minor Arcana - Suit-based (check card name)
        if 'cup' in name_lower:
            return 'cups'
        elif 'wand' in name_lower or 'rod' in name_lower or 'stave' in name_lower:
            return 'wands'
        elif 'sword' in name_lower:
            return 'swords'
        elif 'pentacle' in name_lower or 'coin' in name_lower or 'disk' in name_lower:
            return 'pentacles'

        # Default to major arcana if unclear
        return 'major_arcana'

    def _get_archetype_distribution(self) -> Dict:
        """Count Major vs Minor Arcana draws"""
        major_count = 0
        minor_count = 0

        for draw in self.tarot_draws:
            card_type = self._categorize_card(draw.card_name, draw.card_number)
            if card_type == 'major_arcana':
                major_count += 1
            else:
                minor_count += 1

        total = major_count + minor_count
        return {
            'major_arcana': {
                'count': major_count,
                'percentage': (major_count / total * 100) if total else 0
            },
            'minor_arcana': {
                'count': minor_count,
                'percentage': (minor_count / total * 100) if total else 0
            }
        }

    # ========================================
    # SENTIMENT-COSMIC PATTERNS
    # ========================================

    def _analyze_sentiment_cosmic(self) -> Dict:
        from ..mystical.astronomical_svc import get_planetary_summary
        current_planetary = get_planetary_summary()
        current_element = current_planetary.get('dominant_element', '').lower()

        element_sentiment = self._get_sentiment_by_element()
        overall_sentiment = self._calculate_entries_sentiment(self.entries)

        all_elements = {
            'fire': element_sentiment.get('fire', {'avg': 0, 'count': 0, 'has_meaningful_data': False, 'emoji': '🔥'}),
            'earth': element_sentiment.get('earth', {'avg': 0, 'count': 0, 'has_meaningful_data': False, 'emoji': '🌍'}),
            'air': element_sentiment.get('air', {'avg': 0, 'count': 0, 'has_meaningful_data': False, 'emoji': '💨'}),
            'water': element_sentiment.get('water', {'avg': 0, 'count': 0, 'has_meaningful_data': False, 'emoji': '💧'})
        }

        for element in all_elements:
            all_elements[element]['is_current'] = (element == current_element)
            # DEBUG: Verify current element marking

        return {
            'element_sentiment': all_elements,
            'current_element': current_element,
            'overall_sentiment': overall_sentiment,
            'sentiment_label': self._get_sentiment_label(overall_sentiment),
            'has_data': any(data['count'] > 0 for data in all_elements.values())
        }

    def _get_sentiment_by_element(self) -> Dict:
        MINIMUM_SAMPLE_SIZE = 3
        element_sentiments = {'fire': [], 'earth': [], 'air': [], 'water': []}

        try:
            from ..mystical.astronomical_svc import get_planetary_summary_for_date
            for entry in self.entries:
                try:
                    planetary = get_planetary_summary_for_date(entry.created_at)
                    element = planetary.get('dominant_element', '').lower()
                    if element in element_sentiments:
                        sentiment = self._calculate_entry_sentiment(entry)
                        if sentiment is not None:
                            element_sentiments[element].append(sentiment)
                except:
                    continue
        except ImportError:
            from ..mystical.astronomical_svc import get_planetary_summary
            current_element = get_planetary_summary().get('dominant_element', 'earth').lower()
            for entry in self.entries:
                sentiment = self._calculate_entry_sentiment(entry)
                if sentiment is not None:
                    element_sentiments[current_element].append(sentiment)

        return {
            element: {
                'avg': sum(scores) / len(scores) if scores else 0,
                'count': len(scores),
                'has_meaningful_data': len(scores) >= MINIMUM_SAMPLE_SIZE,
                'emoji': {'fire': '🔥', 'earth': '🌍', 'air': '💨', 'water': '💧'}.get(element, '✨')
            }
            for element, scores in element_sentiments.items()
            if scores
        }

    def _calculate_entry_sentiment(self, entry) -> Optional[float]:
        """Calculate sentiment for a single entry based on tags"""
        tags = entry.tags.all()
        if not tags:
            return None

        scores = [tag.sentiment_score for tag in tags]
        return sum(scores) / len(scores)

    def _calculate_entries_sentiment(self, entries) -> float:
        """Calculate average sentiment across multiple entries"""
        all_scores = []
        for entry in entries:
            sentiment = self._calculate_entry_sentiment(entry)
            if sentiment is not None:
                all_scores.append(sentiment)

        return sum(all_scores) / len(all_scores) if all_scores else 0

    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score <= -0.5:
            return 'Very Negative'
        elif score <= -0.2:
            return 'Negative'
        elif score <= 0.2:
            return 'Neutral'
        elif score <= 0.5:
            return 'Positive'
        else:
            return 'Very Positive'

    # ========================================
    # CROSS-CORRELATIONS (Moon + Planets)
    # ========================================

    def _analyze_cross_correlations(self) -> Dict:
        """
        Find interesting Moon-Planet combinations in journal data.
        This is supplementary to individual Moon/Planet sections.
        """
        # Note: Requires historical data functions
        # If not available, return minimal data

        try:
            from ..mystical.astronomical_svc import get_moon_phase_for_date, get_planetary_summary_for_date

            # Group entries by moon phase + dominant element
            combinations = defaultdict(list)

            for entry in self.entries:
                try:
                    moon = get_moon_phase_for_date(entry.created_at)
                    planetary = get_planetary_summary_for_date(entry.created_at)

                    moon_phase = moon.get('phase', 'Unknown')
                    element = planetary.get('dominant_element', 'Unknown')

                    combo_key = f"{moon_phase}_{element}"
                    combinations[combo_key].append(entry)
                except:
                    continue

            # Find most common combinations
            top_combos = sorted(
                combinations.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:3]

            return {
                'has_data': len(top_combos) > 0,
                'top_combinations': [
                    {
                        'moon_phase': combo[0].split('_')[0],
                        'element': combo[0].split('_')[1],
                        'count': len(combo[1])
                    }
                    for combo in top_combos
                ]
            }

        except ImportError:
            # If historical functions don't exist yet
            return {
                'has_data': False,
                'top_combinations': []
            }

    # ========================================
    # SACRED MILESTONES
    # ========================================

    def _get_sacred_milestones(self) -> List[str]:
        """Detect mystical milestones in journaling practice"""
        milestones = []

        # Complete lunar cycles
        lunar_cycle_days = 29.5
        days_journaling = (self.now - self.entries.first().created_at).days if self.entries else 0
        complete_cycles = int(days_journaling / lunar_cycle_days)

        if complete_cycles >= 1:
            milestones.append(
                f"Journaled through {complete_cycles} complete lunar cycle{'s' if complete_cycles > 1 else ''}")

        # New moon rituals (entries on new moon days)
        new_moon_entries = self._count_moon_phase_entries('New Moon')
        if new_moon_entries >= 3:
            milestones.append(f"{new_moon_entries} new moon journal rituals completed")

        # Full moon reflections
        full_moon_entries = self._count_moon_phase_entries('Full Moon')
        if full_moon_entries >= 3:
            milestones.append(f"{full_moon_entries} full moon reflection sessions")

        # Tarot + Journal synchronicity
        if self.tarot_count > 0:
            sync_rate = self._analyze_tarot_journal_sync()['sync_rate']
            if sync_rate >= 0.6:
                milestones.append(f"Strong tarot-journal synchronicity ({int(sync_rate * 100)}% of draws)")

        # Consistent practice (7+ days in a row)
        streak = self._find_longest_streak()
        if streak >= 7:
            milestones.append(f"{streak}-day journaling streak achieved")

        return milestones

    def _count_moon_phase_entries(self, phase_name: str) -> int:
        """Count entries that occurred during specific moon phase"""
        try:
            from ..mystical.astronomical_svc import get_moon_phase_for_date

            count = 0
            for entry in self.entries:
                try:
                    moon = get_moon_phase_for_date(entry.created_at)
                    if moon.get('phase', '') == phase_name:
                        count += 1
                except:
                    continue
            return count
        except ImportError:
            # If function doesn't exist, return 0
            return 0

    def _find_longest_streak(self) -> int:
        """Find longest consecutive days with journal entries"""
        if not self.entries:
            return 0

        dates = sorted(set(entry.created_at.date() for entry in self.entries))

        longest = 1
        current = 1

        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1

        return longest

    # ========================================
    # INSIGHT GENERATION
    # ========================================

    def _generate_insights(self) -> List[str]:
        """
        Generate human-readable insights from all correlations.

        Only generate insights when:
        - Sample size is meaningful (3+ data points)
        - Pattern is statistically noticeable (not just noise)

        Sentiment thresholds:
        - Strong positive: > +0.3
        - Moderate positive: +0.15 to +0.3
        - Neutral: -0.15 to +0.15
        - Moderate negative: -0.3 to -0.15
        - Strong negative: < -0.3
        """
        insights = []

        # Tarot-sentiment insight (requires 3+ cards of that type)
        tarot_sync = self._analyze_tarot_journal_sync()
        if tarot_sync['has_tarot'] and tarot_sync['card_sentiment']:
            sentiments = tarot_sync['card_sentiment']

            # Only consider card types with meaningful sample size
            meaningful_sentiments = {
                k: v for k, v in sentiments.items()
                if v.get('has_meaningful_data', False)
            }

            if meaningful_sentiments:
                # Find most negative suit (if strongly negative)
                most_negative = min(meaningful_sentiments.items(), key=lambda x: x[1]['avg_sentiment'])

                if most_negative[1]['avg_sentiment'] < -0.3:
                    suit_name = most_negative[0].replace('_', ' ').title()
                    count = most_negative[1]['count']
                    insights.append(f"{suit_name} cards appear during emotional processing ({count} draws)")

                # Find most positive suit (if strongly positive)
                most_positive = max(meaningful_sentiments.items(), key=lambda x: x[1]['avg_sentiment'])

                if most_positive[1]['avg_sentiment'] > 0.3:
                    suit_name = most_positive[0].replace('_', ' ').title()
                    count = most_positive[1]['count']
                    insights.append(f"{suit_name} cards align with uplifting energy ({count} draws)")

        # Element-sentiment insight (requires 3+ entries per element)
        sentiment_cosmic = self._analyze_sentiment_cosmic()
        if sentiment_cosmic['has_data']:
            element_data = sentiment_cosmic['element_sentiment']

            # Only consider elements with meaningful data
            meaningful_elements = {
                k: v for k, v in element_data.items()
                if v.get('has_meaningful_data', False)
            }

            if meaningful_elements:
                # Find most positive element (if noticeably positive)
                most_positive = max(meaningful_elements.items(), key=lambda x: x[1]['avg'])

                if most_positive[1]['avg'] > 0.2:  # Noticeable positive shift
                    elem_name = most_positive[0].title()
                    count = most_positive[1]['count']
                    insights.append(f"Your mood lifts on {elem_name} energy days ({count} entries)")

                # Find most negative element (if noticeably negative)
                most_negative = min(meaningful_elements.items(), key=lambda x: x[1]['avg'])

                if most_negative[1]['avg'] < -0.2:  # Noticeable negative shift
                    elem_name = most_negative[0].title()
                    count = most_negative[1]['count']
                    insights.append(f"{elem_name} energy days bring deeper processing ({count} entries)")

        # Cross-correlation insight (requires meaningful pattern)
        cross = self._analyze_cross_correlations()
        if cross['has_data'] and cross['top_combinations']:
            top = cross['top_combinations'][0]
            # Only mention if it's a strong pattern (5+ occurrences)
            if top['count'] >= 5:
                insights.append(
                    f"You journal most during {top['moon_phase']} with {top['element']} energy ({top['count']}× pattern)")

        return insights