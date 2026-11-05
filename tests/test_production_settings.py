"""Tests for the production settings.

Each test runs Django in a separate process so that the production settings never
replace the settings used by the rest of the test session.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_ENV = {
    "DJANGO_SECRET_KEY": "a-long-random-production-secret-key-with-many-characters",
    "DJANGO_ALLOWED_HOSTS": "farax.example.com,testserver",
    "POSTGRES_DB": "farax",
    "POSTGRES_USER": "farax",
    "POSTGRES_PASSWORD": "password",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
}


def run_with_production_settings(*args, env=None):
    """Run a Python command with the production settings and the given environment."""
    environ = {
        key: value
        for key, value in os.environ.items()
        if key not in REQUIRED_ENV and key != "DJANGO_SETTINGS_MODULE"
    }
    environ.update(env if env is not None else REQUIRED_ENV)
    environ["DJANGO_SETTINGS_MODULE"] = "farax.settings.production"
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        env=environ,
        capture_output=True,
        text=True,
    )


def test_deployment_checks_pass_with_required_variables():
    """Django's deployment checks pass, without warnings, under production settings."""
    result = run_with_production_settings(
        "manage.py", "check", "--deploy", "--fail-level", "WARNING"
    )
    assert result.returncode == 0, result.stderr
