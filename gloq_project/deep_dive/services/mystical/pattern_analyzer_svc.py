# deep_dive/services/pattern_analyzer.py
"""
Personal Rhythm Tracker - Main Pattern Analysis Orchestrator

This service coordinates all pattern detection across:
- Cosmic rhythm (current celestial state)
- Journal rhythm (user's journaling patterns)
- Personal cycles (discovered patterns from data)

Architecture:
- Progressive disclosure: Shows insights based on available data
- Modular: Each pattern type is a separate analyzer
- Cacheable: Expensive calculations can be cached
"""

from django.utils import timezone
from datetime import timedelta
from typing import Dict, Optional


class UserPatternAnalyzer:
    """
    Main orchestrator for personal rhythm analysis.

    Usage:
        analyzer = UserPatternAnalyzer(request.user)
        insights = analyzer.get_all_insights()
    """

    def __init__(self, user):
        self.user = user
        self.now = timezone.now()

        # Assess what data is available
        self.has_birth_profile = self._check_birth_profile()
        self.journal_count = self._count_journals()
        self.data_level = self._assess_data_level()

    def _check_birth_profile(self) -> bool:
        """Check if user has complete birth profile with natal chart"""
        try:
            return (
                    hasattr(self.user, 'birth_profile') and
                    self.user.birth_profile.cached_chart_data is not None
            )
        except:
            return False

    def _count_journals(self, days_back: int = 90) -> int:
        """Count journal entries in recent period"""
        from journal.models import JournalEntry

        cutoff = self.now - timedelta(days=days_back)
        return JournalEntry.objects.filter(
            user=self.user,
            created_at__gte=cutoff
        ).count()

    def _assess_data_level(self) -> str:
        """
        Determine what level of insights we can provide.

        Levels:
        - minimal: 0-2 entries (show cosmic rhythm only)
        - emerging: 3-9 entries (add basic journal patterns)
        - established: 10-29 entries (add frequency analysis)
        - rich: 30+ entries (add cycle detection and correlations)
        """
        if self.journal_count < 3:
            return 'minimal'
        elif self.journal_count < 10:
            return 'emerging'
        elif self.journal_count < 30:
            return 'established'
        else:
            return 'rich'

    # Update to deep_dive/services/mystical/pattern_analyzer.py
    # Add this to UserPatternAnalyzer class

    def get_all_insights(self) -> Dict:
        """
        Main method: Returns all available insights based on data level.

        Returns a structured dict that the view can use to render UI.
        """
        from ..mystical.rhythm_analyzer_svc import CosmicRhythmAnalyzer, JournalRhythmAnalyzer
        from ..mystical.moon_journal_insight_svc import MoonPhaseCorrelator
        from ..mystical.planet_journal_insight_svc import PlanetaryEmotionCorrelator
        from ..mystical.cosmic_alignments_svc import CosmicAlignmentsAnalyzer  # NEW

        insights = {
            'data_level': self.data_level,
            'journal_count': self.journal_count,
            'has_birth_chart': self.has_birth_profile,
            'cosmic_rhythm': None,
            'journal_rhythm': None,
            'moon_correlation': None,
            'planetary_emotions': None,
            'cosmic_alignments': None,  # NEW
            'personal_cycles': None,
            'meta': self._get_meta_info()
        }

        # ALWAYS show cosmic rhythm (no user data needed)
        cosmic_analyzer = CosmicRhythmAnalyzer()
        insights['cosmic_rhythm'] = cosmic_analyzer.get_current_state()

        # Add moon correlation if we have enough data (3+ entries)
        if self.journal_count >= 3:
            moon_correlator = MoonPhaseCorrelator(self.user)
            insights['moon_correlation'] = moon_correlator.analyze()

        # Add planetary-emotion correlation if we have enough data (5+ entries)
        if self.journal_count >= 5:
            planet_correlator = PlanetaryEmotionCorrelator(self.user)
            insights['planetary_emotions'] = planet_correlator.analyze()

        # Add journal rhythm if we have enough data
        if self.data_level in ['emerging', 'established', 'rich']:
            journal_analyzer = JournalRhythmAnalyzer(self.user)
            insights['journal_rhythm'] = journal_analyzer.analyze()

        # NEW: Add cosmic alignments if we have enough data (3+ entries)
        if self.journal_count >= 3:
            alignments_analyzer = CosmicAlignmentsAnalyzer(self.user)
            insights['cosmic_alignments'] = alignments_analyzer.analyze()

        # Add personal cycles for rich data users
        if self.data_level == 'rich' and self.has_birth_profile:
            # This will be implemented in Phase 4
            # from .personal_cycles import PersonalCycleAnalyzer
            # cycle_analyzer = PersonalCycleAnalyzer(self.user)
            # insights['personal_cycles'] = cycle_analyzer.analyze()
            pass

        return insights

    def _get_meta_info(self) -> Dict:
        """
        Metadata about the analysis for UI display.
        Helps render appropriate messages/CTAs based on data level.
        """
        meta = {
            'level_name': self.data_level.title(),
            'level_description': self._get_level_description(),
            'next_milestone': self._get_next_milestone(),
            'can_show_chart': self.data_level in ['established', 'rich'],
            'can_show_correlations': self.data_level == 'rich' and self.has_birth_profile
        }
        return meta

    def _get_level_description(self) -> str:
        """Human-readable description of current data level"""
        descriptions = {
            'minimal': 'Start journaling to discover your personal patterns',
            'emerging': 'Your pattern story is beginning to unfold',
            'established': 'Clear patterns are emerging from your journal',
            'rich': 'Deep pattern insights available'
        }
        return descriptions.get(self.data_level, '')

    def _get_next_milestone(self) -> Optional[Dict]:
        """What the user needs to unlock next level of insights"""
        if self.data_level == 'minimal':
            return {
                'entries_needed': 3 - self.journal_count,
                'message': 'Write 3 entries to unlock basic pattern insights'
            }
        elif self.data_level == 'emerging':
            return {
                'entries_needed': 10 - self.journal_count,
                'message': 'Write 10 entries to unlock frequency analysis'
            }
        elif self.data_level == 'established':
            if not self.has_birth_profile:
                return {
                    'entries_needed': 0,
                    'message': 'Complete your birth profile to unlock cosmic correlations',
                    'needs_birth_chart': True
                }
            return {
                'entries_needed': 30 - self.journal_count,
                'message': 'Write 30 entries to unlock cycle discovery'
            }
        return None  # Already at rich level

    def get_visualization_data(self) -> Dict:
        """
        Returns data formatted for Chart.js visualization.
        Structure depends on data_level.
        """
        from ..mystical.rhythm_analyzer_svc import CosmicRhythmAnalyzer, JournalRhythmAnalyzer
        if self.data_level == 'minimal':
            # Only cosmic rhythm - return current state as simple data

            cosmic = CosmicRhythmAnalyzer()
            return cosmic.get_visualization_data()
        elif self.data_level in ['emerging', 'established']:
            # Journal frequency over time
            journal = JournalRhythmAnalyzer(self.user)
            return journal.get_frequency_chart_data()

        elif self.data_level == 'rich':
            # Combined view: journal rhythm + cosmic correlations
            journal = JournalRhythmAnalyzer(self.user)
            return journal.get_advanced_chart_data()

        return {}