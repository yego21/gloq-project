import json
from django.core.management.base import BaseCommand
from django.core.management import call_command
from userprofile.signals import disable_signals, enable_signals
from user_management.signals import disable_signals as ds, enable_signals as es
from pathlib import Path

class Command(BaseCommand):
    help = 'Load data while controlling signal management and ensuring UTF-8 compatibility'

    def handle(self, *args, **kwargs):
        file_path = Path("db_dump_dev.json")

        # Step 1 — Validate and fix encoding issues
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()
            decoded_data = raw_data.decode("utf-8")  # Will fail if not pure UTF-8

        except UnicodeDecodeError as e:
            self.stderr.write(self.style.WARNING(f"Encoding issue detected: {e}"))
            # Attempt to fix (replace invalid chars with closest match)
            decoded_data = raw_data.decode("utf-8", errors="replace")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(decoded_data)
            self.stdout.write(self.style.WARNING("Invalid characters replaced."))

        # Step 2 — Ensure JSON is valid
        try:
            json.loads(decoded_data)
        except json.JSONDecodeError as e:
            self.stderr.write(self.style.ERROR(f"JSON is invalid: {e}"))
            return

        # Step 3 — Temporarily disable signals
        disable_signals()
        ds()

        # Step 4 — Load the data
        call_command("loaddata", str(file_path))

        # Step 5 — Re-enable signals
        enable_signals()
        es()

        self.stdout.write(self.style.SUCCESS("Successfully loaded data and managed signals."))
