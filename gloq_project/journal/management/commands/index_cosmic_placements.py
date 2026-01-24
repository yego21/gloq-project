# journal/management/commands/index_cosmic_placements.py
from django.core.management.base import BaseCommand

from deep_dive.utils.mystical_utils import index_coincidences
from journal.models import JournalEntry



class Command(BaseCommand):
    help = 'Builds the Planet Journal index for entries that already have snapshots'

    def handle(self, *args, **options):
        # Only grab entries that have snapshots but NO coincidences yet
        entries = JournalEntry.objects.filter(
            planetary_snapshot__isnull=False
        ).exclude(coincidences__isnull=False).distinct()

        self.stdout.write(f"Indexing {entries.count()} entries...")

        for entry in entries:
            index_coincidences(entry)

        self.stdout.write(self.style.SUCCESS("✓ Planet Journal Index is now up to date!"))