# deep_dive/services/moon_correlation.py
"""
Moon Phase Correlation Analyzer

Analyzes relationship between moon phases and journaling patterns.
Shows:
- Which moon phases user journals most during
- Dominant emotions/tags during each phase
- Correlation strength and insights
"""

from django.utils import timezone
from datetime import timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import logging
logging.disable(logging.CRITICAL)
# Set up logger
logger = logging.getLogger(__name__)


class MoonPhaseCorrelator:
    """
    Correlates journal entries with moon phases.
    Reveals lunar patterns in journaling behavior.
    """

    # Moon phase categories and their meanings
    MOON_PHASES = {
        'new_moon': {
            'name': 'New Moon',
            'emoji': '🌑',
            'degrees': (0, 45),
            'energy': 'New beginnings, intention setting, introspection',
            'color': 'from-slate-800 to-slate-900'
        },
        'waxing_crescent': {
            'name': 'Waxing Crescent',
            'emoji': '🌒',
            'degrees': (45, 90),
            'energy': 'Growth, momentum building, hope',
            'color': 'from-indigo-900 to-slate-800'
        },
        'first_quarter': {
            'name': 'First Quarter',
            'emoji': '🌓',
            'degrees': (90, 135),
            'energy': 'Action, decisions, overcoming challenges',
            'color': 'from-blue-900 to-indigo-900'
        },
        'waxing_gibbous': {
            'name': 'Waxing Gibbous',
            'emoji': '🌔',
            'degrees': (135, 180),
            'energy': 'Refinement, analysis, anticipation',
            'color': 'from-cyan-900 to-blue-900'
        },
        'full_moon': {
            'name': 'Full Moon',
            'emoji': '🌕',
            'degrees': (180, 225),
            'energy': 'Culmination, clarity, emotional intensity',
            'color': 'from-yellow-900 to-orange-900'
        },
        'waning_gibbous': {
            'name': 'Waning Gibbous',
            'emoji': '🌖',
            'degrees': (225, 270),
            'energy': 'Gratitude, sharing, reflection',
            'color': 'from-orange-900 to-red-900'
        },
        'last_quarter': {
            'name': 'Last Quarter',
            'emoji': '🌗',
            'degrees': (270, 315),
            'energy': 'Release, letting go, closure',
            'color': 'from-purple-900 to-pink-900'
        },
        'waning_crescent': {
            'name': 'Waning Crescent',
            'emoji': '🌘',
            'degrees': (315, 360),
            'energy': 'Rest, surrender, wisdom integration',
            'color': 'from-slate-900 to-slate-800'
        }
    }

    def __init__(self, user, days_back: int = 90):
        self.user = user
        self.days_back = days_back
        self.now = timezone.now()
        self.cutoff = self.now - timedelta(days=days_back)

        # Import here to avoid circular imports
        from journal.models import JournalEntry

        # Fetch entries with moon phase data
        self.entries = JournalEntry.objects.filter(
            user=user,
            created_at__gte=self.cutoff
        ).prefetch_related('tags').order_by('created_at')

        self.entry_count = self.entries.count()

        logger.info(f"🌙 MoonPhaseCorrelator initialized for user {user.id}")
        logger.info(f"📊 Found {self.entry_count} entries between {self.cutoff} and {self.now}")

    def analyze(self) -> Dict:
        """
        Main analysis method.
        Returns moon phase correlation insights.
        """
        if self.entry_count < 3:
            logger.warning(f"⚠️ Not enough entries for analysis: {self.entry_count} < 3")
            return self._minimal_analysis()

        logger.info(f"🔍 Starting moon phase correlation analysis...")

        # Calculate moon phase for each entry
        entries_by_phase = self._categorize_by_moon_phase()

        # Analyze patterns
        phase_stats = self._calculate_phase_statistics(entries_by_phase)
        dominant_phases = self._find_dominant_phases(phase_stats)
        insights = self._generate_insights(phase_stats, dominant_phases)

        logger.info(f"✅ Analysis complete. Dominant phases: {[p[0] for p in dominant_phases]}")

        return {
            'has_data': True,
            'total_entries': self.entry_count,
            'phase_statistics': phase_stats,
            'dominant_phases': dominant_phases,
            'insights': insights,
            'visualization_data': self._prepare_visualization_data(phase_stats)
        }

    def _categorize_by_moon_phase(self) -> Dict:
        """
        Group entries by moon phase when they were written.
        Uses existing ChartService for moon phase calculation.
        """
        from ..mystical.astronomical_svc import AstronomicalService
        from skyfield.api import utc

        entries_by_phase = defaultdict(list)
        astronomical_svc = AstronomicalService()

        logger.info(f"📅 Categorizing {len(self.entries)} entries by moon phase...")

        for entry in self.entries:
            # Get moon phase for entry's datetime
            try:
                # Convert entry datetime to UTC and make it timezone-aware for Skyfield
                entry_dt = entry.created_at
                original_dt = entry_dt  # Keep for logging

                if entry_dt.tzinfo is None:
                    # If naive, assume it's already UTC
                    entry_dt = entry_dt.replace(tzinfo=utc)
                else:
                    # If aware, convert to UTC
                    entry_dt = entry_dt.astimezone(utc).replace(tzinfo=utc)

                # Create Skyfield time object
                entry_time = astronomical_svc.ts.from_datetime(entry_dt)

                # Calculate positions for entry time
                earth_observer = astronomical_svc.earth
                sun_pos = earth_observer.at(entry_time).observe(astronomical_svc.sun)
                moon_pos = earth_observer.at(entry_time).observe(astronomical_svc.moon)

                sun_lon = sun_pos.apparent().ecliptic_latlon()[1].degrees
                moon_lon = moon_pos.apparent().ecliptic_latlon()[1].degrees

                # Phase angle (0 = New Moon, 180 = Full Moon)
                phase_angle = (moon_lon - sun_lon) % 360

                # Categorize by phase
                phase_key = self._get_phase_key_from_angle(phase_angle)
                phase_name = self.MOON_PHASES[phase_key]['name']
                phase_emoji = self.MOON_PHASES[phase_key]['emoji']

                entries_by_phase[phase_key].append(entry)

                # Detailed logging for each entry
                logger.info(
                    f"  📝 Entry #{entry.id} | "
                    f"Date: {original_dt.strftime('%Y-%m-%d %H:%M:%S %Z')} | "
                    f"Phase Angle: {phase_angle:.2f}° | "
                    f"Phase: {phase_emoji} {phase_name}"

                    f"    🌞 Sun longitude: {sun_lon:.2f}° | "
                    f"🌙 Moon longitude: {moon_lon:.2f}° | "
                    f"📐 Phase angle: {phase_angle:.2f}°"
                )

            except Exception as e:
                logger.error(f"❌ Error calculating moon phase for entry {entry.id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue

        # Summary by phase
        logger.info(f"\n📊 PHASE DISTRIBUTION SUMMARY:")
        for phase_key in ['new_moon', 'waxing_crescent', 'first_quarter', 'waxing_gibbous',
                          'full_moon', 'waning_gibbous', 'last_quarter', 'waning_crescent']:
            count = len(entries_by_phase.get(phase_key, []))
            if count > 0:
                phase_name = self.MOON_PHASES[phase_key]['name']
                phase_emoji = self.MOON_PHASES[phase_key]['emoji']
                percentage = (count / len(self.entries) * 100) if len(self.entries) > 0 else 0
                logger.info(f"  {phase_emoji} {phase_name}: {count} entries ({percentage:.1f}%)")

        return dict(entries_by_phase)

    def _get_phase_key_from_angle(self, angle: float) -> str:
        """Convert moon phase angle (0-360) to phase category"""
        # Normalize angle to 0-360
        angle = angle % 360

        for phase_key, phase_data in self.MOON_PHASES.items():
            min_deg, max_deg = phase_data['degrees']
            if min_deg <= angle < max_deg:
                logger.debug(f"    Angle {angle:.2f}° matches {phase_data['name']} ({min_deg}-{max_deg}°)")
                return phase_key

        # Default to new moon if angle is 360 or close to it
        logger.debug(f"    Angle {angle:.2f}° defaulting to New Moon")
        return 'new_moon'

    def _calculate_phase_statistics(self, entries_by_phase: Dict) -> Dict:
        """
        Calculate detailed statistics for each moon phase.
        """
        logger.info(f"\n🔢 Calculating phase statistics...")
        phase_stats = {}

        for phase_key, phase_data in self.MOON_PHASES.items():
            entries = entries_by_phase.get(phase_key, [])
            entry_count = len(entries)

            # Get top tags for this phase
            tag_counter = Counter()
            for entry in entries:
                for tag in entry.tags.all():
                    tag_counter[tag.name] += 1

            top_tags = tag_counter.most_common(3)

            # Calculate average word count
            if entries:
                avg_words = sum(len(e.content.split()) for e in entries) / len(entries)
            else:
                avg_words = 0

            phase_stats[phase_key] = {
                'name': phase_data['name'],
                'emoji': phase_data['emoji'],
                'energy': phase_data['energy'],
                'color': phase_data['color'],
                'entry_count': entry_count,
                'percentage': (entry_count / self.entry_count * 100) if self.entry_count > 0 else 0,
                'top_tags': top_tags,
                'avg_words': avg_words
            }

            if entry_count > 0:
                logger.info(
                    f"  {phase_data['emoji']} {phase_data['name']}: "
                    f"{entry_count} entries, "
                    f"avg {avg_words:.0f} words, "
                    f"top tags: {[t[0] for t in top_tags]}"
                )

        return phase_stats

    def _find_dominant_phases(self, phase_stats: Dict) -> List[Tuple[str, Dict]]:
        """
        Find which moon phases user journals most during.
        Returns top 3 phases.
        """
        sorted_phases = sorted(
            phase_stats.items(),
            key=lambda x: x[1]['entry_count'],
            reverse=True
        )

        # Return top 3 phases with entries
        dominant = [(k, v) for k, v in sorted_phases if v['entry_count'] > 0][:3]

        logger.info(f"\n🏆 TOP 3 DOMINANT PHASES:")
        for i, (phase_key, phase_data) in enumerate(dominant, 1):
            logger.info(
                f"  #{i}: {phase_data['emoji']} {phase_data['name']} - "
                f"{phase_data['entry_count']} entries ({phase_data['percentage']:.1f}%)"
            )

        return dominant

    def _generate_insights(self, phase_stats: Dict, dominant_phases: List) -> List[str]:
        """
        Generate human-readable insights about lunar patterns.
        """
        insights = []

        if not dominant_phases:
            return ["Not enough data to detect lunar patterns yet"]

        # Insight 1: Most active phase
        top_phase_key, top_phase_data = dominant_phases[0]
        insights.append(
            f"You journal most during {top_phase_data['name']} "
            f"({top_phase_data['entry_count']} entries, {top_phase_data['percentage']:.0f}%)"
        )

        # Insight 2: Emotional pattern during top phase
        if top_phase_data['top_tags']:
            top_tag = top_phase_data['top_tags'][0][0]
            insights.append(
                f"During {top_phase_data['name']}, you often write about {top_tag}"
            )

        # Insight 3: Compare phases
        if len(dominant_phases) >= 2:
            second_phase_key, second_phase_data = dominant_phases[1]
            ratio = top_phase_data['entry_count'] / max(second_phase_data['entry_count'], 1)
            if ratio >= 2:
                insights.append(
                    f"You're {ratio:.1f}x more active during {top_phase_data['name']} "
                    f"than {second_phase_data['name']}"
                )

        # Insight 4: Full moon pattern
        full_moon_stats = phase_stats.get('full_moon', {})
        new_moon_stats = phase_stats.get('new_moon', {})

        if full_moon_stats['entry_count'] > new_moon_stats['entry_count'] * 1.5:
            insights.append(
                "Full moon energizes your journaling - you write significantly more during peak lunar energy"
            )
        elif new_moon_stats['entry_count'] > full_moon_stats['entry_count'] * 1.5:
            insights.append(
                "New moon draws you inward - you prefer journaling during introspective lunar energy"
            )

        # Insight 5: Word count variation
        word_counts = [v['avg_words'] for v in phase_stats.values() if v['entry_count'] > 0]
        if word_counts:
            max_words_phase = max(phase_stats.items(),
                                  key=lambda x: x[1]['avg_words'] if x[1]['entry_count'] > 0 else 0)
            if max_words_phase[1]['entry_count'] > 0 and max_words_phase[1]['avg_words'] > 0:
                insights.append(
                    f"Your longest entries happen during {max_words_phase[1]['name']} "
                    f"({max_words_phase[1]['avg_words']:.0f} words avg)"
                )

        logger.info(f"\n💡 Generated {len(insights)} insights")
        for i, insight in enumerate(insights, 1):
            logger.info(f"  {i}. {insight}")

        return insights[:4]  # Return top 4 insights

    def _prepare_visualization_data(self, phase_stats: Dict) -> Dict:
        """
        Prepare data for circular moon phase visualization.
        Returns data in format for Chart.js polar chart.
        """
        labels = []
        data = []
        colors = []

        for phase_key in ['new_moon', 'waxing_crescent', 'first_quarter', 'waxing_gibbous',
                          'full_moon', 'waning_gibbous', 'last_quarter', 'waning_crescent']:
            stats = phase_stats[phase_key]
            labels.append(f"{stats['emoji']} {stats['name']}")
            data.append(stats['entry_count'])
            # Convert Tailwind gradient to solid color for chart
            colors.append(self._gradient_to_color(phase_key))

        return {
            'type': 'moon_phases',
            'labels': labels,
            'data': data,
            'colors': colors,
            'emojis': [phase_stats[k]['emoji'] for k in phase_stats.keys()]
        }

    def _gradient_to_color(self, phase_key: str) -> str:
        """Convert phase to chart color"""
        color_map = {
            'new_moon': 'rgba(71, 85, 105, 0.8)',  # slate
            'waxing_crescent': 'rgba(99, 102, 241, 0.8)',  # indigo
            'first_quarter': 'rgba(59, 130, 246, 0.8)',  # blue
            'waxing_gibbous': 'rgba(6, 182, 212, 0.8)',  # cyan
            'full_moon': 'rgba(251, 191, 36, 0.8)',  # yellow
            'waning_gibbous': 'rgba(249, 115, 22, 0.8)',  # orange
            'last_quarter': 'rgba(168, 85, 247, 0.8)',  # purple
            'waning_crescent': 'rgba(100, 116, 139, 0.8)'  # slate-500
        }
        return color_map.get(phase_key, 'rgba(139, 92, 246, 0.8)')

    def _minimal_analysis(self) -> Dict:
        """Return minimal data when not enough entries"""
        return {
            'has_data': False,
            'total_entries': self.entry_count,
            'message': f"Need at least 3 entries to detect lunar patterns (you have {self.entry_count})",
            'phase_statistics': {},
            'dominant_phases': [],
            'insights': []
        }