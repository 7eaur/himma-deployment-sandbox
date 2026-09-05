"""Small runtime safety helpers used by the recovery branch."""

from __future__ import annotations

import os

_PROTECTED_RUNTIME_ENVS = {"trial", "production"}


def runtime_environment() -> str:
    return os.getenv("ENV", "development").strip().lower() or "development"


def validate_runtime_safety() -> None:
    """Fail closed for settings that are explicitly unsafe in a real trial.

    Audio recording has no development bypass. Submitted recordings remain
    pending for supervisor review until the approved automatic speech model is
    integrated. Dependency availability belongs to `/ready`.
    """

    environment = runtime_environment()
    if environment not in _PROTECTED_RUNTIME_ENVS:
        return

    secret = os.getenv("API_SECRET_KEY", "")
    if len(secret) < 32:
        raise RuntimeError(
            "API_SECRET_KEY must contain at least 32 characters in trial/production"
        )
