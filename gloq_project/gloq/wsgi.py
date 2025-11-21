import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# django_env = env('DJANGO_ENV', default='prod')  # default prod for safety
django_env = os.getenv('DJANGO_ENV')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'gloq.settings.{django_env}')
print(f'djando env:{django_env}')

application = get_wsgi_application()
