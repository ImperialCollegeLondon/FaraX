"""Django settings for running FaraX in production.

Use these settings by setting `DJANGO_SETTINGS_MODULE=farax.settings.production`. They
extend the base settings and read the deployment's configuration from environment
variables. Django fails to start if any of these is missing:

- `DJANGO_SECRET_KEY`: the secret key.
- `DJANGO_ALLOWED_HOSTS`: comma-separated host names the site is served from.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` and
  `POSTGRES_PORT`: the PostgreSQL database connection.
"""

import os

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.environ["POSTGRES_PORT"],
    }
}

# Static files are collected into STATIC_ROOT with `collectstatic` and served by
# WhiteNoise, so no separate web server configuration is needed.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],  # noqa: F405
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# HTTPS. The site is expected to sit behind a reverse proxy that terminates TLS and sets
# the X-Forwarded-Proto header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 15552000  # 180 days
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Joining the browser HSTS preload list is a decision for the hosting target, which is
# not yet chosen, so Django's warning about it is silenced.
SILENCED_SYSTEM_CHECKS = ["security.W021"]

# Email is sent over SMTP, using Django's defaults (localhost, port 25) until email is
# needed.
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    },
}
