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

# The base settings configure PostgreSQL from the POSTGRES_* variables but give all
# except POSTGRES_DB defaults. Production has no defaults, so require each one here.
for name in (
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
):
    if name not in os.environ:
        raise KeyError(name)

# Static files are collected into STATIC_ROOT with `collectstatic` and served by
# WhiteNoise, so no separate web server configuration is needed.
# WhiteNoise must come directly after SecurityMiddleware.
MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# HTTPS. These settings assume the site sits behind a reverse proxy that terminates TLS
# and sets the X-Forwarded-Proto header. The hosting target is not yet decided (#1), so
# revisit them once it is.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS is hard to undo once browsers have cached it, so start with a short duration and
# raise it (e.g. to 180 days) once the hosting target is confirmed.
SECURE_HSTS_SECONDS = 3600  # 1 hour

# Whether HSTS should cover subdomains (W005) or the site should join the browser HSTS
# preload list (W021) depends on the hosting target, which is not yet chosen, so
# Django's warnings about them are silenced.
SILENCED_SYSTEM_CHECKS = ["security.W005", "security.W021"]

# Email is sent over SMTP, using Django's defaults (localhost, port 25) until email is
# needed.
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    },
}
