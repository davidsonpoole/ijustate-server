"""
TEMPLATE for local_settings.py, which is untracked.

Copy this file to local_settings.py and fill in your own values. Django will
refuse to start without it, because SECRET_KEY and ALLOWED_HOSTS are
deployment-specific and must never be committed.

Generate a key with:
    ./venv/bin/python -c "from django.core.management.utils import \
get_random_secret_key; print(get_random_secret_key())"
"""

SECRET_KEY = "replace-me-with-a-generated-key"

# Never True on a host reachable from the internet: Django's debug pages
# disclose settings, file paths and your configured hostnames to anyone who
# can trigger a 500.
DEBUG = False

# The hostnames/IPs this server answers on.
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

# Only needed if a browser-based client is added; the iOS app does not use CORS.
# CORS_ALLOWED_ORIGINS = []
