# Standard library imports
import logging
import random
from datetime import timedelta

# Django imports
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.utils import timezone

# Local imports
from ..models import JournalEntry, Tag
from modes.models import Mode
from modes.utils import get_active_mode


class StreamView(LoginRequiredMixin, View):
    """Main stream view handling both full page and HTMX partial updates"""

    def get(self, request):
        view_type = request.GET.get('view', 'chronological')
        entries = self._get_entries(view_type)

        context = {
            'entries': entries,
            'entries_count': entries.count(),
            'view_type': view_type
        }

        # Debug logging
        print(f"HX-Request header: {request.headers.get('HX-Request')}")
        print(f"All headers: {dict(request.headers)}")

        # Return partial template for HTMX requests
        if request.headers.get('HX-Request'):
            return render(request, 'journal/stream/note_stream.html', context)

        return render(request, 'journal/stream/stream.html', context)

    def _get_base_queryset(self):
        """Always filter entries to the logged-in user"""
        return JournalEntry.objects.filter(
            user=self.request.user
        ).prefetch_related('tags')

    def _get_entries(self, view_type='chronological'):
        """Get entries based on view type"""
        base_query = self._get_base_queryset()

        if view_type == 'chronological':
            return base_query.order_by('-created_at')[:3]

        elif view_type == 'clustered':
            return self._get_clustered_entries(base_query)

        elif view_type == 'weekly':
            week_ago = timezone.now() - timedelta(days=7)
            return base_query.filter(created_at__gte=week_ago).order_by('-created_at')

        return base_query.order_by('-created_at')[:20]

    def _get_clustered_entries(self, queryset):
        """Group entries by tags or themes for clustered view"""
        return queryset.annotate(
            tag_count=Count('tags')
        ).order_by('-tag_count', '-created_at')[:20]


class StreamToggleView(View):
    """Handle view toggle between chronological and clustered"""

    def post(self, request):
        view_type = request.POST.get('view_type', 'chronological')

        entries = StreamView()._get_entries(view_type)
        context = {
            'entries': entries,
            'entries_count': entries.count(),
            'view_type': view_type
        }

        return render(request, 'journal/stream/partials/stream_entries.html', context)


class QuickActionView(View):
    """Handle quick actions on stream entries"""

    def post(self, request):
        action = request.POST.get('action')
        entry_id = request.POST.get('entry_id')

        try:
            entry = JournalEntry.objects.get(id=entry_id)
        except JournalEntry.DoesNotExist:
            return JsonResponse({'error': 'Entry not found'}, status=404)

        if action == 'favorite':
            entry.is_favorited = not entry.is_favorited
            entry.save()
            return JsonResponse({
                'success': True,
                'is_favorited': entry.is_favorited
            })

        elif action == 'tag':
            # Handle tag addition/removal
            tag_name = request.POST.get('tag_name', '').strip()
            if tag_name:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                if entry.tags.filter(id=tag.id).exists():
                    entry.tags.remove(tag)
                    action_type = 'removed'
                else:
                    entry.tags.add(tag)
                    action_type = 'added'

                return JsonResponse({
                    'success': True,
                    'action': action_type,
                    'tag_name': tag_name
                })

        elif action == 'reflect':
            # Trigger AI reflection - delegate to synthesize view
            from ..views import SynthesizeEntriesView
            synthesize_view = SynthesizeEntriesView()
            return synthesize_view.post(request)

        return JsonResponse({'error': 'Invalid action'}, status=400)


class DriftCommentaryService:
    """Generate AI-powered commentary for why entries surface in the stream"""
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        self.mode_prompts = {
            'spiritual': {
                'system_prompt': (
                    "You are a spiritual guide who perceives resurfacing journal entries as sacred echoes. "
                    "You interpret them through rituals, prayers, and divine lessons embedded in daily life. "
                    "When entries resurface, you help users see the spiritual wisdom they've already discovered. "
                    "Respond with 20-30 words offering gentle guidance that connects past insight to present moment."
                ),
                'style': 'spiritual, sacred, faith-based'
            },
            'visionary': {
                'system_prompt': (
                    "You are a visionary thinker who sees resurfacing journal entries as future signposts. "
                    "You interpret them as glimpses of patterns, breakthrough moments, and forward momentum. "
                    "When entries resurface, you help users recognize the vision they're already building. "
                    "Respond with 20-30 words that feel transformative and connect past progress to future potential."
                ),
                'style': 'visionary, innovative, future-focused'
            },
            'exploratory': {
                'system_prompt': (
                    "You are an explorer of consciousness who treats resurfacing journal entries as discovery maps. "
                    "You frame them as evidence of curiosity rewarded and paths worth revisiting. "
                    "When entries resurface, you remind users of their own exploratory wisdom. "
                    "Respond with 20-30 words filled with adventurous recognition of discoveries already made."
                ),
                'style': 'exploratory, curious, adventurous'
            },
            'productive': {
                'system_prompt': (
                    "You are a productivity coach who views resurfacing journal entries as proof of what works. "
                    "You uncover practical patterns, successful strategies, and effective approaches they've used before. "
                    "When entries resurface, you remind users of systems and methods that served them well. "
                    "Respond with 20-30 words that emphasize proven strategies and actionable wisdom from experience."
                ),
                'style': 'productive, efficient, action-oriented'
            },
            'creative': {
                'system_prompt': (
                    "You are a creative muse who interprets resurfacing journal entries as artistic breadcrumbs. "
                    "You draw connections between past creative moments and current artistic potential. "
                    "When entries resurface, you remind users of their creative breakthroughs and flowing states. "
                    "Respond with 20-30 words weaving recognition of creative wisdom they've already accessed."
                ),
                'style': 'creative, artistic, inspiring'
            },
            'medical': {
                'system_prompt': (
                    "You are a medical guide who understands resurfacing journal entries as health pattern recognition. "
                    "You connect them to what worked before for well-being, stress management, and self-care. "
                    "When entries resurface, you remind users of healing approaches and wellness insights they've discovered. "
                    "Respond with 20-30 words that are supportive and highlight health wisdom from their own experience."
                ),
                'style': 'medical, scientific, healing'
            },
            'philosophical': {
                'system_prompt': (
                    "You are a philosopher who interprets resurfacing journal entries as wisdom returning. "
                    "You treat them as evidence of insights earned and understanding deepened through experience. "
                    "When entries resurface, you remind users of philosophical clarity they've already achieved. "
                    "Respond with 20-30 words offering recognition of rational insights and contemplative wisdom they've gained."
                ),
                'style': 'philosophical, rational, reflective'
            },
            'mystical': {
                'system_prompt': (
                    "You are a mystical guide who understands the cosmic significance of memories returning. "
                    "When old journal entries emerge, you see them as synchronistic reminders of spiritual insights already received. "
                    "You help users recognize the mystical patterns and divine timing in their own words returning. "
                    "Respond with 20-30 words of evocative recognition that honors the mystery of perfect timing."
                ),
                'style': 'mystical, cosmic, esoteric'
            },
        }

        # Enhanced fallback templates - now more contextual
        self.commentary_templates = {
            'tag_connection': {
                'patterns': [
                    "echoes the same {current_theme} energy you're exploring now",
                    "returns with familiar {tag_name} wisdom when you need it most",
                    "resurfaces the same theme—your mind is connecting the dots",
                    "brings back proven insights about {current_theme}"
                ],
                'mood_descriptors': ['returning', 'familiar', 'connecting', 'recognizing']
            },
            'temporal_connection': {
                'patterns': [
                    "from when you navigated something similar successfully",
                    "carries forward wisdom from {time_context} that still applies",
                    "returns from a time when you found your way through",
                    "brings perspective from {time_context} when things clicked"
                ],
                'mood_descriptors': ['experienced', 'tested', 'proven', 'seasoned']
            },
            'serendipity': {
                'patterns': [
                    "surfaces with perfect timing from your deeper wisdom",
                    "emerges precisely when your subconscious knows you need it",
                    "returns mysteriously carrying exactly what serves you now",
                    "drifts up with uncanny relevance to your current path"
                ],
                'mood_descriptors': ['intuitive', 'synchronistic', 'timely', 'knowing']
            }
        }

    def generate_drift_commentary(self, drift_entry, drift_reason, context_data):
        """Generate contextual commentary for why an entry surfaced"""

        # Get current session mode
        active_mode = context_data.get('active_mode', 'philosophical')

        # Try AI commentary first
        ai_commentary = self._generate_ai_commentary(drift_entry, drift_reason, active_mode, context_data)

        if ai_commentary:
            return ai_commentary

        # Fallback to template system
        return self._generate_template_commentary(drift_entry, drift_reason, context_data)

    def _generate_ai_commentary(self, drift_entry, drift_reason, active_mode, context_data):
        """Generate AI commentary based on current active mode using Groq API"""

        logger = logging.getLogger('drift_commentary')
        logger.info(f"=== AI Commentary Generation Debug ===")
        logger.info(f"Entry ID: {drift_entry.id}")
        logger.info(f"Drift Reason: {drift_reason}")
        logger.info(f"Active mode: '{active_mode}'")

        # Get mode configuration
        mode_config = self.mode_prompts.get(active_mode.lower(), self.mode_prompts['philosophical'])
        selected_mode = active_mode.lower() if active_mode.lower() in self.mode_prompts else 'philosophical'

        logger.info(f"Selected mode: '{selected_mode}'")

        try:
            from groq import Groq
            from django.conf import settings

            client = Groq(api_key=settings.GROQ_API_KEY)

            # Enhanced context building
            entry_preview = drift_entry.content[:200] if len(drift_entry.content) > 200 else drift_entry.content
            days_ago = context_data.get('days_ago', 0)

            # Get recent entries content
            recent_content = context_data.get('recent_entries_content', 'No recent entries available')

            # Build richer context for better commentary
            contextual_analysis = self._analyze_entry_context(drift_entry, context_data)

            # === RANDOMIZED PROMPT PATTERN ===
            prompt_pattern = self._get_random_prompt_pattern(active_mode)

            # Connection context with more insight
            connection_context = self._build_connection_narrative(drift_reason, context_data, contextual_analysis)

            # UPDATED PROMPT: Include recent entries content
            prompt = f"""ROLE: You are a {active_mode.title()} guide operating in {active_mode.title()} Mode.

            PRIMARY FOCUS:
            The commentary must be about the user's most recent journal entries. These are the subject of your reflection.

            RECENT ENTRIES (main subject):
            "{recent_content}"

            REFERENCE ENTRY (background only):
            An older resurfaced entry from {days_ago} days ago:
            "{entry_preview}"
            This is not the subject. Use it only as a memory or comparison.

            SITUATION: {connection_context}

            PATTERN RECOGNITION: {contextual_analysis['pattern_description']}

            MODE INSTRUCTIONS: {mode_config['system_prompt']}

            SPECIFIC TASK: {prompt_pattern['instruction']}

            STYLE REQUIREMENTS:
            - PLEASE, Commentary must read like natural reflection, not referencing labels such as “Recent Entry” or “Entry 1/2.”
            - Unmistakably {active_mode} tone: {mode_config['style']}
            - No explanations, just the insight
            - Example of {active_mode} tone: "{prompt_pattern['example']}"
            - Pick lessons and insights from REFERENCE ENTRY/resurfaced entry that could give insights to the user about their RECENT ENTRIES.
            - VERY IMPORTANT! Respond with ONLY the insight (20–30 words). Vary phrasing naturally, and make sure your response is a finished sentence.
            """

            logger.info(f"Enhanced prompt with recent entries context")
            logger.info(f"ACTIVE MODE: {active_mode.title()} PROMPT PATTERN RANDOM: {prompt_pattern}")
            logger.info(f"RECENT ENTRIES: {recent_content}")

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100,
            )

            ai_response = response.choices[0].message.content.strip().strip('"\'')
            word_count = len(ai_response.split())

            if ai_response and word_count >= 8:
                logger.info(f"SUCCESS: Contextual AI commentary generated with recent entries context")
                logger.info(f"AI Response FULL: {ai_response}")
                return {
                    'reason_phrase': ai_response,
                    'context_phrase': self._generate_context_phrase(drift_entry, context_data, drift_reason),
                    'mood_descriptor': mode_config['style'].split(',')[0].strip(),
                    'confidence': 0.85,
                    'connection_strength': 'strong' if drift_reason == 'tag_connection' else 'medium',
                    'ai_generated': True,
                    'contextual_insight': contextual_analysis['insight_type']
                }
            else:
                logger.warning(f"AI response too short: '{ai_response}' ({word_count} words)")

        except Exception as e:
            logger.error(f"AI commentary generation failed: {e}", exc_info=True)

        return None

    def _analyze_entry_context(self, drift_entry, context_data):
        """Analyze the entry to understand its contextual role and patterns"""

        analysis = {
            'insight_type': 'general',
            'pattern_description': 'No clear pattern detected',
            'contextual_relevance': 'medium',
            'action_indicators': [],
            'emotional_indicators': [],
            'solution_indicators': []
        }

        content = drift_entry.content.lower()

        # Detect action/solution language
        action_words = ['decided', 'tried', 'worked', 'helped', 'solved', 'figured out',
                        'realized', 'learned', 'discovered', 'found that', 'turns out']
        solution_words = ['finally', 'breakthrough', 'clicked', 'makes sense', 'got it',
                          'worked out', 'solved', 'answer', 'solution', 'way forward']

        for word in action_words:
            if word in content:
                analysis['action_indicators'].append(word)
                analysis['insight_type'] = 'actionable'

        for word in solution_words:
            if word in content:
                analysis['solution_indicators'].append(word)
                analysis['insight_type'] = 'breakthrough'

        # Detect emotional processing
        emotion_words = ['felt', 'feeling', 'emotions', 'stressed', 'calm', 'anxious',
                         'peaceful', 'frustrated', 'grateful', 'worried', 'relieved']
        for word in emotion_words:
            if word in content:
                analysis['emotional_indicators'].append(word)
                if analysis['insight_type'] == 'general':
                    analysis['insight_type'] = 'emotional_processing'

        # Build pattern description
        if analysis['solution_indicators']:
            analysis['pattern_description'] = "Entry contains breakthrough moments or solutions"
        elif analysis['action_indicators']:
            analysis['pattern_description'] = "Entry shows actionable approaches and decisions"
        elif analysis['emotional_indicators']:
            analysis['pattern_description'] = "Entry focuses on emotional processing and reflection"
        else:
            analysis['pattern_description'] = "Entry captures general thoughts and observations"

        # Check tag patterns for recurring themes
        shared_tags = context_data.get('shared_tags', [])
        if shared_tags:
            tag_names = [tag.name.lower() for tag in shared_tags]
            analysis['pattern_description'] += f" with recurring themes: {', '.join(tag_names[:2])}"
            analysis['contextual_relevance'] = 'high'

        return analysis

    def _build_connection_narrative(self, drift_reason, context_data, analysis):
        """Build a narrative explaining why this entry surfaced"""

        if drift_reason == 'tag_connection':
            shared_tags = context_data.get('shared_tags', [])
            if shared_tags:
                tag_name = shared_tags[0].name
                if analysis['insight_type'] == 'breakthrough':
                    return f"This entry about {tag_name} contains insights you discovered before - now the same theme is active in your recent writing"
                elif analysis['insight_type'] == 'actionable':
                    return f"This entry shows how you approached {tag_name} before - you're exploring the same territory again"
                else:
                    return f"This entry explores {tag_name}, which you've been writing about recently - your mind is connecting related thoughts"

        elif drift_reason == 'temporal_connection':
            days_ago = context_data.get('days_ago', 0)
            if analysis['insight_type'] == 'breakthrough':
                return f"From {days_ago} days ago when you had some breakthroughs - similar patterns might be emerging now"
            else:
                return f"From {days_ago} days ago when you were processing similar thoughts - cyclical patterns in your thinking"

        else:  # serendipity
            if analysis['insight_type'] == 'actionable':
                return "Emerged mysteriously with practical wisdom that might apply to your current situation"
            elif analysis['insight_type'] == 'breakthrough':
                return "Surfaced unexpectedly with insights that could illuminate something you're working through"
            else:
                return "Rose from the depths with perfect timing - your subconscious might know why"

        return "Surfaced through the natural flow of memory and relevance"

    def _generate_template_commentary(self, drift_entry, drift_reason, context_data):
        """Enhanced fallback template-based commentary generation"""

        commentary_data = self._analyze_drift_context(drift_entry, drift_reason, context_data)

        # Generate the main reason phrase with more context awareness
        reason_phrase = self._generate_contextual_reason_phrase(drift_reason, commentary_data, context_data)

        # Add contextual depth
        context_phrase = self._generate_context_phrase(drift_entry, context_data)

        # Create mood descriptor
        mood = self._select_mood_descriptor(drift_reason, commentary_data)

        return {
            'reason_phrase': reason_phrase,
            'context_phrase': context_phrase,
            'mood_descriptor': mood,
            'confidence': commentary_data.get('confidence', 0.7),
            'connection_strength': commentary_data.get('connection_strength', 'medium'),
            'ai_generated': False
        }

    def _generate_contextual_reason_phrase(self, drift_reason, analysis, context_data):
        """Generate reason phrase with contextual awareness"""

        templates = self.commentary_templates.get(drift_reason, {}).get('patterns', [])
        if not templates:
            return "surfaced with meaningful timing"

        template = random.choice(templates)

        # Enhanced template filling with context
        if drift_reason == 'tag_connection' and analysis.get('dominant_theme'):
            template = template.format(
                current_theme=analysis['dominant_theme'],
                tag_name=analysis['dominant_theme']
            )
        elif drift_reason == 'temporal_connection':
            days_ago = context_data.get('days_ago', 0)
            time_context = self._categorize_time_distance(days_ago)
            template = template.format(time_context=time_context)

        return template

    def _analyze_drift_context(self, drift_entry, drift_reason, context_data):
        """Enhanced context analysis with pattern recognition"""

        analysis = {
            'primary_reason': drift_reason,
            'confidence': 0.5,
            'connection_strength': 'medium',
            'thematic_overlap': [],
            'temporal_relevance': None,
            'contextual_factors': []
        }

        if drift_reason == 'tag_connection':
            shared_tags = context_data.get('shared_tags', [])
            analysis['thematic_overlap'] = shared_tags
            analysis['confidence'] = min(0.9, 0.6 + (len(shared_tags) * 0.1))
            analysis['dominant_theme'] = shared_tags[0].name if shared_tags else None
            analysis['connection_strength'] = 'strong' if len(shared_tags) > 1 else 'medium'
            analysis['contextual_factors'].append('recurring_theme')

        elif drift_reason == 'temporal_connection':
            days_ago = context_data.get('days_ago', 0)
            analysis['temporal_relevance'] = self._categorize_time_distance(days_ago)
            analysis['confidence'] = 0.65
            analysis['contextual_factors'].append('cyclical_pattern')

        else:  # serendipity
            analysis['confidence'] = 0.75  # High confidence in meaningful randomness
            analysis['contextual_factors'].append('intuitive_timing')

        return analysis

    def _generate_context_phrase(self, drift_entry, context_data, drift_reason):
        """Generate enhanced contextual information"""

        phrases = []

        # Tag context
        if drift_entry.tags.exists():
            tag_count = drift_entry.tags.count()
            shared_tags = context_data.get('shared_tags', [])
            print(f'REASON:{drift_reason}')
            if shared_tags:
                if len(shared_tags) == 1:
                    phrases.append(f"tagged {shared_tags[0].name} - reconnecting themes")
                else:
                    phrases.append("multiple shared themes surfacing")
            else:
                if tag_count == 1:
                    phrases.append(f"tagged {drift_entry.tags.first().name}")
                elif tag_count <= 3:
                    phrases.append(f"{tag_count} themes interweaving")

        # Temporal context
        days_ago = context_data.get('days_ago', 0)
        if days_ago == 0:
            phrases.append("today's thoughts resurfacing")
        elif days_ago == 1:
            phrases.append("yesterday's echo returning")
        elif 2 <= days_ago <= 3:
            phrases.append("recent days unearthed")
        elif 4 <= days_ago <= 6:
            phrases.append("this week's fragments rediscovered")
        elif 7 <= days_ago <= 14:
            phrases.append("last week's echoes resounding")
        elif 15 <= days_ago <= 21:
            phrases.append("recent weeks' wisdom resurfacing")
        elif 22 <= days_ago <= 30:
            phrases.append("this month's patterns reemerging")
        elif 31 <= days_ago <= 60:
            phrases.append("last month's memories excavated")
        elif 61 <= days_ago <= 90:
            phrases.append("seasonal insights unearthed")
        elif 91 <= days_ago <= 180:
            phrases.append("half-year cycles returning")
        elif 181 <= days_ago <= 365:
            phrases.append("year-old wisdom resurfacing")
        elif 366 <= days_ago <= 730:
            phrases.append("annual patterns reemerging")
        else:
            phrases.append("ancient archives rediscovered")

        # Mode alignment
        if drift_reason == "mode_connection":
            active_mode = context_data.get("active_mode", "current mode").title()
            phrases.append(f"{active_mode} tune")

        if drift_reason == "temporal_cycle":
            phrases.append("Echoing a familiar cycle")

        # Reconnecting themes
        if drift_reason == "reconnecting_themes":
            theme = context_data.get("contextual_analysis", {}).get("insight_type", "recurring thread")
            phrases.append(f"reconnecting themes: {theme}")

        # Random drift
        if drift_reason == "serendipity":
            phrases.append("a spontaneous drift without clear pattern")

        return " • ".join(phrases[:3])  # still keep max 2 for brevity

    def _select_mood_descriptor(self, drift_reason, analysis):
        """Select mood descriptor based on enhanced analysis"""

        base_descriptors = self.commentary_templates.get(drift_reason, {}).get('mood_descriptors', ['meaningful'])

        # Enhance based on connection strength
        if analysis.get('connection_strength') == 'strong':
            enhanced_descriptors = ['resonant', 'aligned', 'connected', 'significant']
            base_descriptors.extend(enhanced_descriptors)

        return random.choice(base_descriptors)

    def _categorize_time_distance(self, days_ago):
        """Enhanced temporal categorization"""
        if days_ago < 7:
            return "recent reflections"
        elif days_ago < 30:
            return "last month's insights"
        elif days_ago < 90:
            return "seasonal processing"
        elif days_ago < 365:
            return "deeper archives"
        else:
            return "ancient wisdom"

    def _get_random_prompt_pattern(self, active_mode):
        """Return a randomized prompt pattern to vary AI responses"""
        logger = logging.getLogger("drift_commentary")

        pattern_types = [
            # Direct reminder patterns
            {
                "instruction": (
                    "Offer a clear, practical reminder of how the user previously navigated "
                    "a similar situation, drawing naturally from the memory itself without "
                    "referring to it as an 'entry' or 'note.' Keep the language in the "
                    "{mode_config['style']} tone."
                ),
                "examples": {
                    "spiritual": "That prayer still holds the same peace — return to it.",
                    "visionary": "You already mapped this territory — trust your old bearings.",
                    "exploratory": "This curiosity path is one you've walked with good results.",
                    "productive": "That system served you well before — reactivate it.",
                    "creative": "You found flow here once — the channel remains open.",
                    "medical": "Your body responded well to this rhythm — listen again.",
                    "philosophical": "This insight hasn't aged — apply it with new eyes.",
                    "mystical": "The same hidden hand guides you to familiar waters."
                }
            },
            # Reflaction
            {
                "instruction": (
                    "State the connection or insight directly, without framing it as advice, "
                    "a question, or a metaphor. Simply reflect what is evident, in "
                    "{mode_config['style']} tone."
                ),
                "examples": {
                    "spiritual": "The same peace that once filled you is present in today’s words.",
                    "visionary": "The vision you held before is showing itself again in your current steps.",
                    "exploratory": "The curiosity you noted earlier flows into your reflections now.",
                    "productive": "Your past structure is mirrored in the effort you describe today.",
                    "creative": "The inspiration you once caught appears here in new form.",
                    "medical": "The same strain your body carried before is present in your recent notes.",
                    "philosophical": "The idea you wrestled with then is clearly alive in these lines now.",
                    "mystical": "The same thread of mystery you glimpsed earlier runs through this moment."
                }
            },
            # Questioning prompt patterns
            {
                "instruction": (
                    "Pose a reflective question that hints at the recurring wisdom. Anchor it "
                    "in the resurfaced entry's theme so it feels relevant, but never call it "
                    "an 'entry' or describe it as a record. Tone should remain in "
                    "{mode_config['style']}."
                ),
                "examples": {
                    "spiritual": "Doesn't this peace feel like one you've cultivated before?",
                    "visionary": "Haven't you already envisioned a version of this future?",
                    "exploratory": "What did you discover last time this curiosity struck?",
                    "productive": "Remember how this method simplified things before?",
                    "creative": "Doesn't this idea resonate with an old inspiration?",
                    "medical": "When did this rhythm previously bring you balance?",
                    "philosophical": "How did you unravel this paradox the first time?",
                    "mystical": "Isn't this the same coincidence that once guided you?"
                }
            },
            # Metaphor
            {
                "instruction": (
                    "Speak in metaphor, likening the resurfaced memory to a symbol, element, or rhythm. "
                    "Do not name it as an entry or a note. "
                    "Keep the tone aligned with {mode_config['style']}."
                ),
                "examples": {
                    "spiritual": "Like a bell that rings again, the same peace resounds within you.",
                    "visionary": "The old spark is a lighthouse — guiding today’s uncertain horizon.",
                    "exploratory": "This moment circles back like a path through a familiar forest.",
                    "productive": "The pattern reappears like gears clicking into place once more.",
                    "creative": "The echo returns like paint still wet on a hidden canvas.",
                    "medical": "The body recalls its balance as tides recall the shore.",
                    "philosophical": "The wheel of thought turns again, tracing its old arc in new light.",
                    "mystical": "The same constellation glimmers above, aligning you with forgotten stars."
                }
            }
        ]

        mode_pattern_weights = {
            "spiritual": [30, 20, 25, 25],
            "visionary": [35, 25, 25, 15],
            "exploratory": [25, 25, 35, 15],
            "productive": [45, 35, 15, 5],
            "creative": [30, 20, 20, 30],
            "medical": [40, 35, 20, 5],
            "philosophical": [25, 25, 35, 15],
            "mystical": [20, 15, 20, 45],
        }

        mode_key = active_mode.lower()
        weights = mode_pattern_weights.get(mode_key, [35, 25, 25, 15])
        selected_pattern = random.choices(pattern_types, weights=weights, k=1)[0]

        logger.info(
            f"[Pattern Selection] Mode='{mode_key}' | Weights={weights} | Selected='{selected_pattern['instruction'][:40]}...'"
        )

        return {
            'instruction': selected_pattern['instruction'],
            'example': selected_pattern['examples'].get(
                mode_key,
                "This pattern returns with wisdom you've gathered before."
            )
        }


class AmbientDriftView(View):
    """Serve ambient drift content with AI commentary - old notes that resurface"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commentary_service = DriftCommentaryService()

    def get(self, request):
        logger = logging.getLogger('ambient_drift')
        user = request.user
        self.request = request

        logger.info(f"Drift request for user: {user.username}")

        # Check if we have viable drift content
        drift_entry = self._select_drift_entry(user)

        if drift_entry:
            drift_reason = self._get_drift_reason(drift_entry)

            # Weighted probability based on relevance
            if drift_reason == 'mode_connection':
                probability = 1.0  # 100% chance for mode-connected entries
            elif drift_reason == 'tag_connection':
                probability = 0.7  # 70% chance for tag-connected entries
            else:
                probability = 0.4  # 40% chance for temporal/serendipity discoveries

            random_roll = random.random()
            logger.info(f"Found {drift_reason} entry, probability: {probability}, roll: {random_roll:.2f}")

            if random_roll <= probability:
                days_ago = (timezone.now() - drift_entry.created_at).days

                # Generate enhanced AI commentary
                commentary = self._generate_commentary_for_entry(drift_entry, drift_reason, days_ago)

                logger.info(f"Showing drift entry: ID {drift_entry.id}, {days_ago} days old, reason: {drift_reason}")
                context = {
                    'drift_entry': drift_entry,
                    'days_ago': days_ago,
                    'drift_reason': drift_reason,
                    'commentary': commentary
                }
                return render(request, 'journal/stream/partials/ambient_drift.html', context)
            else:
                logger.info(f"Skipped showing drift entry due to probability ({random_roll:.2f} > {probability})")
        else:
            logger.info("No drift candidates found")

        return render(request, 'journal/stream/partials/ambient_drift.html', {'drift_entry': None})

    def _generate_commentary_for_entry(self, drift_entry, drift_reason, days_ago):
        """Generate commentary using enhanced contextual analysis"""
        logger = logging.getLogger('ambient_drift')

        # Get active mode
        try:
            # from ..utils import get_active_mode
            active_mode = get_active_mode(self.request)
            if not active_mode:
                active_mode = 'philosophical'
                logger.warning("Active mode object missing slug, defaulting to philosophical")
        except Exception as e:
            logger.error(f"Error getting active mode: {e}")
            active_mode = 'philosophical'

        # Get recent entries (last 2)
        recent_entries = self._get_recent_entries(drift_entry.user, limit=2)

        # Prepare recent entries content for the prompt
        recent_entries_content = []
        for i, entry in enumerate(recent_entries):
            # preview = entry.content[:150] + "..." if len(entry.content) > 150 else entry.content
            preview = entry.content
            recent_entries_content.append(f"Recent entry {i + 1}: '{preview}'")

        recent_content_text = "\n".join(recent_entries_content)

        # Rest of your context data setup...
        context_data = {
            'days_ago': days_ago,
            'active_mode': active_mode,
            'recent_entries': recent_entries,
            'recent_entries_content': recent_content_text  # Add this for the prompt
        }

        # Add shared tags for tag connections
        if drift_reason == 'tag_connection':
            recent_tags = self._get_recent_user_tags(drift_entry.user)
            shared_tags = [tag for tag in recent_tags
                           if drift_entry.tags.filter(id=tag.id).exists()]
            context_data['shared_tags'] = shared_tags
            logger.info(f"Shared tags: {[tag.name for tag in shared_tags]}")

        # Enhanced contextual analysis
        recent_content_patterns = self._analyze_recent_content_patterns(drift_entry.user)
        context_data['content_patterns'] = recent_content_patterns

        logger.info(f"Enhanced context data prepared with recent entries: {recent_content_text}")

        # Generate AI commentary with enhanced context
        return self.commentary_service.generate_drift_commentary(
            drift_entry, drift_reason, context_data
        )

    def _select_drift_entry(self, user):
        """Select entry for drift based on weighted criteria with mode-aware selection"""
        logger = logging.getLogger('ambient_drift')

        # Get current active mode
        try:
            # from ..utils import get_active_mode
            active_mode = get_active_mode(self.request)
            logger.info(f"Active mode for drift selection: '{active_mode}'")
        except Exception as e:
            logger.error(f"Error getting active mode for drift selection: {e}")
            active_mode = 'philosophical'

        # Base criteria: 3+ days old, exclude recent drifts
        min_age = timezone.now() - timedelta(days=3)
        base_query = JournalEntry.objects.filter(
            user=user,
            created_at__lt=min_age
        )

        total_old_entries = base_query.count()
        logger.info(f"Total entries older than 3 days: {total_old_entries}")

        if total_old_entries == 0:
            logger.info("No entries older than 3 days found")
            return None

        # Exclude recently drifted entries
        recent_drift_ids = self._get_recent_drift_ids(user)
        base_query = base_query.exclude(id__in=recent_drift_ids)
        available_entries = base_query.count()
        logger.info(f"Available entries after excluding recent drifts: {available_entries}")

        if available_entries == 0:
            logger.info("No available entries after excluding recent drifts")
            return None

        # PRIORITY 1: Mode-relevant entries (100% selection probability)
        try:
            mode_relevant_entry = self._find_mode_relevant_entry(user, base_query, active_mode)
            if mode_relevant_entry:
                logger.info(f"SUCCESS: Found mode-relevant entry ID {mode_relevant_entry.id} for mode '{active_mode}'")
                return mode_relevant_entry
            else:
                logger.info(f"No mode-relevant entries found for '{active_mode}', falling back to standard selection")
        except Exception as e:
            logger.error(f"Error in mode-relevant selection: {e}, falling back to standard selection")

        # FALLBACK: Original weighted selection logic
        candidates = []

        # 2. Tag-connected entries (high priority)
        recent_tags = self._get_recent_user_tags(user)
        logger.info(f"Recent tags: {[tag.name for tag in recent_tags]}")

        if recent_tags:
            tag_related = base_query.filter(tags__in=recent_tags).distinct()[:8]
            tag_related_list = list(tag_related)
            logger.info(f"Tag-related candidates: {len(tag_related_list)} entries")
            candidates.extend([(entry, 3) for entry in tag_related_list])
        else:
            logger.info("No recent tags found for tag-based selection")

        # 3. Temporal pattern entries (cyclical timing)
        try:
            cyclical_entries = self._find_cyclical_entries(user, base_query)
            logger.info(f"Cyclical candidates: {len(cyclical_entries)} entries")
            candidates.extend([(entry, 2) for entry in cyclical_entries])
        except Exception as e:
            logger.error(f"Error finding cyclical entries: {e}")

        # 4. Random discoveries from archives
        try:
            very_old = base_query.filter(
                created_at__lt=timezone.now() - timedelta(days=14)
            ).order_by('?')[:3]
            very_old_list = list(very_old)
            logger.info(f"Archive candidates (14+ days): {len(very_old_list)} entries")
            candidates.extend([(entry, 1) for entry in very_old_list])
        except Exception as e:
            logger.error(f"Error finding archive entries: {e}")

        if not candidates:
            logger.warning("No candidates found in any category")
            return None

        # Remove duplicates while preserving highest weight
        unique_candidates = {}
        for entry, weight in candidates:
            if entry.id not in unique_candidates or unique_candidates[entry.id][1] < weight:
                unique_candidates[entry.id] = (entry, weight)

        final_candidates = list(unique_candidates.values())
        logger.info(f"Final unique candidates: {len(final_candidates)}")

        if final_candidates:
            selected = self._weighted_random_choice(final_candidates)
            if selected:
                logger.info(f"Selected entry ID {selected.id} from {selected.created_at} via fallback selection")
                return selected
            else:
                logger.warning("Weighted random choice failed to select an entry")
        else:
            logger.warning("No final candidates after deduplication")

        return None

    def _find_cyclical_entries(self, user, base_query):
        """Find entries that might represent cyclical patterns"""
        logger = logging.getLogger('ambient_drift')

        # Look for entries from similar time periods (weekly/monthly cycles)
        now = timezone.now()

        # Weekly cycle - same day of week from previous weeks
        same_weekday = base_query.filter(
            created_at__week_day=now.weekday() + 1  # Django uses 1-7 for Sunday-Saturday
        )[:3]

        # Monthly cycle - similar date from previous months
        same_day_of_month = base_query.filter(
            created_at__day=now.day
        )[:3]

        cyclical_candidates = list(same_weekday) + list(same_day_of_month)

        # Remove duplicates
        seen_ids = set()
        unique_cyclical = []
        for entry in cyclical_candidates:
            if entry.id not in seen_ids:
                unique_cyclical.append(entry)
                seen_ids.add(entry.id)

        logger.info(f"Found {len(unique_cyclical)} cyclical entries")
        return unique_cyclical[:5]  # Limit to 5

    def _analyze_recent_content_patterns(self, user):
        """Analyze recent entries to understand current themes and emotional patterns"""

        # Get last 5 entries
        recent_entries = self._get_recent_entries(user, limit=5)

        patterns = {
            'dominant_themes': [],
            'emotional_tone': 'neutral',
            'action_orientation': 'low',
            'solution_seeking': False,
            'reflection_depth': 'medium'
        }

        if not recent_entries:
            return patterns

        # Analyze content patterns
        all_content = ' '.join([entry.content.lower() for entry in recent_entries])

        # Check for solution-seeking language
        solution_words = ['how to', 'need to', 'should', 'trying to', 'figuring out',
                          'working on', 'planning', 'thinking about']
        if any(word in all_content for word in solution_words):
            patterns['solution_seeking'] = True

        # Check for action orientation
        action_words = ['will', 'going to', 'decided', 'plan to', 'working', 'doing', 'started']
        action_count = sum(1 for word in action_words if word in all_content)
        if action_count >= 3:
            patterns['action_orientation'] = 'high'
        elif action_count >= 1:
            patterns['action_orientation'] = 'medium'

        # Get dominant themes from tags
        all_tags = []
        for entry in recent_entries:
            all_tags.extend(list(entry.tags.all()))

        if all_tags:
            # Count tag frequency
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1

            # Get most frequent themes
            sorted_themes = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            patterns['dominant_themes'] = [theme[0] for theme in sorted_themes[:3]]

        return patterns

    def _get_recent_user_tags(self, user, days=7):
        """Get recent tags with testing mode option"""
        logger = logging.getLogger('ambient_drift')

        TEST_MODE = True  # Set to False to go back to normal

        if TEST_MODE:
            # TEST MODE: Get tags from last 3 entries
            last_entries = JournalEntry.objects.filter(
                user=user
            ).prefetch_related('tags').order_by('-created_at')[:3]

            recent_tags = set()
            tag_names = set()  # Just for logging

            for entry in last_entries:
                entry_tags = list(entry.tags.all())
                recent_tags.update(entry_tags)
                tag_names.update(tag.name for tag in entry_tags)

            logger.info(f" TEST MODE: Tag names: {list(tag_names)}")

            return list(recent_tags)




        else:
            # NORMAL MODE: Get tags from last 7 days
            since = timezone.now() - timedelta(days=days)
            tags = Tag.objects.filter(
                entries__user=user,
                entries__created_at__gte=since
            ).distinct()[:5]

            tag_names = [tag.name for tag in tags]
            logger.info(f"Normal mode recent tags: {tag_names}")

            return list(tags)

    def _get_recent_drift_ids(self, user):
        """Get recently drifted entry IDs to avoid repetition"""
        session_key = f'drifted_entries_{user.id}'
        recent_drift_ids = self.request.session.get(session_key, [])
        return recent_drift_ids[-15:] if recent_drift_ids else []  # Increased to 15

    def _get_recent_entries(self, user, limit=5):
        """Get recent entries for context"""
        return JournalEntry.objects.filter(
            user=user
        ).prefetch_related('tags').order_by('-created_at')[:limit]

    def _weighted_random_choice(self, candidates):
        """Select entry based on weights"""
        logger = logging.getLogger('ambient_drift')

        if not candidates:
            return None

        total_weight = sum(weight for _, weight in candidates)
        logger.debug(f"Total weight: {total_weight} from {len(candidates)} candidates")

        if total_weight == 0:
            selected = random.choice(candidates)[0] if candidates else None
        else:
            r = random.uniform(0, total_weight)
            current_weight = 0
            selected = None

            for entry, weight in candidates:
                current_weight += weight
                if r <= current_weight:
                    selected = entry
                    break

            if not selected and candidates:
                selected = candidates[-1][0]

        if selected:
            self._track_drift_selection(selected)
            logger.info(f"Selected entry {selected.id}")

        return selected

    def _track_drift_selection(self, entry):
        """Track that this entry was selected for drift"""
        session_key = f'drifted_entries_{entry.user.id}'
        recent_drifts = self.request.session.get(session_key, [])
        recent_drifts.append(entry.id)
        self.request.session[session_key] = recent_drifts[-15:]  # Keep last 15

    def _find_mode_relevant_entry(self, user, base_query, active_mode):
        """Find entries that naturally align with the current active mode"""
        logger = logging.getLogger('ambient_drift')

        # Define mode-specific keywords and patterns
        mode_keywords = {
            'spiritual': {
                'keywords': ['prayer', 'faith', 'blessing', 'grace', 'divine', 'sacred', 'soul',
                             'spirit', 'meditation', 'peace', 'gratitude', 'worship', 'holy',
                             'miracle', 'church', 'god', 'universe', 'prayer', 'thankful'],
                'patterns': ['praying', 'blessed', 'grateful', 'faithful', 'peaceful']
            },
            'visionary': {
                'keywords': ['future', 'vision', 'dream', 'goal', 'plan', 'imagine', 'possibility',
                             'breakthrough', 'innovation', 'transform', 'change', 'opportunity',
                             'potential', 'aspire', 'ambition', 'create', 'build'],
                'patterns': ['planning', 'envisioning', 'dreaming', 'building', 'creating']
            },
            'exploratory': {
                'keywords': ['discover', 'explore', 'curious', 'wonder', 'question', 'investigate',
                             'adventure', 'journey', 'learn', 'experiment', 'try', 'new', 'unknown',
                             'mystery', 'search', 'find', 'research'],
                'patterns': ['exploring', 'wondering', 'questioning', 'discovering', 'learning']
            },
            'productive': {
                'keywords': ['work', 'task', 'goal', 'accomplish', 'complete', 'finish', 'organize',
                             'system', 'method', 'efficient', 'productive', 'schedule', 'plan',
                             'priority', 'focus', 'result', 'achieve'],
                'patterns': ['working', 'organizing', 'planning', 'achieving', 'completing']
            },
            'creative': {
                'keywords': ['create', 'art', 'design', 'write', 'music', 'paint', 'draw', 'craft',
                             'inspire', 'imagination', 'creative', 'artistic', 'beautiful', 'express',
                             'flow', 'idea', 'original'],
                'patterns': ['creating', 'writing', 'designing', 'painting', 'expressing']
            },
            'medical': {
                'keywords': ['health', 'body', 'pain', 'healing', 'medicine', 'doctor', 'symptom',
                             'treatment', 'wellness', 'exercise', 'sleep', 'nutrition', 'energy',
                             'recovery', 'therapy', 'care', 'balance'],
                'patterns': ['healing', 'recovering', 'treating', 'caring', 'resting']
            },
            'philosophical': {
                'keywords': ['think', 'thought', 'meaning', 'purpose', 'wisdom', 'truth', 'reality',
                             'existence', 'understand', 'reflect', 'contemplate', 'reason', 'logic',
                             'question', 'perspective', 'insight', 'knowledge'],
                'patterns': ['thinking', 'reflecting', 'contemplating', 'understanding', 'reasoning']
            },
            'mystical': {
                'keywords': ['magic', 'mysterious', 'synchronicity', 'intuition', 'cosmic', 'energy',
                             'universe', 'connection', 'signs', 'symbols', 'dreams', 'spiritual',
                             'mystical', 'transcendent', 'awareness', 'consciousness', 'flow'],
                'patterns': ['connecting', 'sensing', 'feeling', 'experiencing', 'transcending']
            }
        }

        mode_config = mode_keywords.get(active_mode.lower(), mode_keywords['philosophical'])

        logger.info(f"Searching for {active_mode} entries with keywords: {mode_config['keywords'][:5]}...")

        # Search for entries containing mode-relevant keywords
        content_queries = []

        try:
            # Build Q objects for keyword search
            for keyword in mode_config['keywords']:
                content_queries.append(Q(content__icontains=keyword))

            for pattern in mode_config.get('patterns', []):
                content_queries.append(Q(content__icontains=pattern))

            if not content_queries:
                logger.warning(f"No search queries built for mode '{active_mode}' - keyword configuration issue")
                return None

            # Combine all queries with OR
            combined_query = content_queries[0]
            for query in content_queries[1:]:
                combined_query |= query

            mode_relevant_entries = base_query.filter(combined_query).order_by('?')[:5]
            mode_relevant_list = list(mode_relevant_entries)

            logger.info(f"Found {len(mode_relevant_list)} mode-relevant entries for '{active_mode}'")

            if mode_relevant_list:
                # Select the best match
                selected = self._select_best_mode_match(mode_relevant_list, mode_config, active_mode)
                if selected:
                    self._track_drift_selection(selected)
                    logger.info(f"Successfully selected mode-relevant entry ID {selected.id}")
                    return selected
                else:
                    logger.warning(f"Mode search found {len(mode_relevant_list)} entries but none scored well enough")
            else:
                logger.info(f"No entries matched mode keywords for '{active_mode}'")

        except Exception as e:
            logger.error(f"Error during mode-relevant entry search for '{active_mode}': {e}")
            return None

        logger.info(f"Mode-relevant search completed with no viable candidates for '{active_mode}'")
        return None

    def _select_best_mode_match(self, entries, mode_config, active_mode):
        """Select the entry that best matches the mode from candidates"""
        logger = logging.getLogger('ambient_drift')

        if not entries:
            logger.warning("_select_best_mode_match called with empty entries list")
            return None

        try:
            # Score entries based on keyword frequency
            scored_entries = []

            for entry in entries:
                content_lower = entry.content.lower()
                score = 0
                matched_keywords = []

                # Count keyword matches
                for keyword in mode_config['keywords']:
                    keyword_count = content_lower.count(keyword.lower())
                    if keyword_count > 0:
                        score += keyword_count
                        matched_keywords.append(keyword)

                for pattern in mode_config.get('patterns', []):
                    pattern_count = content_lower.count(pattern.lower())
                    if pattern_count > 0:
                        score += pattern_count * 1.5  # Patterns get higher weight
                        matched_keywords.append(f"{pattern}(pattern)")

                # Boost score for entries with mode-related tags
                mode_related_tags = self._get_mode_related_tags(active_mode)
                tag_matches = []
                for tag in entry.tags.all():
                    if tag.name.lower() in mode_related_tags:
                        score += 3  # Tag matches get high boost
                        tag_matches.append(tag.name)

                if score > 0:
                    logger.debug(
                        f"Entry {entry.id} scored {score} with keywords: {matched_keywords[:3]} and tags: {tag_matches}")

                scored_entries.append((entry, score, matched_keywords, tag_matches))

            # Filter out zero-score entries
            viable_entries = [(entry, score, kw, tags) for entry, score, kw, tags in scored_entries if score > 0]

            if not viable_entries:
                logger.info(f"All {len(scored_entries)} candidate entries scored 0 for mode '{active_mode}'")
                return None

            # Sort by score descending
            viable_entries.sort(key=lambda x: x[1], reverse=True)

            best_entry, best_score, best_keywords, best_tags = viable_entries[0]
            logger.info(f"Selected best mode match: Entry {best_entry.id} with score {best_score}")
            logger.debug(f"Best entry keywords: {best_keywords[:5]} tags: {best_tags}")

            return best_entry

        except Exception as e:
            logger.error(f"Error in _select_best_mode_match for mode '{active_mode}': {e}")
            # Fallback to random selection
            if entries:
                selected = random.choice(entries)
                logger.info(f"Error fallback: selected random entry {selected.id}")
                return selected
            return None

    def _get_mode_related_tags(self, active_mode):
        """Get tag names that commonly relate to specific modes"""
        logger = logging.getLogger('ambient_drift')
        mode_tag_mapping = {
            'spiritual': ['faith', 'prayer', 'meditation', 'gratitude', 'church', 'soul', 'peace'],
            'visionary': ['goals', 'future', 'dreams', 'plans', 'vision', 'ambition', 'innovation'],
            'exploratory': ['learning', 'discovery', 'curiosity', 'adventure', 'research', 'experiment'],
            'productive': ['work', 'productivity', 'goals', 'tasks', 'organization', 'efficiency'],
            'creative': ['art', 'creativity', 'writing', 'music', 'design', 'inspiration', 'flow'],
            'medical': ['health', 'wellness', 'healing', 'exercise', 'sleep', 'recovery', 'therapy'],
            'philosophical': ['wisdom', 'reflection', 'thoughts', 'philosophy', 'meaning', 'truth'],
            'mystical': ['magic', 'intuition', 'synchronicity', 'energy', 'cosmic', 'mystery']
        }

        tags = mode_tag_mapping.get(active_mode.lower(), [])
        if not tags:
            logger.debug(f"No mode-related tags found for '{active_mode}', using empty list")
        return tags

    def _get_drift_reason(self, entry):
        """Return why this entry was selected (now includes mode_connection)"""
        logger = logging.getLogger('ambient_drift')

        # Check for mode connection first
        try:

            # active_mode = get_active_mode(self.request)
            mode_config = self._get_mode_keywords(active_mode)

            if self._entry_matches_mode(entry, mode_config):
                logger.debug(f"Entry {entry.id} identified as mode_connection for '{active_mode}'")
                return "mode_connection"
        except Exception as e:
            logger.error(f"Error checking mode connection for entry {entry.id}: {e}")

        # Check for tag connection
        try:
            recent_tags = self._get_recent_user_tags(entry.user)
            if entry.tags.filter(id__in=[tag.id for tag in recent_tags]).exists():
                logger.debug(f"Entry {entry.id} identified as tag_connection")
                return "tag_connection"
        except Exception as e:
            logger.error(f"Error checking tag connection for entry {entry.id}: {e}")

        # Check for cyclical patterns
        try:
            now = timezone.now()
            if (entry.created_at.weekday() == now.weekday() or
                    entry.created_at.day == now.day):
                logger.debug(f"Entry {entry.id} identified as temporal_connection")
                return "temporal_connection"
        except Exception as e:
            logger.error(f"Error checking temporal connection for entry {entry.id}: {e}")

        logger.debug(f"Entry {entry.id} classified as serendipity (fallback)")
        return "serendipity"

    def _get_mode_keywords(self, active_mode):
        """Get keywords for mode matching"""
        logger = logging.getLogger('ambient_drift')
        mode_keywords = {
            'spiritual': ['prayer', 'faith', 'blessing', 'grace', 'divine', 'sacred'],
            'visionary': ['future', 'vision', 'dream', 'goal', 'plan', 'possibility'],
            'exploratory': ['discover', 'explore', 'curious', 'wonder', 'question'],
            'productive': ['work', 'task', 'accomplish', 'organize', 'efficient'],
            'creative': ['create', 'art', 'design', 'inspire', 'imagination'],
            'medical': ['health', 'body', 'healing', 'wellness', 'recovery'],
            'philosophical': ['think', 'meaning', 'wisdom', 'truth', 'reflect'],
            'mystical': ['magic', 'mysterious', 'synchronicity', 'intuition', 'cosmic']
        }
        keywords = mode_keywords.get(active_mode.lower(), [])
        if not keywords:
            logger.warning(f"No keywords found for mode '{active_mode}', using empty list")
        return keywords

    def _entry_matches_mode(self, entry, mode_keywords):
        """Check if entry contains mode-relevant keywords"""
        logger = logging.getLogger('ambient_drift')
        if not mode_keywords:
            return False

        try:
            content_lower = entry.content.lower()
            matches = [keyword.lower() for keyword in mode_keywords if keyword.lower() in content_lower]

            if matches:
                logger.debug(f"Entry {entry.id} matches mode keywords: {matches[:3]}")
                return True
            else:
                logger.debug(f"Entry {entry.id} does not match any mode keywords")
                return False

        except Exception as e:
            logger.error(f"Error checking mode keywords for entry {entry.id}: {e}")
            return False


class StreamPulseView(View):
    """Generate dynamic stream pulse based on user activity patterns"""

    def get(self, request):
        logger = logging.getLogger('stream_pulse')
        user = request.user

        pulse_data = self._analyze_user_pulse(user)
        logger.info(f"Generated pulse for {user.username}: {pulse_data['pattern']}")

        return render(request, 'journal/stream/partials/stream_pulse.html', pulse_data)

    def _analyze_user_pulse(self, user):
        """Analyze user's journaling patterns to generate pulse"""
        now = timezone.now()

        # Activity windows
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Get entry counts
        today_count = JournalEntry.objects.filter(
            user=user,
            created_at__date=today
        ).count()

        week_count = JournalEntry.objects.filter(
            user=user,
            created_at__gte=week_ago
        ).count()

        month_count = JournalEntry.objects.filter(
            user=user,
            created_at__gte=month_ago
        ).count()

        # Calculate patterns
        daily_average = week_count / 7 if week_count > 0 else 0
        consistency_score = self._calculate_consistency(user, week_ago)

        # Determine pulse pattern and message
        pulse_pattern, message, intensity = self._get_pulse_characteristics(
            today_count, daily_average, consistency_score, week_count
        )

        return {
            'pattern': pulse_pattern,
            'message': message,
            'intensity': intensity,
            'today_count': today_count,
            'week_count': week_count,
            'daily_average': round(daily_average, 1),
            'consistency_score': consistency_score,
            'show_pulse': True
        }

    def _calculate_consistency(self, user, since_date):
        """Calculate how consistently user has been journaling"""
        from django.db.models import Count

        # Count entries per day
        daily_counts = JournalEntry.objects.filter(
            user=user,
            created_at__gte=since_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            entries=Count('id')
        ).order_by('day')

        if not daily_counts:
            return 0

        # Calculate consistency (days with entries / total days)
        days_with_entries = len(daily_counts)
        total_days = 7
        return min(100, (days_with_entries / total_days) * 100)

    def _get_pulse_characteristics(self, today_count, daily_average, consistency, week_count):
        """Determine pulse visual pattern and message based on activity"""

        # High activity today
        if today_count >= 3:
            if consistency > 70:
                return 'flowing', 'You\'re in deep flow today', 'high'
            else:
                return 'bursting', 'Creative burst happening', 'high'

        # Good consistent activity
        elif consistency > 80 and daily_average >= 1:
            return 'steady', 'You\'ve been flowing consistently', 'medium'

        # Moderate activity
        elif today_count >= 1 or daily_average >= 0.5:
            if consistency > 50:
                return 'gentle', 'Gentle rhythm building', 'medium'
            else:
                return 'sporadic', 'Ideas coming in waves', 'low'

        # Low activity
        elif week_count > 0:
            return 'quiet', 'Quiet reflection period', 'low'

        # No recent activity
        else:
            return 'dormant', 'Stream waiting for your thoughts', 'minimal'


class StreamStatsView(View):
    """Provide detailed stream statistics for pulse tooltips/chart_modals"""

    def get(self, request):
        user = request.user

        stats = self._get_detailed_stats(user)
        return JsonResponse(stats)

    def _get_detailed_stats(self, user):
        """Get comprehensive journaling statistics"""
        from django.db.models import Count, Avg
        from django.db.models.functions import TruncDate, TruncHour

        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Basic counts
        total_entries = JournalEntry.objects.filter(user=user).count()
        week_entries = JournalEntry.objects.filter(user=user, created_at__gte=week_ago).count()

        # Peak activity hours
        hourly_activity = JournalEntry.objects.filter(
            user=user, created_at__gte=week_ago
        ).extra(
            select={'hour': 'EXTRACT(hour FROM created_at)'}
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('-count')[:3]

        peak_hours = [int(item['hour']) for item in hourly_activity if item['count'] > 0]

        # Most active days
        daily_activity = JournalEntry.objects.filter(
            user=user, created_at__gte=week_ago
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('-count')

        # Streak calculation
        streak = self._calculate_streak(user)

        return {
            'total_entries': total_entries,
            'week_entries': week_entries,
            'peak_hours': peak_hours,
            'current_streak': streak,
            'most_active_day': daily_activity[0]['day'] if daily_activity else None,
            'avg_daily': round(week_entries / 7, 1)
        }

    def _calculate_streak(self, user):
        """Calculate current journaling streak in days"""
        from datetime import date

        today = timezone.now().date()
        streak = 0
        current_date = today

        while True:
            has_entry = JournalEntry.objects.filter(
                user=user,
                created_at__date=current_date
            ).exists()

            if has_entry:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break

            # Prevent infinite loops
            if streak > 365:
                break

        return streak