# journal/management/commands/backfill_planetary_snapshots.py
from django.core.management.base import BaseCommand
from django.db import transaction
from journal.models import JournalEntry, DailyPlanetarySnapshot
from django.utils import timezone as django_timezone
import pytz
import warnings


class Command(BaseCommand):
    help = 'Backfill planetary_snapshot for existing journal entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of entries to process in each batch (default: 100)',
        )
        parser.add_argument(
            '--start-from',
            type=int,
            default=None,
            help='Start from a specific entry ID (useful for resuming)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Only process this many entries (useful for testing)',
        )
        parser.add_argument(
            '--user',
            type=str,
            default=None,
            help='Only process entries for a specific username',
        )
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='Force regenerate snapshots even if they already exist',
        )

    def handle(self, *args, **options):
        # Suppress cache key warnings
        warnings.filterwarnings('ignore', category=Warning, message='.*Cache key contains characters.*')

        dry_run = options['dry_run']
        batch_size = options['batch_size']
        start_from = options['start_from']
        limit = options['limit']
        username = options['user']
        regenerate = options['regenerate']

        # Build the query
        queryset = JournalEntry.objects.select_related(
            'user', 'user__userprofile'
        ).order_by('id')  # Changed to 'id' for more predictable ordering

        # Filter based on regenerate flag
        if not regenerate:
            queryset = queryset.filter(planetary_snapshot__isnull=True)

        # Apply filters
        if start_from:
            queryset = queryset.filter(id__gte=start_from)
            self.stdout.write(f"📍 Starting from entry ID {start_from}")

        if username:
            queryset = queryset.filter(user__username=username)
            self.stdout.write(f"👤 Filtering for user: {username}")

        if limit:
            queryset = queryset[:limit]
            self.stdout.write(f"🔢 Limiting to {limit} entries")

        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✓ No entries to process!"))
            return

        # Get ID range for reference
        first_entry = queryset.first()
        last_entry = queryset.last()

        self.stdout.write(f"\n📊 Found {total} entries to process")
        self.stdout.write(f"📍 Entry ID range: {first_entry.id} → {last_entry.id}")
        self.stdout.write(f"📅 Date range: {first_entry.created_at.date()} → {last_entry.created_at.date()}")

        if regenerate:
            self.stdout.write(
                self.style.WARNING("🔄 REGENERATE MODE - Will update ALL entries including existing snapshots"))

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No changes will be made\n"))

        updated = 0
        failed = 0
        failed_ids = []
        snapshots_created = 0
        snapshots_reused = 0
        last_processed_id = None

        # Convert queryset to list to avoid issues with slicing
        entries_list = list(queryset)

        # Process in batches
        for i in range(0, len(entries_list), batch_size):
            batch = entries_list[i:i + batch_size]

            if not batch:  # Skip if batch is empty
                continue

            batch_start = batch[0].id
            batch_end = batch[-1].id

            self.stdout.write(
                f"\n📦 Batch {i // batch_size + 1}/{(len(entries_list) + batch_size - 1) // batch_size} "
                f"(Entries {i + 1}-{min(i + batch_size, len(entries_list))} of {total}) "
                f"[IDs: {batch_start}-{batch_end}]"
            )

            for entry in batch:
                last_processed_id = entry.id

                try:
                    # Get local date - ensure it's a datetime object for consistency
                    local_datetime = self._get_local_datetime(entry)
                    local_date = local_datetime.date()

                    if dry_run:
                        if i < 3 or (updated + 1) % 50 == 0:
                            status = "UPDATE" if entry.planetary_snapshot else "NEW"
                            self.stdout.write(
                                f"  [{status}] ID {entry.id}: {entry.user.username}, "
                                f"{entry.created_at.strftime('%Y-%m-%d %H:%M')} → {local_date}"
                            )
                        updated += 1
                    else:
                        # Check if snapshot already exists for this date
                        snapshot_exists = DailyPlanetarySnapshot.objects.filter(
                            date=local_date
                        ).exists()

                        # Pass datetime object to maintain compatibility
                        snapshot = DailyPlanetarySnapshot.get_or_create_for_date(local_datetime)

                        if not snapshot_exists:
                            snapshots_created += 1
                        else:
                            snapshots_reused += 1

                        entry.planetary_snapshot = snapshot
                        entry.save(update_fields=['planetary_snapshot'])

                        updated += 1

                        if updated % 25 == 0:
                            self.stdout.write(f"  ✓ Processed {updated}/{total} entries... (last ID: {entry.id})")

                except Exception as e:
                    failed += 1
                    failed_ids.append(entry.id)
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ ID {entry.id} ({entry.user.username}): {str(e)}"
                        )
                    )

            # Show progress after each batch
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Batch complete! Last processed ID: {last_processed_id}"
                    )
                )

        # Final summary
        self.stdout.write("\n" + "=" * 70)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ DRY RUN COMPLETE:\n"
                    f"  • {updated} entries would be updated\n"
                    f"  • {failed} entries would fail\n"
                    f"  • ID range processed: {first_entry.id} → {last_entry.id}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ BACKFILL COMPLETE:\n"
                    f"  • {updated} entries updated successfully\n"
                    f"  • {snapshots_created} new snapshots created\n"
                    f"  • {snapshots_reused} existing snapshots reused\n"
                    f"  • {failed} entries failed\n"
                    f"  • Last processed ID: {last_processed_id}"
                )
            )

            if failed_ids:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n❌ Failed entry IDs: {', '.join(map(str, failed_ids))}"
                    )
                )
                self.stdout.write(
                    f"\n💡 To retry failed entries, run:\n"
                    f"   python manage.py backfill_planetary_snapshots --start-from {min(failed_ids)}"
                )

        self.stdout.write("=" * 70 + "\n")

        # Show next steps if there might be more entries
        if not dry_run and last_processed_id and not limit and not regenerate:
            remaining = JournalEntry.objects.filter(
                planetary_snapshot__isnull=True,
                id__gt=last_processed_id
            ).count()

            if remaining > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  There are still {remaining} entries after ID {last_processed_id}\n"
                        f"   To continue, run:\n"
                        f"   python manage.py backfill_planetary_snapshots --start-from {last_processed_id + 1}"
                    )
                )

    def _get_local_datetime(self, entry):
        """Get entry's creation datetime in user's local timezone (returns datetime, not date)"""
        try:
            user_tz = pytz.timezone(entry.user.userprofile.timezone or 'UTC')
            local_dt = entry.created_at.astimezone(user_tz)
            return local_dt  # Return datetime object
        except Exception:
            # Fallback to UTC if profile doesn't exist or timezone is invalid
            return entry.created_at