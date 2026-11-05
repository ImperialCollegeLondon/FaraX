"""Django settings for running FaraX in production.

Use these settings by setting `DJANGO_SETTINGS_MODULE=farax.settings.production`. They
extend the base settings and read the deployment's configuration from environment
variables. Django fails to start if any of these is missing:

- `DJANGO_SECRET_KEY`: the secret key.
- `DJANGO_ALLOWED_HOSTS`: comma-separated host names the site is served from.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` and
  `POSTGRES_PORT`: the PostgreSQL database connection.

Email is sent over SMTP, configured by these optional variables:

- `DJANGO_EMAIL_HOST`: the SMTP server (default: `localhost`).
- `DJANGO_EMAIL_PORT`: the SMTP port (default: 587 with TLS, otherwise 25).
- `DJANGO_EMAIL_HOST_USER` and `DJANGO_EMAIL_HOST_PASSWORD`: credentials to log in to
  the SMTP server with (default: don't log in).
- `DJANGO_EMAIL_USE_TLS`: `true` to use STARTTLS (default: `false`).

Django fails to start if `DJANGO_EMAIL_PORT` isn't a whole number or
`DJANGO_EMAIL_USE_TLS` isn't `true` or `false` (`1`/`0`, `yes`/`no` and `on`/`off` also
work).
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

# Email is sent over SMTP. Django 6.1 configures email through MAILERS, which replaces
# the deprecated EMAIL_* settings (Django refuses to start if both are set). The SMTP
# backend reads its configuration from OPTIONS and requires "host"; it picks the port
# from use_tls when "port" isn't given. Empty variables count as unset.
_email_options: dict[str, object] = {
    "host": os.environ.get("DJANGO_EMAIL_HOST") or "localhost",
}
if _email_port := os.environ.get("DJANGO_EMAIL_PORT"):
    if not _email_port.isdigit():
        raise ValueError(
            f"DJANGO_EMAIL_PORT must be a whole number, not {_email_port!r}"
        )
    _email_options["port"] = int(_email_port)
if _email_user := os.environ.get("DJANGO_EMAIL_HOST_USER"):
    _email_options["username"] = _email_user
if _email_password := os.environ.get("DJANGO_EMAIL_HOST_PASSWORD"):
    _email_options["password"] = _email_password
_email_use_tls = os.environ.get("DJANGO_EMAIL_USE_TLS", "").strip().lower()
if _email_use_tls in ("true", "1", "yes", "on"):
    _email_options["use_tls"] = True
elif _email_use_tls not in ("", "false", "0", "no", "off"):
    raise ValueError(
        f"DJANGO_EMAIL_USE_TLS must be true or false, not {_email_use_tls!r}"
    )

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": _email_options,
    },
}
