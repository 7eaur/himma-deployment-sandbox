"""Small runtime feature flags used by the recovery/demo branch."""

from __future__ import annotations

import os

_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}
_PROTECTED_RUNTIME_ENVS = {"trial", "production"}


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = raw.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    return default


def temporary_audio_skip_enabled() -> bool:
    """Allow neutral skipping of recording tasks while the real audio path is unfinished.

    TEMPORARY — switch HIMMA_TEMP_AUDIO_SKIP=false when the production audio
    pipeline is activated. Development keeps the historical default so the
    recovery branch remains exercisable without silently making trial safe.
    Trial/production startup is guarded separately by validate_runtime_safety().
    """

    return env_flag("HIMMA_TEMP_AUDIO_SKIP", default=True)


def runtime_environment() -> str:
    return os.getenv("ENV", "development").strip().lower() or "development"


def validate_runtime_safety() -> None:
    """Fail closed for settings that are explicitly unsafe in a real trial.

    M08 remains external-gated, so a trial/release process must never start with
    the temporary neutral audio bypass enabled.  This validation is deliberately
    small and deterministic; dependency availability belongs to `/ready`.
    """

    environment = runtime_environment()
    if environment not in _PROTECTED_RUNTIME_ENVS:
        return

    if temporary_audio_skip_enabled():
        raise RuntimeError(
            "HIMMA_TEMP_AUDIO_SKIP must be false when ENV is trial or production"
        )

    secret = os.getenv("API_SECRET_KEY", "")
    if len(secret) < 32:
        raise RuntimeError(
            "API_SECRET_KEY must contain at least 32 characters in trial/production"
        )
