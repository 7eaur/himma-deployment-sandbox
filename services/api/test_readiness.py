"""M09 release-readiness regression coverage."""

import pytest

import main
import readiness
from runtime_flags import validate_runtime_safety


_REQUIRED_ENV = {
    "DATABASE_URL": "postgresql://example.invalid/himma",
    "API_SECRET_KEY": "x" * 40,
    "S3_ACCESS_KEY": "test-access",
    "S3_SECRET_KEY": "test-secret",
    "S3_BUCKET_NAME": "himma-audio-test",
    "REDIS_URL": "redis://localhost:6379/0",
}


def _set_required_env(monkeypatch):
    for name, value in _REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)


def test_trial_runtime_rejects_temporary_audio_skip(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("ENV", "trial")
    monkeypatch.setenv("HIMMA_TEMP_AUDIO_SKIP", "true")

    with pytest.raises(RuntimeError, match="HIMMA_TEMP_AUDIO_SKIP must be false"):
        validate_runtime_safety()


def test_production_runtime_requires_strong_api_secret(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("HIMMA_TEMP_AUDIO_SKIP", "false")
    monkeypatch.setenv("API_SECRET_KEY", "too-short")

    with pytest.raises(RuntimeError, match="at least 32 characters"):
        validate_runtime_safety()


def test_trial_runtime_accepts_audio_skip_disabled(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("ENV", "trial")
    monkeypatch.setenv("HIMMA_TEMP_AUDIO_SKIP", "false")

    validate_runtime_safety()


def test_readiness_report_is_sanitized_and_requires_all_components(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setattr(readiness, "_database_ready", lambda: True)
    monkeypatch.setattr(readiness, "_storage_ready", lambda: False)
    monkeypatch.setattr(readiness, "_redis_ready", lambda: True)

    report = readiness.readiness_report()

    assert report == {
        "status": "not_ready",
        "service": "himma-api",
        "checks": {
            "config": "ok",
            "database": "ok",
            "storage": "unavailable",
            "redis": "ok",
        },
    }
    assert "password" not in str(report).lower()
    assert "secret" not in str(report).lower()


def test_ready_endpoint_returns_200_or_503_from_readiness_state(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "readiness_report",
        lambda: {
            "status": "ready",
            "service": "himma-api",
            "checks": {"config": "ok", "database": "ok", "storage": "ok", "redis": "ok"},
        },
    )
    assert client.get("/ready").status_code == 200

    monkeypatch.setattr(
        main,
        "readiness_report",
        lambda: {
            "status": "not_ready",
            "service": "himma-api",
            "checks": {"config": "ok", "database": "unavailable", "storage": "ok", "redis": "ok"},
        },
    )
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "unavailable"
