# deep_dive/services/cosmic_rhythm.py
"""
Cosmic Rhythm Analyzer - Current Celestial State

Shows what's happening in the sky RIGHT NOW.
No personal data required - this is "cosmic weather" for everyone.

Uses existing skyfield service for calculations.
"""

from django.utils import timezone
from typing import Dict, List


class CosmicRhythmAnalyzer:
    """
    Analyzes current cosmic conditions.
    Always available regardless of user data.
    """

    def __init__(self):
        self.now = timezone.now()

    def get_current_state(self) -> Dict:
        """
        Main method: Returns current cosmic state.

        Returns:
            {
                'moon': {...},
                'planetary_summary': {...},
                'dominant_elements': {...},
                'energy_summary': str,
                'timestamp': datetime
            }
        """
        try:
            # Import here to avoid circular imports
            from ..mystical.astronomical_svc import get_moon_phase, get_planetary_summary

            # Get moon phase using existing service
            moon_data = get_moon_phase()

            # Get planetary positions
            planetary_data = get_planetary_summary()

            # Analyze elemental distribution
            elements = self._analyze_elements(planetary_data)

            # Generate human-readable summary
            energy_summary = self._generate_energy_summary(moon_data, elements)

            return {
                'moon': moon_data,
                'planetary_summary': planetary_data,
                'dominant_elements': elements,
                'energy_summary': energy_summary,
                'timestamp': self.now,
                'visual_markers': self._get_visual_markers(moon_data, elements)
            }

        except Exception as e:
            import traceback
            print(f"Cosmic rhythm analysis error: {e}")
            print(traceback.format_exc())
            return self._fallback_state()

    def _analyze_elements(self, planetary_data: Dict) -> Dict:
        """
        Analyze distribution of elements based on current planetary positions.

        Elements:
        - Fire (Aries, Leo, Sagittarius)
        - Earth (Taurus, Virgo, Capricorn)
        - Air (Gemini, Libra, Aquarius)
        - Water (Cancer, Scorpio, Pisces)
        """
        element_map = {
            'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
            'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
            'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
            'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
        }

        element_counts = {'fire': 0, 'earth': 0, 'air': 0, 'water': 0}

        # Count planets in each element
        # Your service returns 'planetary_positions' not 'planets'
        if planetary_data and 'planetary_positions' in planetary_data:
            for planet_data in planetary_data['planetary_positions']:
                sign = planet_data.get('sign', '')
                element = element_map.get(sign)
                if element:
                    element_counts[element] += 1

        # Find dominant elements
        max_count = max(element_counts.values()) if element_counts.values() else 0
        dominant = [elem for elem, count in element_counts.items() if count == max_count and count > 0]

        return {
            'counts': element_counts,
            'dominant': dominant,
            'total_planets': sum(element_counts.values())
        }

    def _generate_energy_summary(self, moon_data: Dict, elements: Dict) -> str:
        """
        Generate human-readable cosmic energy summary.
        """
        summaries = []

        # Moon phase energy
        if moon_data:
            phase = moon_data.get('phase_name', '').lower()
            if 'new' in phase:
                summaries.append("New beginnings energy")
            elif 'full' in phase:
                summaries.append("Culmination and clarity")
            elif 'waxing' in phase:
                summaries.append("Building momentum")
            elif 'waning' in phase:
                summaries.append("Release and reflection")

        # Elemental energy
        dominant = elements.get('dominant', [])
        if 'fire' in dominant:
            summaries.append("active fire energy")
        if 'earth' in dominant:
            summaries.append("grounding earth influence")
        if 'air' in dominant:
            summaries.append("mental air currents")
        if 'water' in dominant:
            summaries.append("emotional water flow")

        return " • ".join(summaries) if summaries else "Balanced cosmic energy"

    def _get_visual_markers(self, moon_data: Dict, elements: Dict) -> Dict:
        """
        Data for visual representation (icons, colors, etc.)
        """
        return {
            'moon_emoji': moon_data.get('emoji', '🌙') if moon_data else '🌙',
            'dominant_element_emoji': self._get_element_emoji(elements.get('dominant', [])),
            'energy_color': self._get_energy_color(elements.get('dominant', []))
        }

    def _get_element_emoji(self, dominant_elements: List[str]) -> str:
        """Get emoji representation of dominant element"""
        emoji_map = {
            'fire': '🔥',
            'earth': '🌍',
            'air': '💨',
            'water': '💧'
        }
        if dominant_elements:
            return emoji_map.get(dominant_elements[0], '✨')
        return '✨'

    def _get_energy_color(self, dominant_elements: List[str]) -> str:
        """Get color representation for UI"""
        color_map = {
            'fire': 'red',
            'earth': 'green',
            'air': 'blue',
            'water': 'cyan'
        }
        if dominant_elements:
            return color_map.get(dominant_elements[0], 'purple')
        return 'purple'

    def get_visualization_data(self) -> Dict:
        """
        Returns data formatted for simple visualization.
        Used when user has minimal journal data.
        """
        state = self.get_current_state()

        return {
            'type': 'cosmic_state',
            'labels': ['Fire', 'Earth', 'Air', 'Water'],
            'data': [
                state['dominant_elements']['counts']['fire'],
                state['dominant_elements']['counts']['earth'],
                state['dominant_elements']['counts']['air'],
                state['dominant_elements']['counts']['water']
            ],
            'moon_phase': state['moon'].get('phase_name', 'Unknown') if state['moon'] else 'Unknown',
            'moon_emoji': state['moon'].get('emoji', '🌙') if state['moon'] else '🌙',
            'summary': state['energy_summary']
        }

    def _fallback_state(self) -> Dict:
        """Fallback state if calculation fails"""
        return {
            'moon': {'phase_name': 'Unknown', 'emoji': '🌙'},
            'planetary_summary': None,
            'dominant_elements': {
                'counts': {'fire': 0, 'earth': 0, 'air': 0, 'water': 0},
                'dominant': [],
                'total_planets': 0
            },
            'energy_summary': 'Cosmic data temporarily unavailable',
            'timestamp': self.now,
            'visual_markers': {
                'moon_emoji': '🌙',
                'dominant_element_emoji': '✨',
                'energy_color': 'purple'
            }
        }


# deep_dive/services/journal_rhythm.py
"""
Journal Rhythm Analyzer - Discovers patterns in user's journaling behavior

Analyzes:
- Frequency patterns (when they journal)
- Tag patterns (what they write about)
- Emotional waves (sentiment over time)
- Volume patterns (writing length)

Gracefully handles small datasets.
"""

from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta, datetime
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import json


class JournalRhythmAnalyzer:
    """
    Analyzes patterns in user's journal entries.

    Usage:
        analyzer = JournalRhythmAnalyzer(user)
        patterns = analyzer.analyze()
    """

    def __init__(self, user, days_back: int = 90):
        self.user = user
        self.days_back = days_back
        self.now = timezone.now()
        self.cutoff = self.now - timedelta(days=days_back)

        # Import here to avoid circular imports
        from journal.models import JournalEntry

        # Fetch all relevant entries once
        self.entries = JournalEntry.objects.filter(
            user=user,
            created_at__gte=self.cutoff
        ).prefetch_related('tags').order_by('created_at')

        self.entry_count = self.entries.count()

    def analyze(self) -> Dict:
        """
        Main analysis method.
        Returns different insights based on entry count.
        """
        if self.entry_count < 3:
            return self._minimal_analysis()
        elif self.entry_count < 10:
            return self._emerging_analysis()
        elif self.entry_count < 30:
            return self._established_analysis()
        else:
            return self._rich_analysis()

    def _minimal_analysis(self) -> Dict:
        """Analysis for 0-2 entries"""
        return {
            'level': 'minimal',
            'entry_count': self.entry_count,
            'message': f"You have {self.entry_count} entries. Keep journaling to discover your patterns!",
            'insights': []
        }

    def _emerging_analysis(self) -> Dict:
        """Analysis for 3-9 entries"""
        insights = []

        # Basic frequency insight
        days_with_entries = set(entry.created_at.date() for entry in self.entries)
        insights.append(f"You've journaled on {len(days_with_entries)} different days")

        # Top tags
        tag_freq = self._get_tag_frequency()
        if tag_freq:
            top_tag = tag_freq[0]
            insights.append(f"Most common theme: {top_tag[0]} ({top_tag[1]} times)")

        # Time of day preference
        hour_dist = self._get_hour_distribution()
        if hour_dist:
            peak_hour = max(hour_dist.items(), key=lambda x: x[1])
            time_label = self._get_time_label(peak_hour[0])
            insights.append(f"You journal most in the {time_label}")

        return {
            'level': 'emerging',
            'entry_count': self.entry_count,
            'insights': insights,
            'top_tags': tag_freq[:3],
            'message': 'Your journaling pattern is starting to emerge'
        }

    def _established_analysis(self) -> Dict:
        """Analysis for 10-29 entries"""
        insights = []

        # Frequency pattern
        avg_per_week = self._calculate_weekly_average()
        insights.append(f"You journal an average of {avg_per_week:.1f} times per week")

        # Consistency insight
        consistency = self._analyze_consistency()
        insights.append(consistency)

        # Tag patterns
        tag_freq = self._get_tag_frequency()
        if len(tag_freq) >= 2:
            insights.append(f"Your main themes: {tag_freq[0][0]} and {tag_freq[1][0]}")

        # Day of week pattern
        dow_pattern = self._analyze_day_of_week()
        if dow_pattern:
            insights.append(dow_pattern)

        return {
            'level': 'established',
            'entry_count': self.entry_count,
            'insights': insights,
            'top_tags': tag_freq[:5],
            'weekly_average': avg_per_week,
            'frequency_data': self._get_weekly_frequency_data(),
            'message': 'Clear patterns are emerging in your journaling'
        }

    def _rich_analysis(self) -> Dict:
        """Analysis for 30+ entries"""
        established = self._established_analysis()

        # Add advanced insights
        advanced_insights = []

        # Emotional wave detection
        emotional_trend = self._detect_emotional_trend()
        if emotional_trend:
            advanced_insights.append(emotional_trend)

        # Volume pattern
        volume_pattern = self._analyze_volume_pattern()
        if volume_pattern:
            advanced_insights.append(volume_pattern)

        # Clustering detection
        cluster_insight = self._detect_clustering()
        if cluster_insight:
            advanced_insights.append(cluster_insight)

        established['insights'].extend(advanced_insights)
        established['level'] = 'rich'
        established['message'] = 'Deep pattern insights available'
        established['advanced_data'] = {
            'tag_correlations': self._get_tag_correlations(),
            'monthly_distribution': self._get_monthly_distribution()
        }

        return established

    # ========================================
    # HELPER METHODS - Pattern Detection
    # ========================================

    def _get_tag_frequency(self) -> List[Tuple[str, int]]:
        """Return tags sorted by frequency"""
        tag_counts = Counter()
        for entry in self.entries:
            for tag in entry.tags.all():
                tag_counts[tag.name] += 1
        return tag_counts.most_common()

    def _get_hour_distribution(self) -> Dict[int, int]:
        """Count entries by hour of day"""
        hour_counts = defaultdict(int)
        for entry in self.entries:
            hour = entry.created_at.hour
            hour_counts[hour] += 1
        return dict(hour_counts)

    def _get_time_label(self, hour: int) -> str:
        """Convert hour to time-of-day label"""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def _calculate_weekly_average(self) -> float:
        """Calculate average entries per week"""
        days_span = (self.now - self.cutoff).days
        weeks = days_span / 7
        return self.entry_count / weeks if weeks > 0 else 0

    def _analyze_consistency(self) -> str:
        """Analyze journaling consistency"""
        dates = [entry.created_at.date() for entry in self.entries]
        if len(dates) < 2:
            return "Building consistency"

        # Calculate average gap between entries
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        avg_gap = sum(gaps) / len(gaps)

        if avg_gap <= 3:
            return "Very consistent journaling rhythm"
        elif avg_gap <= 7:
            return "Regular journaling pattern"
        else:
            return "Journaling in bursts"

    def _analyze_day_of_week(self) -> str:
        """Find favorite day of week for journaling"""
        dow_counts = Counter(entry.created_at.weekday() for entry in self.entries)
        if not dow_counts:
            return ""

        most_common_dow, count = dow_counts.most_common(1)[0]
        if count >= 3:  # Only mention if significant
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            return f"You often journal on {days[most_common_dow]}s"
        return ""

    def _detect_emotional_trend(self) -> str:
        """Detect overall emotional trend from tags"""
        # Define emotional valence of common tags
        positive_tags = {'happy', 'grateful', 'excited', 'inspired', 'motivated', 'joy', 'peaceful', 'content'}
        negative_tags = {'anxious', 'stressed', 'tired', 'frustrated', 'sad', 'overwhelmed', 'burnout', 'angry'}

        positive_count = 0
        negative_count = 0

        for entry in self.entries:
            for tag in entry.tags.all():
                tag_lower = tag.name.lower()
                if tag_lower in positive_tags:
                    positive_count += 1
                elif tag_lower in negative_tags:
                    negative_count += 1

        if positive_count > negative_count * 1.5:
            return "Your entries lean toward positive themes"
        elif negative_count > positive_count * 1.5:
            return "You often process challenging emotions in your journal"
        return ""

    def _analyze_volume_pattern(self) -> str:
        """Analyze writing volume patterns"""
        volumes = [len(entry.content.split()) for entry in self.entries]
        if not volumes:
            return ""

        avg_words = sum(volumes) / len(volumes)

        if avg_words > 200:
            return "You write detailed, reflective entries"
        elif avg_words > 100:
            return "You maintain a balanced writing length"
        else:
            return "You prefer concise, focused entries"

    def _detect_clustering(self) -> str:
        """Detect if entries come in clusters"""
        dates = sorted([entry.created_at.date() for entry in self.entries])
        if len(dates) < 5:
            return ""

        # Find clusters (entries within 2 days)
        clusters = []
        current_cluster = [dates[0]]

        for i in range(1, len(dates)):
            if (dates[i] - current_cluster[-1]).days <= 2:
                current_cluster.append(dates[i])
            else:
                if len(current_cluster) >= 3:
                    clusters.append(current_cluster)
                current_cluster = [dates[i]]

        if len(current_cluster) >= 3:
            clusters.append(current_cluster)

        if len(clusters) >= 2:
            return "You tend to journal in focused bursts"
        return ""

    def _get_tag_correlations(self) -> List[Tuple[str, str, int]]:
        """Find tags that often appear together"""
        tag_pairs = Counter()

        for entry in self.entries:
            tags = [tag.name for tag in entry.tags.all()]
            if len(tags) >= 2:
                # Count all pairs
                for i in range(len(tags)):
                    for j in range(i + 1, len(tags)):
                        pair = tuple(sorted([tags[i], tags[j]]))
                        tag_pairs[pair] += 1

        # Return top correlations
        return [(pair[0], pair[1], count) for pair, count in tag_pairs.most_common(3)]

    def _get_monthly_distribution(self) -> Dict[str, int]:
        """Count entries per month"""
        monthly = defaultdict(int)
        for entry in self.entries:
            month_key = entry.created_at.strftime('%Y-%m')
            monthly[month_key] += 1
        return dict(monthly)

    # ========================================
    # VISUALIZATION DATA
    # ========================================

    def get_frequency_chart_data(self) -> Dict:
        """
        Return data for Chart.js frequency visualization.
        Shows entries per week over time.
        """
        weekly_data = self._get_weekly_frequency_data()

        return {
            'type': 'frequency',
            'labels': [item['week_label'] for item in weekly_data],
            'data': [item['count'] for item in weekly_data],
            'average': self._calculate_weekly_average()
        }

    def _get_weekly_frequency_data(self) -> List[Dict]:
        """Group entries by week"""
        weekly_counts = defaultdict(int)

        for entry in self.entries:
            # Get week start (Monday)
            week_start = entry.created_at.date() - timedelta(days=entry.created_at.weekday())
            weekly_counts[week_start] += 1

        # Convert to sorted list
        weeks = sorted(weekly_counts.keys())
        return [
            {
                'week_start': week,
                'week_label': week.strftime('%b %d'),
                'count': weekly_counts[week]
            }
            for week in weeks
        ]

    def get_advanced_chart_data(self) -> Dict:
        """
        Advanced visualization data for rich-level users.
        Includes frequency + tag distribution.
        """
        return {
            'type': 'advanced',
            'frequency': self.get_frequency_chart_data(),
            'tag_distribution': {
                'labels': [tag[0] for tag in self._get_tag_frequency()[:5]],
                'data': [tag[1] for tag in self._get_tag_frequency()[:5]]
            },
            'hour_distribution': {
                'labels': [f"{h:02d}:00" for h in range(24)],
                'data': [self._get_hour_distribution().get(h, 0) for h in range(24)]
            }
        }