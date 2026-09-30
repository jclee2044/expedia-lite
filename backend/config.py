"""Load backend configuration from the project-root environment file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def get_geoapify_api_key() -> str | None:
    """Load and return the configured Geoapify key when it is usable."""
    load_dotenv(dotenv_path=ENV_FILE)
    value = os.getenv("GEOAPIFY_API_KEY")
    if value is None or not value.strip():
        return None
    return value.strip()


def geoapify_key_is_configured() -> bool:
    """Return whether the project environment contains a usable API key."""
    return get_geoapify_api_key() is not None
