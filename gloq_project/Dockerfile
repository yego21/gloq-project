# --- Base image ---
FROM python:3.11-slim

# --- Environment variables ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Create working directory ---
WORKDIR /app

# --- Install system dependencies (Postgres support, etc.) ---
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Install Python dependencies ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy all project files ---
COPY . .

# --- Expose port for Django/Gunicorn ---
EXPOSE 8000

# --- Start Django using Gunicorn ---
CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]
