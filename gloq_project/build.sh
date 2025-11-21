#!/bin/sh
set -e  # stop if error

if [ "$DJANGO_ENV" = "prod" ]; then
    echo "Starting Gunicorn..."
    gunicorn --bind 0.0.0.0:8000 gloq.wsgi:application
else
    echo "Starting Django development server..."
    python manage.py runserver 0.0.0.0:8000
fi
