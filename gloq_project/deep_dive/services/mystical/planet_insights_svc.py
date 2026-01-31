# from django.db.models import Count, Q
#
# from journal.models import JournalEntry
#
#
# def generate_planet_insight_data(user, planet_name):
#     # 1. Base Data Fetching
#     coincidences = JournalEntry.objects.filter(
#         user=user,
#         coincidences__planet_key=planet_name.capitalize()
#     ).select_related('planetary_snapshot')
#
#     total_hits = coincidences.count()
#     if total_hits == 0:
#         return None
#
#     # --- INSIGHT 1: Mood/Tag Fingerprint ---
#     # We find the most disproportionately common tag for this planet
#     top_tags = coincidences.values('tags__name', 'tags__emoji') \
#                    .annotate(count=Count('tags')) \
#                    .order_by('-count')[:3]
#
#     # --- INSIGHT 2: Stellium Weight (The 'Friends') ---
#     # Find other planets frequently hitting at the SAME TIME as this one
#     # We look at the Coincidence table for the same entries
#     from journal.models import JournalCosmicCoincidence
#     entry_ids = coincidences.values_list('id', flat=True)
#
#     companions = JournalCosmicCoincidence.objects.filter(entry_id__in=entry_ids) \
#                      .exclude(planet_key=planet_name.capitalize()) \
#                      .values('planet_key') \
#                      .annotate(occurence=Count('id')) \
#                      .order_by('-occurence')[:1]
#
#     frequent_companion = companions[0]['planet_key'] if companions else None
#
#     # --- INSIGHT 3: Retrograde Resilience ---
#     # Compare journal length or frequency during Retrograde vs Direct
#     retro_entries = coincidences.filter(
#         planetary_snapshot__planetary_data__planetary_positions__name=planet_name.capitalize(),
#         planetary_snapshot__planetary_data__planetary_positions__is_retrograde=True).count()
#
#     retro_percentage = (retro_entries / total_hits * 100) if total_hits > 0 else 0
#
#     # --- INSIGHT 4: House Focus (Natal Context) ---
#     natal_data = user.birth_profile.cached_chart_data
#     natal_planet = next((p for p in natal_data.get('planets', [])
#                          if p['name'] == planet_name.capitalize()), {})
#
#     house_num = natal_planet.get('house')
#     theme_data = HOUSE_INSIGHTS.get(house_num, {"theme": "General", "insight": "Exploring life."})
#
#     return {
#         'total_hits': total_hits,
#         'house': house_num,
#         'theme': theme_data['theme'],
#         'personal_note': theme_data['insight'],
#         'top_tags': top_tags,
#         'frequent_companion': frequent_companion,
#         'retro_percentage': round(retro_percentage),
#         'is_retro_resilient': retro_percentage > 30  # Just an example logic gate
#     }
#
#
# HOUSE_INSIGHTS = {
#     1: {"theme": "Self-Expression & Vitality", "insight": "You tend to focus on your personal identity and how the world sees you."},
#     2: {"theme": "Material & Inner Worth", "insight": "Your entries often revolve around security, belongings, and what you truly value."},
#     3: {"theme": "Intellectual Connection", "insight": "This planet triggers your curiosity, local environment, and sibling relationships."},
#     4: {"theme": "Emotional Foundations", "insight": "You write more about your home, family, and your deepest private feelings."},
#     5: {"theme": "Creative Spark", "insight": "This transit highlights your hobbies, romance, and the things that bring you pure joy."},
#     6: {"theme": "Rituals & Wellness", "insight": "Your focus shifts to your daily habits, health, and how you can be of service."},
#     7: {"theme": "Mirroring & Partnership", "insight": "You often reflect on your one-on-one relationships and the balance of 'Me vs. We'."},
#     8: {"theme": "Shadows & Shared Depths", "insight": "This triggers reflections on intimacy, deep change, and what is hidden beneath the surface."},
#     9: {"theme": "Expansion & Belief", "insight": "You tend to write about your philosophy, long-distance travel, or higher learning."},
#     10: {"theme": "Public Path", "insight": "Your entries lean toward your career, reputation, and your place in the wider world."},
#     11: {"theme": "Collectives & Hopes", "insight": "You focus on your social circles, friendships, and your dreams for the future."},
#     12: {"theme": "Solitude & Spirit", "insight": "This is a quiet, introspective time focused on dreams, healing, and ending old cycles."}
# }


# deep_dive/services/planet_insights_svc.py
"""
Analyzes journaling patterns for ALL planets efficiently.
Called once when modal opens, cached for session.
"""
import logging

from django.core.cache import cache
from django.db.models import Count, Avg, Q
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import statistics




class PlanetJournalInsightsService:
    """
    Efficiently analyzes ALL planet-journal patterns in one pass.
    Results cached per user to avoid repeated DB scans.
    """

    CACHE_TIMEOUT = 60 * 60 * 2  # 2 hours

    def __init__(self, user):
        self.user = user
        self.cache_key = f'planet_insights_{user.id}'

    def get_all_planet_insights(self):
        """
        Get insights for ALL planets, using cache when possible.
        Returns: dict keyed by planet_name
        """
        # Try cache first
        logger = logging.getLogger('drift_commentary')
        cached_data = cache.get(self.cache_key)
        if cached_data:
            logger.info(f"Cache HIT for user {self.user.username}")
            return cached_data

        logger.info(f"Cache MISS for user {self.user.username} - calculating fresh")
        insights = self._calculate_all_insights()
        cache.set(self.cache_key, insights, self.CACHE_TIMEOUT)
        return insights

    def get_planet_insight(self, planet_name):
        """
        Get insight for a specific planet (uses cached ALL data).
        """
        all_insights = self.get_all_planet_insights()
        return all_insights.get(planet_name, self._empty_insight(planet_name))

    def _calculate_all_insights(self):
        """
        Single-pass calculation for all planets.
        Efficient DB queries using prefetch and select_related.
        """
        from journal.models import JournalEntry, JournalCosmicCoincidence

        # === SINGLE QUERY: Get all entries with prefetched tags ===
        all_entries = list(
            JournalEntry.objects
            .filter(user=self.user)
            .prefetch_related('tags')
            .order_by('created_at')
        )

        if len(all_entries) < 3:
            return self._minimal_insights()

        # === SINGLE QUERY: Get all cosmic coincidences ===
        all_coincidences = list(
            JournalCosmicCoincidence.objects
            .filter(user=self.user)
            .select_related('entry')
            .prefetch_related('entry__tags')
        )

        # === Group coincidences by planet ===
        planet_entries = defaultdict(list)
        for coincidence in all_coincidences:
            planet_entries[coincidence.planet_key].append(coincidence.entry)

        # === Calculate baseline metrics (all entries) ===
        baseline = self._calculate_baseline(all_entries)

        # === Calculate per-planet insights ===
        insights = {}

        # All planets we care about
        planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                   'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

        for planet_name in planets:
            entries = planet_entries.get(planet_name, [])

            if len(entries) >= 3:  # Minimum threshold
                insights[planet_name] = {
                    'has_data': True,
                    'fingerprint': self._calculate_fingerprint(entries, baseline, all_entries),
                    'emotional_weather': self._calculate_emotional_weather(entries, baseline),
                }
            else:
                insights[planet_name] = self._empty_insight(planet_name, len(entries))

        return insights

    def _calculate_baseline(self, all_entries):
        """Calculate baseline metrics across all journaling."""
        if not all_entries:
            return {
                'total_entries': 0,
                'avg_word_count': 0,
                'avg_sentiment': 0,
                'morning_percentage': 0,
            }

        word_counts = []
        sentiments = []
        morning_count = 0

        for entry in all_entries:
            # Word count
            word_count = len(entry.content.split())
            word_counts.append(word_count)

            # Sentiment (average of entry's tags)
            entry_tags = list(entry.tags.all())
            if entry_tags:
                entry_sentiment = sum(t.sentiment_score for t in entry_tags) / len(entry_tags)
                sentiments.append(entry_sentiment)

            # Morning check (before noon)
            if entry.created_at.hour < 12:
                morning_count += 1

        return {
            'total_entries': len(all_entries),
            'avg_word_count': statistics.mean(word_counts) if word_counts else 0,
            'avg_sentiment': statistics.mean(sentiments) if sentiments else 0,
            'morning_percentage': (morning_count / len(all_entries) * 100) if all_entries else 0,
        }

    def _calculate_fingerprint(self, planet_entries, baseline, all_entries):
        """
        Calculate journaling fingerprint for a planet.

        Returns:
        - activity_level: count and percentage
        - writing_style: word count comparison
        - timing_pattern: when they write
        - comparison_multiplier: how much more they write during this planet
        """
        if not planet_entries:
            return None

        total_planet_entries = len(planet_entries)
        total_all_entries = baseline['total_entries']

        # Activity level
        percentage = (total_planet_entries / total_all_entries * 100) if total_all_entries else 0

        # Comparison multiplier
        expected_percentage = 100 / 10  # Rough expectation if evenly distributed
        multiplier = percentage / expected_percentage if expected_percentage else 1

        # Word count analysis
        word_counts = [len(e.content.split()) for e in planet_entries]
        avg_word_count = statistics.mean(word_counts) if word_counts else 0
        word_count_diff = avg_word_count - baseline['avg_word_count']

        # Timing pattern
        morning_count = sum(1 for e in planet_entries if e.created_at.hour < 12)
        afternoon_count = sum(1 for e in planet_entries if 12 <= e.created_at.hour < 18)
        evening_count = sum(1 for e in planet_entries if e.created_at.hour >= 18)

        morning_pct = (morning_count / total_planet_entries * 100) if total_planet_entries else 0
        afternoon_pct = (afternoon_count / total_planet_entries * 100) if total_planet_entries else 0
        evening_pct = (evening_count / total_planet_entries * 100) if total_planet_entries else 0

        # Determine primary time
        time_map = {
            morning_pct: 'morning',
            afternoon_pct: 'afternoon',
            evening_pct: 'evening'
        }
        primary_time = time_map[max(morning_pct, afternoon_pct, evening_pct)]
        primary_time_pct = max(morning_pct, afternoon_pct, evening_pct)

        return {
            'total_entries': total_planet_entries,
            'percentage_of_journal': round(percentage, 1),
            'activity_level': self._get_activity_label(percentage),
            'comparison_multiplier': round(multiplier, 1),
            'avg_word_count': round(avg_word_count),
            'baseline_word_count': round(baseline['avg_word_count']),
            'word_count_diff': round(word_count_diff),
            'word_style': 'longer' if word_count_diff > 50 else 'shorter' if word_count_diff < -50 else 'similar',
            'primary_time': primary_time,
            'primary_time_percentage': round(primary_time_pct),
            'morning_pct': round(morning_pct),
            'afternoon_pct': round(afternoon_pct),
            'evening_pct': round(evening_pct),
        }

    def _calculate_emotional_weather(self, planet_entries, baseline):
        """
        Calculate emotional signature for a planet.

        Returns:
        - overall_sentiment: average and label
        - sentiment_range: min to max
        - top_emotions: most common tags with sentiment
        - variance: emotional volatility
        - comparison: vs baseline
        """
        if not planet_entries:
            return None

        # Collect all tags and sentiments
        all_tags = []
        all_sentiments = []

        for entry in planet_entries:
            entry_tags = list(entry.tags.all())
            all_tags.extend(entry_tags)

            if entry_tags:
                entry_sentiment = sum(t.sentiment_score for t in entry_tags) / len(entry_tags)
                all_sentiments.append(entry_sentiment)

        if not all_sentiments:
            return None

        # Calculate metrics
        avg_sentiment = statistics.mean(all_sentiments)
        min_sentiment = min(all_sentiments)
        max_sentiment = max(all_sentiments)
        sentiment_variance = statistics.stdev(all_sentiments) if len(all_sentiments) > 1 else 0

        # Top emotions (tags)
        tag_counter = Counter([tag.name for tag in all_tags])
        top_emotions = []

        for tag_name, count in tag_counter.most_common(5):
            # Get sentiment for this tag (average if appears multiple times)
            tag_sentiments = [t.sentiment_score for t in all_tags if t.name == tag_name]
            tag_avg_sentiment = statistics.mean(tag_sentiments)

            top_emotions.append({
                'name': tag_name,
                'count': count,
                'sentiment': round(tag_avg_sentiment, 2),
                'emoji': self._sentiment_to_emoji(tag_avg_sentiment)
            })

        # Comparison to baseline
        sentiment_diff = avg_sentiment - baseline['avg_sentiment']

        return {
            'avg_sentiment': round(avg_sentiment, 2),
            'sentiment_label': self._sentiment_to_label(avg_sentiment),
            'min_sentiment': round(min_sentiment, 2),
            'max_sentiment': round(max_sentiment, 2),
            'sentiment_range_spread': round(max_sentiment - min_sentiment, 2),
            'variance': round(sentiment_variance, 2),
            'variance_label': self._variance_to_label(sentiment_variance),
            'top_emotions': top_emotions,
            'baseline_sentiment': round(baseline['avg_sentiment'], 2),
            'sentiment_diff': round(sentiment_diff, 2),
            'sentiment_shift': 'more positive' if sentiment_diff > 0.1 else 'more challenging' if sentiment_diff < -0.1 else 'similar',
        }

    # === HELPER METHODS ===

    def _get_activity_label(self, percentage):
        """Convert percentage to activity label."""
        if percentage >= 20:
            return 'VERY HIGH'
        elif percentage >= 15:
            return 'HIGH'
        elif percentage >= 10:
            return 'MODERATE'
        elif percentage >= 5:
            return 'LOW'
        else:
            return 'MINIMAL'

    def _sentiment_to_label(self, sentiment):
        """Convert sentiment score to label."""
        if sentiment >= 0.5:
            return 'Very Positive'
        elif sentiment >= 0.2:
            return 'Moderately Positive'
        elif sentiment >= -0.2:
            return 'Neutral/Mixed'
        elif sentiment >= -0.5:
            return 'Moderately Challenging'
        else:
            return 'Very Challenging'

    def _variance_to_label(self, variance):
        """Convert variance to emotional intensity label."""
        if variance >= 0.6:
            return 'VERY HIGH (emotional rollercoaster)'
        elif variance >= 0.4:
            return 'HIGH (wide emotional swings)'
        elif variance >= 0.2:
            return 'MODERATE (varied but stable)'
        else:
            return 'LOW (emotionally consistent)'

    def _sentiment_to_emoji(self, sentiment):
        """Convert sentiment to emoji."""
        if sentiment >= 0.5:
            return '😊'
        elif sentiment >= 0.2:
            return '🙂'
        elif sentiment >= -0.2:
            return '😐'
        elif sentiment >= -0.5:
            return '😤'
        else:
            return '😔'

    def _empty_insight(self, planet_name, entry_count=0):
        """Return structure for planets with insufficient data."""
        return {
            'has_data': False,
            'planet_name': planet_name,
            'entry_count': entry_count,
            'message': f'Need at least 3 entries during {planet_name} activations to detect patterns (you have {entry_count})'
        }

    def _minimal_insights(self):
        """Return minimal data when user has very few total entries."""
        planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                   'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

        return {
            planet: self._empty_insight(planet, 0)
            for planet in planets
        }


# === Convenience function ===
def get_planet_insight(user, planet_name):
    """
    Get insight for a specific planet.
    Uses cached data when possible.
    """
    service = PlanetJournalInsightsService(user)
    return service.get_planet_insight(planet_name)