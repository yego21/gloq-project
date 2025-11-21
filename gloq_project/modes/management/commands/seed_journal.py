import random
from datetime import timedelta, datetime, time
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from journal.models import JournalEntry, Tag

# Sample content with coherent tag associations
SAMPLE_ENTRIES_WITH_TAGS = [
    # Sample content with coherent tag associations - raw scribble style

    {
        "content": "Woke up before the alarm again, body feels heavy like yesterday. Coffee machine making weird noise. Mind already racing about that meeting later. Should probably eat something.",
        "tags": ["anxiety", "exhaustion"]
    },
    {
        "content": "Sunlight hitting the wall in that same pattern. Dreamt about the old apartment again. Forgot to buy milk. Head feels fuzzy, need water.",
        "tags": ["nostalgia", "mindfulness"]
    },
    {
        "content": "Slept through the alarm, rushed to get ready. Can't find my keys anywhere. Traffic was terrible. Already tired and it's only 9 AM.",
        "tags": ["frustration", "overwhelm"]
    },
    {
        "content": "Woke up with that song stuck in my head from yesterday. Weather's nice but cold. Should go for a walk later if time permits.",
        "tags": ["curiosity", "optimism"]
    },
    {
        "content": "Stomach feels off this morning. Dreamt about work again, can't shake the stress. Need to remember to call mom today.",
        "tags": ["anxiety", "connection"]
    },

    # Mid-day entries (second of day)
    {
        "content": "Lunch alone at the desk again. Emails piling up. That conversation from earlier keeps replaying in my head. Should've said something different.",
        "tags": ["self_doubt", "overthinking"]
    },
    {
        "content": "Got lost in work and missed lunch. Neck hurts from staring at screen. Sun came out briefly then disappeared. Need to move around.",
        "tags": ["focus", "exhaustion"]
    },
    {
        "content": "Random thought: why do we keep doing the same things expecting different results? Coffee isn't working today. Mind wandering to vacation ideas.",
        "tags": ["introspection", "restlessness"]
    },
    {
        "content": "Solved that problem that was bothering me all morning. Small win. Colleague brought cookies. Mood lifting slightly.",
        "tags": ["accomplishment", "positivity"]
    },
    {
        "content": "Keep checking phone for no reason. Distracted easily today. That notification sound is getting annoying. Should put it on silent.",
        "tags": ["overwhelm", "frustration"]
    },

    # Evening entries (third of day)
    {
        "content": "Day dragged on forever. Traffic home was worse than this morning. Leftovers for dinner again. Too tired to cook. Just want to sleep.",
        "tags": ["exhaustion", "resignation"]
    },
    {
        "content": "Walked home instead of taking bus. Saw the sunset between buildings. Felt peaceful for a moment. Now back to reality and chores.",
        "tags": ["mindfulness", "serenity"]
    },
    {
        "content": "Scrolled through photos from last year. Time moves too fast. Should message that friend I've been thinking about. Always put it off.",
        "tags": ["nostalgia", "connection"]
    },
    {
        "content": "Couldn't focus on the movie, mind kept drifting to work stuff. Ate too much junk food. Regret the entire day's choices honestly.",
        "tags": ["self_doubt", "frustration"]
    },
    {
        "content": "Finished that book I've been reading. Ending was unsatisfying. Rain started outside. Cozy but lonely feeling. Tea helps.",
        "tags": ["comfort", "loneliness"]
    },

    # More varied entries
    {
        "content": "Keep forgetting where I put things. Keys, phone, wallet. Same cycle every day. Need to establish better habits but too tired to start.",
        "tags": ["overwhelm", "frustration"]
    },
    {
        "content": "Random memory from childhood popped up while washing dishes. That smell of rain on concrete. Haven't thought about that in years.",
        "tags": ["nostalgia", "mindfulness"]
    },
    {
        "content": "Procrastinated on that task again. Why do I do this every time? Self-sabotage pattern continues. Need to break it somehow.",
        "tags": ["self_doubt", "frustration"]
    },
    {
        "content": "Saw a bird building a nest outside the window. Simple dedication. Made me think about my own projects. Need more of that focus.",
        "tags": ["inspiration", "reflection"]
    },
    {
        "content": "Weather changed suddenly. Cold now. Should've brought a jacket. Always unprepared. Story of my life really.",
        "tags": ["resignation", "self_reflection"]
    },
    {
        "content": "That song came on shuffle and hit differently today. Lyrics made sense in a new way. Funny how that happens.",
        "tags": ["perspective", "nostalgia"]
    },
    {
        "content": "Accomplished nothing today despite being busy all day. Where does the time go? Need to track time better tomorrow.",
        "tags": ["frustration", "self_reflection"]
    },
    {
        "content": "Made a decision without overthinking it for once. Felt good. Small progress. Should try that more often.",
        "tags": ["accomplishment", "optimism"]
    },
    {
        "content": "Keep having the same argument with myself in my head. Circular thoughts. Need to break the cycle but don't know how.",
        "tags": ["overthinking", "frustration"]
    },
    {
        "content": "Found an old note in my pocket from last week. Forgotten reminder. Time feels both fast and slow simultaneously.",
        "tags": ["nostalgia", "mindfulness"]
    },
    {
        "content": "Ate lunch too fast now stomach hurts. Rushed through everything today. Need to slow down but the pace feels unavoidable.",
        "tags": ["overwhelm", "frustration"]
    },
    {
        "content": "Saw someone who looked familiar but wasn't. That weird déjà vu feeling. Mind playing tricks again.",
        "tags": ["curiosity", "uncertainty"]
    },
    {
        "content": "Finally cleaned that area I've been avoiding. Small satisfaction. Why do I put off things that feel good to complete?",
        "tags": ["accomplishment", "self_reflection"]
    },
    {
        "content": "Keep checking the time every few minutes. Waiting for the day to end. Clock moves slower when you watch it.",
        "tags": ["restlessness", "frustration"]
    },
    {
        "content": "Random burst of energy in the afternoon. Got more done in an hour than the whole morning. Wish I could harness that consistently.",
        "tags": ["productivity", "motivation"]
    },
    {
        "content": "Thought about calling someone but didn't. Social anxiety wins again. Always the same pattern. Need to push through it.",
        "tags": ["anxiety", "self_doubt"]
    },
    {
        "content": "Wind sounds different tonight. Can't sleep. Mind won't quiet down. Same worries cycling through. Should write them down maybe.",
        "tags": ["overthinking", "anxiety"]
    },
    {
        "content": "Made a mistake at work. Can't stop thinking about it. Probably not a big deal but feels huge. Overreacting as usual.",
        "tags": ["self_doubt", "overthinking"]
    },
    {
        "content": "Found an old photo while cleaning. Smiled for a solid minute. Good memory. Should print more photos instead of digital only.",
        "tags": ["nostalgia", "positivity"]
    },
    {
        "content": "Keep putting off exercise. Tomorrow for sure. Said that yesterday too. Pattern continues.",
        "tags": ["frustration", "self_reflection"]
    }
]
#     {
#         "content": "Morning light carried an echo of dreams I couldn't quite remember.",
#         "tags": ["nostalgia", "reflection"]
#     },
#     {
#         "content": "A small hesitation today revealed something larger beneath my choices.",
#         "tags": ["introspection", "self_discovery"]
#     },
#     {
#         "content": "Patterns return in my thoughts, as if circling back to teach again.",
#         "tags": ["reflection", "perspective"]
#     },
#     {
#         "content": "Walking alone, I felt both the weight of time and its kindness.",
#         "tags": ["introspection", "serenity"]
#     },
#     {
#         "content": "An old song drifted in, stirring emotions I thought had long gone quiet.",
#         "tags": ["nostalgia", "emotion"]
#     },
#     {
#         "content": "Energy rose then fell quickly, like tides I cannot command.",
#         "tags": ["exhaustion", "frustration"]
#     },
#     {
#         "content": "I laughed suddenly, realizing how heavy I had made a simple moment.",
#         "tags": ["amusement", "perspective"]
#     },
#     {
#         "content": "The body whispered for rest, but the mind resisted with restless questions.",
#         "tags": ["exhaustion", "overthinking"]
#     },
#     {
#         "content": "Memories surfaced during coffee, blurring with the scent of the present.",
#         "tags": ["nostalgia", "mindfulness"]
#     },
#     {
#         "content": "A conversation left me unsettled, though no words explained why.",
#         "tags": ["uncertainty", "self_doubt"]
#     },
#     {
#         "content": "Silence today felt more like a teacher than any book I opened.",
#         "tags": ["mindfulness", "self_reflection"]
#     },
#     {
#         "content": "I noticed the rhythm of footsteps aligning with my inner state.",
#         "tags": ["mindfulness", "introspection"]
#     },
#     {
#         "content": "An old fear revisited me, but softer this time, almost gentle.",
#         "tags": ["resilience", "self_discovery"]
#     },
#     {
#         "content": "I felt a strange clarity staring at the evening sky.",
#         "tags": ["serenity", "clarity"]
#     },
#     {
#         "content": "Time felt folded today, as though present and past were overlapping.",
#         "tags": ["nostalgia", "existentialism"]
#     },
#     {
#         "content": "Work moved forward, but my heart longed to wander elsewhere.",
#         "tags": ["restlessness", "ambition"]
#     },
#     {
#         "content": "Dream fragments carried over into waking, shaping my morning mood.",
#         "tags": ["introspection", "curiosity"]
#     },
#     {
#         "content": "Something in me wants to pause, though life pulls forward.",
#         "tags": ["reflection", "resignation"]
#     },
#     {
#         "content": "A quiet sense of gratitude filled me without reason.",
#         "tags": ["gratitude", "positivity"]
#     },
#     {
#         "content": "The day passed quickly, yet inside felt suspended and still.",
#         "tags": ["mindfulness", "calmness"]
#     },
#     {
#         "content": "Recurring thoughts remind me that the story isn't finished yet.",
#         "tags": ["persistence", "self_reflection"]
#     },
#     {
#         "content": "In stillness, I found movement in the smallest details around me.",
#         "tags": ["mindfulness", "curiosity"]
#     },
#     {
#         "content": "The weight of routine pressed down, yet gave me strange comfort.",
#         "tags": ["comfort", "resignation"]
#     },
#     {
#         "content": "I felt both near and far from myself at once.",
#         "tags": ["introspection", "uncertainty"]
#     },
#     {
#         "content": "Colors of the evening reminded me of forgotten places within.",
#         "tags": ["nostalgia", "self_discovery"]
#     },
#     {
#         "content": "Today's effort felt necessary, but the meaning remains unclear.",
#         "tags": ["uncertainty", "perseverance"]
#     },
#     {
#         "content": "An unexpected calm arrived as the sun went down.",
#         "tags": ["serenity", "calmness"]
#     },
#     {
#         "content": "I sensed invisible threads pulling me toward reflection.",
#         "tags": ["introspection", "self_reflection"]
#     },
#     {
#         "content": "The laughter of others highlighted a quiet emptiness in me.",
#         "tags": ["loneliness", "self_doubt"]
#     },
#     {
#         "content": "Moments of ease today reminded me that not all must be effort.",
#         "tags": ["relaxation", "positivity"]
#     },
#     {
#         "content": "I watched the day slip away, uncertain if I had held it well.",
#         "tags": ["self_doubt", "reflection"]
#     },
#     {
#         "content": "A restless energy stirred beneath even my calmest moments.",
#         "tags": ["anxiety", "overwhelm"]
#     },
#     {
#         "content": "I felt echoes of past choices in small decisions today.",
#         "tags": ["reflection", "perspective"]
#     },
#     {
#         "content": "The body felt heavy, but the mind wandered light.",
#         "tags": ["exhaustion", "curiosity"]
#     },
#     {
#         "content": "Dreams today clung to me, shaping the tone of waking life.",
#         "tags": ["introspection", "self_discovery"]
#     },
#     {
#         "content": "Something about today felt like repetition, but also renewal.",
#         "tags": ["persistence", "optimism"]
#     },
#     {
#         "content": "I noticed how quickly joy and worry dance together in me.",
#         "tags": ["self_reflection", "ambivalence"]
#     },
#     {
#         "content": "An unanswered question lingers, but I'm learning to sit with it.",
#         "tags": ["patience", "uncertainty"]
#     },
#     {
#         "content": "Movement brought release, though my thoughts resisted being carried away.",
#         "tags": ["catharsis", "perseverance"]
#     },
#     {
#         "content": "A small act today carried greater weight than I expected.",
#         "tags": ["significance", "self_reflection"]
#     },
#     {
#         "content": "I saw myself reflected in another's struggle.",
#         "tags": ["empathy", "connection"]
#     },
#     {
#         "content": "A quiet resolve formed, though I'm unsure what it belongs to.",
#         "tags": ["determination", "uncertainty"]
#     },
#     {
#         "content": "I felt time bending, as if pointing me back toward something forgotten.",
#         "tags": ["nostalgia", "self_discovery"]
#     },
#     {
#         "content": "Even fatigue carried a strange beauty when I noticed it fully.",
#         "tags": ["mindfulness", "acceptance"]
#     },
#     {
#         "content": "An old memory resurfaced as if summoned by nothing at all.",
#         "tags": ["nostalgia", "surprise"]
#     },
#     {
#         "content": "The ordinary felt luminous for a moment, then slipped back into routine.",
#         "tags": ["mindfulness", "aesthetics"]
#     },
#     {
#         "content": "Words seemed insufficient today, yet silence said too much.",
#         "tags": ["frustration", "introspection"]
#     },
#     {
#         "content": "I stood still, sensing how much was moving within and without.",
#         "tags": ["mindfulness", "connection"]
#     },
#     {
#         "content": "The night sky pressed its vastness into my small thoughts.",
#         "tags": ["existentialism", "awe"]
#     },
#     {
#         "content": "I felt the paradox of longing for both change and stillness.",
#         "tags": ["ambivalence", "self_reflection"]
#     },
#     {
#         "content": "The day closed softly, leaving me with questions rather than answers.",
#         "tags": ["uncertainty", "introspection"]
#     },
# ]


class Command(BaseCommand):
    help = "Seed mock journal entries with coherent tags for testing (limit 3 entries per day, 2 relevant tags each)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Username of the user to assign journal entries to",
            required=True,
        )

        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days back to create entries for (default: 7)",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear this user's journal entries before seeding",
        )

    def handle(self, *args, **options):
        username = options["username"]
        days = options["days"]

        # Get the user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist.")

        if options["clear"]:
            JournalEntry.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING(f"Cleared all entries for '{username}'"))

        # Create a mapping of tag names to Tag objects
        tag_mapping = {}
        for tag in Tag.objects.all():
            tag_mapping[tag.name] = tag

        entries_created = 0

        for day_offset in range(days):
            # Calculate the target date
            target_date = timezone.now().date() - timedelta(days=day_offset)

            for i in range(3):  # 3 entries per day
                # Get a random entry with its predefined tags
                entry_data = random.choice(SAMPLE_ENTRIES_WITH_TAGS)
                content = entry_data["content"]
                tag_names = entry_data["tags"]

                # Create a random time for this entry on the target date
                random_hour = random.randint(6, 23)  # Random hour between 6 AM and 11 PM
                random_minute = random.randint(0, 59)
                random_second = random.randint(0, 59)

                # Combine the target date with random time
                target_datetime = datetime.combine(
                    target_date,
                    time(random_hour, random_minute, random_second)
                )

                # Make it timezone-aware
                created_at = timezone.make_aware(target_datetime)

                # Create entry first
                entry = JournalEntry.objects.create(
                    user=user,
                    label=f"entry{i + 1}",
                    content=content,
                )

                # Force update the created_at field directly in the database
                JournalEntry.objects.filter(id=entry.id).update(created_at=created_at)

                # Add the predefined tags (convert names to Tag objects)
                tag_objects = []
                for tag_name in tag_names:
                    if tag_name in tag_mapping:
                        tag_objects.append(tag_mapping[tag_name])
                    else:
                        self.stdout.write(self.style.WARNING(f"Tag '{tag_name}' not found in database"))

                if tag_objects:
                    entry.tags.set(tag_objects)

                entries_created += 1

                # Debug output to verify dates and tags
                entry.refresh_from_db()  # Reload from database to get updated created_at
                self.stdout.write(f"Created entry {entries_created}: {entry.created_at} - Tags: {', '.join(tag_names)}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {entries_created} entries for user '{username}' with coherent tags."
            )
        )