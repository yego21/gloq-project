#!/usr/bin/env python
import os
import sys
import environ
from pathlib import Path


def main():
    BASE_DIR = Path(__file__).resolve().parent.parent
    env = environ.Env()
    environ.Env.read_env(BASE_DIR / '.env')

    django_env = env('DJANGO_ENV', default='dev')  # local default
    # django_env = os.getenv('DJANGO_ENV')
    print(f'djando env manage:{django_env}')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'gloq.settings.{django_env}')

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
