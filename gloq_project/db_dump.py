# db_dump.py
import os
import sys
import json
import django
import environ
from pathlib import Path

# Setup environment exactly like manage.py does
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

django_env = env('DJANGO_ENV', default='dev')
print(f'djando env:{django_env}')

# Set settings module based on environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'gloq.settings.{django_env}')
django.setup()

from django.core import serializers
from django.apps import apps
from django.conf import settings

print("🌙 Starting UTF-8 database dump...")
print(f"📂 Settings module: {settings.SETTINGS_MODULE}")

# Handle different database configurations
try:
    if hasattr(settings, 'DATABASES') and settings.DATABASES:
        db_config = settings.DATABASES.get('default', list(settings.DATABASES.values())[0])
        db_name = db_config.get('NAME', 'Unknown')
        print(f"📊 Database: {db_name}")
        print(f"   Engine: {db_config.get('ENGINE', 'Unknown')}")
    else:
        print("📊 Database: Configuration not found")
except Exception as e:
    print(f"📊 Database: Could not read config ({e})")
print()

# List all installed apps
print("📱 Installed apps:")
for app in settings.INSTALLED_APPS:
    print(f"  - {app}")
print()

# Get all models
all_models = list(apps.get_models())
print(f"🗂️  Found {len(all_models)} models:")
for model in all_models:
    print(f"  - {model._meta.app_label}.{model._meta.model_name}")
print()

# Count objects per model
print("🔍 Checking object counts:")
all_objects = []
model_stats = {}

for model in all_models:
    try:
        count = model.objects.count()
        model_name = f"{model._meta.app_label}.{model._meta.model_name}"
        model_stats[model_name] = count

        if count > 0:
            print(f"  ✓ {model_name}: {count} objects")
            objects = list(model.objects.all())
            all_objects.extend(objects)
        else:
            print(f"  ○ {model_name}: 0 objects (skipping)")
    except Exception as e:
        print(f"  ✗ Error with {model._meta.app_label}.{model._meta.model_name}: {e}")

print()
print(f"📦 Total objects to serialize: {len(all_objects)}")

if len(all_objects) == 0:
    print()
    print("⚠️  WARNING: No objects found in database!")
    print("   Possible reasons:")
    print("   1. Database is empty")
    print("   2. Wrong database file being read")
    print("   3. Wrong DJANGO_ENV setting")
    print()

    # Try to check if database file exists
    try:
        db_config = settings.DATABASES.get('default', list(settings.DATABASES.values())[0])
        db_path = db_config.get('NAME')
        if db_path and os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            print(f"   ✓ Database file exists: {db_path} ({db_size:,} bytes)")
        else:
            print(f"   ✗ Database path: {db_path}")
    except Exception as e:
        print(f"   ? Could not check database file: {e}")

    print()
    response = input("Continue with empty dump? (y/n): ")
    if response.lower() != 'y':
        sys.exit(1)

# Serialize
print("📝 Serializing data...")
data_json = serializers.serialize('json', all_objects, indent=4)

# Parse and re-dump with ensure_ascii=False
data = json.loads(data_json)

# Write with UTF-8 encoding
output_file = f'db_dump_{django_env}.json'
print(f"💾 Writing to {output_file}...")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print()
print(f"✅ Successfully dumped {len(data)} objects to {output_file}!")
print()

if model_stats:
    print("📊 Summary by model:")
    for model_name, count in sorted(model_stats.items()):
        if count > 0:
            print(f"   {model_name}: {count}")
    print()

print("🌞 Emojis preserved: 🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘")