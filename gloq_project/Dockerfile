FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
    && chmod +x tailwindcss-linux-x64 \
    && mv tailwindcss-linux-x64 /usr/local/bin/tailwindcss

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN tailwindcss -i ./static/src/input.css -o ./static/css/output.css --minify
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Simple CMD instead of entrypoint script
CMD python manage.py migrate --noinput && \
    gunicorn gloq.wsgi:application --bind 0.0.0.0:8000 --workers 3