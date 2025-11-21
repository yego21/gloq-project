from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType
from django.db import connection

class Command(BaseCommand):
    help = 'Safely load fixture data with signal control and contenttype handling'

    def add_arguments(self, parser):
        parser.add_argument(
            'fixture',
            type=str,
            help='Fixture file to load'
        )
        parser.add_argument(
            '--fresh',
            action='store_true',
            help='Fresh load (clear existing data first)'
        )

    def handle(self, *args, **options):
        fixture = options['fixture']
        fresh = options.get('fresh', False)

        self.stdout.write(self.style.WARNING('🔧 Starting safe fixture load...'))

        # Step 1: Disable signals if you have them
        self.stdout.write('📵 Disabling signals...')
        try:
            from userprofile.signals import disable_signals  # Adjust import path
            disable_signals()
            signals_disabled = True
        except ImportError:
            self.stdout.write(self.style.WARNING('   ⚠️  No signal controls found, skipping'))
            signals_disabled = False

        try:
            if fresh:
                # Step 2: Clear ContentTypes (this causes the conflicts)
                self.stdout.write('🗑️  Clearing ContentTypes...')
                ContentType.objects.all().delete()

            # Step 3: Load the fixture
            self.stdout.write(f'📦 Loading fixture: {fixture}')
            call_command('loaddata', fixture, verbosity=2)

            self.stdout.write(self.style.SUCCESS('✅ Fixture loaded successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error loading fixture: {e}'))
            raise

        finally:
            # Step 4: Re-enable signals
            if signals_disabled:
                self.stdout.write('📶 Re-enabling signals...')
                try:
                    from userprofile.signals import enable_signals  # Adjust import path
                    enable_signals()
                except ImportError:
                    pass

        self.stdout.write(self.style.SUCCESS('🎉 All done!'))