"""Tests for the production settings.

Each test runs Django in a separate process so that the production settings never
replace the settings used by the rest of the test session.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

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


@pytest.mark.parametrize("missing", sorted(REQUIRED_ENV))
def test_settings_fail_to_load_when_a_required_variable_is_missing(missing):
    """Django refuses to start when any required variable is not set."""
    env = {key: value for key, value in REQUIRED_ENV.items() if key != missing}
    result = run_with_production_settings("manage.py", "check", env=env)
    assert result.returncode != 0
    assert f"KeyError: '{missing}'" in result.stderr


@pytest.mark.parametrize(
    "variable, value",
    [("DJANGO_EMAIL_PORT", "smtp"), ("DJANGO_EMAIL_USE_TLS", "maybe")],
)
def test_settings_fail_to_load_with_an_invalid_email_variable(variable, value):
    """Django refuses to start when an email variable can't be understood."""
    result = run_with_production_settings(
        "manage.py", "check", env={**REQUIRED_ENV, variable: value}
    )
    assert result.returncode != 0
    assert f"ValueError: {variable} must be" in result.stderr
