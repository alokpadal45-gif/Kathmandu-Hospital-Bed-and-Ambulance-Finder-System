"""
Development settings.
Run with: DJANGO_SETTINGS_MODULE=config.settings.development
(this is already the default set in manage.py / asgi.py / wsgi.py)
"""

from .base import *  # noqa: F401,F403
from decouple import config, Csv

DEBUG = True

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# ---------------------------------------------------------------------------
# Database — SQLite is enough for local development (matches the doc's
# feasibility study: MySQL is listed as optional, for later production use).
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ---------------------------------------------------------------------------
# Channels layer — in-memory is fine for local dev (single process).
# Production swaps this for Redis so multiple server workers can share
# WebSocket group messages (see production.py).
# ---------------------------------------------------------------------------
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# Emails just print to the console during development (password resets etc.)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CORS_ALLOW_ALL_ORIGINS = True
