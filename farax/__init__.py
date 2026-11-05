"""The FaraX Django project: settings, root URLs and ASGI and WSGI entry points."""

from contextlib import suppress
from importlib.metadata import PackageNotFoundError, version

with suppress(PackageNotFoundError):
    __version__ = version(__name__)
