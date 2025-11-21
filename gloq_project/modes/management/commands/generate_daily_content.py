from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from modes.models import DailyContent, Mode
from groq import Groq
import os
import json


class Command(BaseCommand):
    help = 'Pre-generate daily content for journal modes (maintains 3-day buffer: yesterday, today, tomorrow)'

    def add_arguments(self, parser):
        parser.add_argument('--mode', type=str, help='Specific mode slug to generate')
        parser.add_argument('--date', type=str, help='Specific date (YYYY-MM-DD) - for manual generation')
        parser.add_argument('--force', action='store_true', help='Regenerate existing content')

    def handle(self, *args, **options):
        if not os.getenv("GROQ_API_KEY"):
            self.stdout.write(self.style.ERROR("GROQ_API_KEY not found in environment"))
            return

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Determine which modes to generate
        if options['mode']:
            modes = Mode.objects.filter(slug=options['mode'], is_active=True)
            if not modes.exists():
                self.stdout.write(self.style.ERROR(f"Mode '{options['mode']}' not found or inactive"))
                return
        else:
            modes = Mode.objects.filter(is_active=True)

        # Determine date range - always maintain 3-day buffer unless specific date requested
        if options['date']:
            try:
                specific_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                dates = [specific_date]
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid date format. Use YYYY-MM-DD"))
                return
        else:
            # Maintain 3-day buffer: yesterday, today, tomorrow
            today_utc = timezone.now().date()
            dates = [
                today_utc - timedelta(days=1),  # Yesterday
                today_utc,  # Today
                today_utc + timedelta(days=1)  # Tomorrow
            ]

        total_generated = 0
        total_skipped = 0

        for mode in modes:
            for date in dates:
                result = self.generate_for_mode_and_date(client, mode, date, options['force'])
                if result == 'generated':
                    total_generated += 1
                elif result == 'skipped':
                    total_skipped += 1

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n=== SUMMARY ===\n"
            f"Generated: {total_generated} entries\n"
            f"Skipped: {total_skipped} entries (already exist)\n"
            f"Modes processed: {modes.count()}\n"
            f"Date range: {dates[0]} to {dates[-1]}"
        ))

    def generate_for_mode_and_date(self, client, mode, date, force=False):
        # Check if content already exists
        existing = DailyContent.objects.filter(
            mode=mode,
            date=date,
            content_type='global'
        ).first()

        if existing and not force:
            self.stdout.write(f"  ⏭️  {mode.slug} on {date} (already exists)")
            return 'skipped'

        try:
            content_data = self.call_groq_for_mode(client, mode, date)

            if existing and force:
                # Update existing
                existing.content_data = content_data
                existing.save()
                self.stdout.write(self.style.WARNING(f"  🔄 Updated {mode.slug} on {date}"))
            else:
                # Create new
                DailyContent.objects.create(
                    mode=mode,
                    date=date,
                    content_type='global',
                    content_data=content_data
                )
                self.stdout.write(self.style.SUCCESS(f"  ✅ Generated {mode.slug} on {date}"))

            return 'generated'

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Failed {mode.slug} on {date}: {e}"))
            return 'error'

    # def call_groq_for_mode(self, client, mode, date):
    #     if mode.slug == 'mystical':
    #         prompt = (
    #             "Return JSON with exactly these keys: "
    #             "`astronomical` Astronomical notable (if no event, give timeless sky reflection), "
    #             "`action` Suggested mystical action, "
    #             "`fact` Mystical fact about magick, alchemy, or esoteric traditions. "
    #             "Keep each concise and inspiring."
    #         )
    #     elif mode.slug == 'philosophical':
    #         prompt = (
    #             f"Generate JSON with keys 'question' and 'fact'. "
    #             f"1) A concise philosophical question for self-reflection. "
    #             f"2) A short philosophical fact or idea from history. "
    #             f"Make both 1-2 sentences. Date context: {date}."
    #         )
    #     else:
    #         self.stdout.write(self.style.WARNING(f"No prompt defined for mode: {mode.slug}"))
    #         return {}
    #
    #     response = client.chat.completions.create(
    #         model="llama-3.1-8b-instant",
    #         messages=[{"role": "user", "content": prompt}],
    #         max_tokens=300,
    #         temperature=0.7
    #     )
    #
    #     content = response.choices[0].message.content.strip()
    #
    #     # Debug what Groq actually returned
    #     if not content:
    #         self.stdout.write(self.style.WARNING(f"Groq returned empty content for {mode.slug}"))
    #
    #     self.stdout.write(f"[DEBUG] Groq raw response for {mode.slug}: {repr(content[:200])}")
    #
    #     try:
    #         # Clean up markdown code blocks if present
    #         if content.startswith('```json'):
    #             content = content.split('```json')[1].split('```')[0].strip()
    #         elif content.startswith('```'):
    #             content = content.split('```')[1].split('```')[0].strip()
    #
    #         if not content:
    #             raise json.JSONDecodeError("Empty content after cleanup", "", 0)
    #
    #         return json.loads(content)
    #
    #     except json.JSONDecodeError as e:
    #         self.stdout.write(self.style.WARNING(f"JSON parsing failed for {mode.slug}: {e}"))
    #
    #         # Return fallback content if JSON parsing fails
    #         if mode.slug == 'mystical':
    #             return {
    #                 "astronomical": "The Moon continues its eternal dance across the sky.",
    #                 "action": "Take a moment to appreciate the mystery of existence.",
    #                 "fact": "Ancient alchemists believed in the principle 'as above, so below'."
    #             }
    #         elif mode.slug == 'philosophical':
    #             return {
    #                 "question": "What does it mean to live an examined life?",
    #                 "fact": "Socrates famously declared that 'the unexamined life is not worth living'."
    #             }
    #         return {}

    def call_groq_for_mode(self, client, mode, date):
        if mode.slug == 'mystical':
            prompt = (
                "You are an API returning only valid JSON with no explanation, no prose, "
                "no markdown formatting. Output must be a single JSON object with exactly "
                "these keys: 'astronomical', 'action', 'fact'.\n"
                "- 'astronomical': Astronomical notable (if no event, give timeless sky reflection)\n"
                "- 'action': Suggested mystical action\n"
                "- 'fact': Mystical fact about magick, alchemy, or esoteric traditions.\n"
                "Keep each concise and inspiring."
            )
        elif mode.slug == 'philosophical':
            prompt = (
                "You are an API returning only valid JSON with no explanation, no prose, "
                "no markdown formatting. Output must be a single JSON object with exactly "
                "these keys: 'question', 'fact'.\n"
                "- 'question': A concise philosophical question for self-reflection (1-2 sentences)\n"
                "- 'action': A short actionable philosophical tip\n"
                "- 'fact': A short philosophical fact or idea from history (1-2 sentences)\n"
                f"Date context: {date}."
            )

        elif mode.slug == 'medical':
            prompt = (
                "You are an API returning only valid JSON with no explanation, no prose, "
                "no markdown formatting. Output must be a single JSON object with exactly "
                "these keys: 'question', 'action', 'fact'.\n"
                "- 'question': A health-related self-reflection question (1-2 sentences)\n"
                "- 'action': A short actionable wellness tip\n"
                "- 'fact': A concise historical or medical fact.\n"
                f"Date context: {date}."
            )

        elif mode.slug == 'creative':
            prompt = (
                "You are an API returning only valid JSON with no explanation, no prose, "
                "no markdown formatting. Output must be a single JSON object with exactly "
                "these keys: 'question', 'action', 'fact'.\n"
                "- 'question': A brief creative challenge question (1-2 sentences)\n"
                "- 'action': A short artistic or creative exercise\n"
                "- 'fact': A concise fact about art, literature, or creativity in history.\n"
                f"Date context: {date}."
            )

        elif mode.slug == 'productive':
            prompt = (
                "You are an API returning only valid JSON with no explanation, no prose, "
                "no markdown formatting. Output must be a single JSON object with exactly "
                "these keys: 'question', 'action', 'fact'.\n"
                "- 'question': A short productivity or efficiency question (1-2 sentences)\n"
                "- 'action': A quick, actionable productivity tip\n"
                "- 'fact': A concise fact about historical productivity methods or tools.\n"
                f"Date context: {date}."
            )

        elif mode.slug == 'exploratory':
            prompt = (
                "You are an API returning only valid JSON with no explanation, no prose, "
                "no markdown formatting. Output must be a single JSON object with exactly "
                "these keys: 'question', 'action', 'fact'.\n"
                "- 'question': A curiosity-driven or discovery-based self-question (1-2 sentences)\n"
                "- 'action': A short suggestion to explore or learn something new\n"
                "- 'fact': A concise historical or scientific exploration fact.\n"
                f"Date context: {date}."
            )

        elif mode.slug == 'visionary':
            prompt = (
                "You are an API returning only valid JSON with no explanation, no prose, "
                "no markdown formatting. Output must be a single JSON object with exactly "
                "these keys: 'question', 'action', 'fact'.\n"
                "- 'question': A future-oriented or innovative self-reflection question (1-2 sentences)\n"
                "- 'action': A brief visionary or forward-thinking task\n"
                "- 'fact': A concise historical fact about visionaries or groundbreaking ideas.\n"
                f"Date context: {date}."
            )

        elif mode.slug == 'spiritual':
            prompt = (
                "You are an API returning only valid JSON with no explanation, no prose, "
                "no markdown formatting. Output must be a single JSON object with exactly "
                "these keys: 'question', 'action', 'fact'.\n"
                "- 'question': A short spiritual self-reflection question (1-2 sentences)\n"
                "- 'action': A brief spiritual or mindful action suggestion\n"
                "- 'fact': A concise historical or cultural spiritual fact.\n"
                f"Date context: {date}."
            )
        else:
            self.stdout.write(self.style.WARNING(f"No prompt defined for mode: {mode.slug}"))
            return {}

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        self.stdout.write(f"[DEBUG] Groq raw response for {mode.slug}: {repr(content[:200])}")

        try:
            # Find JSON inside any extra text
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                content = content[start:end + 1].strip()

            # Remove markdown fences if any slipped through
            if content.startswith("```"):
                content = content.strip("`").strip()

            if not content:
                raise json.JSONDecodeError("Empty content after cleanup", "", 0)

            return json.loads(content)

        except json.JSONDecodeError as e:
            self.stdout.write(self.style.WARNING(f"JSON parsing failed for {mode.slug}: {e}"))

            # Fallback content
            if mode.slug == 'mystical':
                return {
                    "astronomical": "The Moon continues its eternal dance across the sky.",
                    "action": "Take a moment to appreciate the mystery of existence.",
                    "fact": "Ancient alchemists believed in the principle 'as above, so below'."
                }
            elif mode.slug == 'philosophical':
                return {
                    "question": "What does it mean to live an examined life?",
                    "fact": "Socrates famously declared that 'the unexamined life is not worth living'."
                }
            return {}