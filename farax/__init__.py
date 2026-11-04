"""The main module for FaraX."""

from contextlib import suppress
from importlib.metadata import PackageNotFoundError, version

with suppress(PackageNotFoundError):
    __version__ = version(__name__)
