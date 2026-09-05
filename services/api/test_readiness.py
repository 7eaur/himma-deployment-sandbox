"""M09 release-readiness regression coverage."""

from pathlib import Path

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


def _patch_component_checks(monkeypatch, *, content=True, approved_audio=True, storage=True, redis=True):
    monkeypatch.setattr(readiness, "_database_ready", lambda: True)
    monkeypatch.setattr(readiness, "_content_ready", lambda: content)
    monkeypatch.setattr(readiness, "_approved_audio_ready", lambda: approved_audio)
    monkeypatch.setattr(readiness, "_storage_ready", lambda: storage)
    monkeypatch.setattr(readiness, "_redis_ready", lambda: redis)


def test_student_audio_bypass_route_is_absent(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("ENV", "trial")
    # A stale deployment setting cannot re-enable the deleted feature.
    monkeypatch.setenv("HIMMA_TEMP_AUDIO_SKIP", "true")
    validate_runtime_safety()

    paths = {getattr(route, "path", "") for route in main.app.routes}
    assert not any("temporary-audio" in path for path in paths)


def test_production_runtime_requires_strong_api_secret(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("API_SECRET_KEY", "too-short")

    with pytest.raises(RuntimeError, match="at least 32 characters"):
        validate_runtime_safety()


def test_trial_runtime_accepts_strong_secret(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.setenv("ENV", "trial")

    validate_runtime_safety()


def test_readiness_report_is_sanitized_and_requires_all_components(monkeypatch):
    _set_required_env(monkeypatch)
    _patch_component_checks(monkeypatch, storage=False)

    report = readiness.readiness_report()

    assert report == {
        "status": "not_ready",
        "service": "himma-api",
        "checks": {
            "config": "ok",
            "database": "ok",
            "content": "ok",
            "approved_audio": "ok",
            "storage": "unavailable",
            "redis": "ok",
        },
    }
    assert "password" not in str(report).lower()
    assert "secret" not in str(report).lower()


def test_readiness_fails_closed_when_content_projection_is_stale(monkeypatch):
    _set_required_env(monkeypatch)
    _patch_component_checks(monkeypatch, content=False)

    report = readiness.readiness_report()

    assert report["status"] == "not_ready"
    assert report["checks"]["content"] == "unavailable"


def test_readiness_fails_closed_when_approved_audio_contract_is_missing(monkeypatch):
    _set_required_env(monkeypatch)
    _patch_component_checks(monkeypatch, approved_audio=False)

    report = readiness.readiness_report()

    assert report["status"] == "not_ready"
    assert report["checks"]["approved_audio"] == "unavailable"


def test_approved_audio_probe_requires_exact_semantics_and_both_binary_variants(tmp_path, monkeypatch):
    audio_root = tmp_path / "HIMMA_AUDIO_V1"
    wav_root = audio_root / "wav_master"
    mp3_root = audio_root / "web_mp3"
    wav_root.mkdir(parents=True)
    mp3_root.mkdir(parents=True)
    manifest = audio_root / "manifest.csv"

    rows = [
        ("LET-01", "مَ"),
        ("SYL-13", "سَا"),
        ("WRD-29", "موز"),
        ("INS-01", "قصة ليان في المزرعة"),
        ("INS-02", "قصة نادر في الشاطئ"),
    ]
    manifest.write_text(
        "id,text_ar,filename_wav,filename_mp3,status\n"
        + "".join(f"{asset},{text},{asset}.wav,{asset}.mp3,approved\n" for asset, text in rows),
        encoding="utf-8",
    )
    for asset, _ in rows:
        (wav_root / f"{asset}.wav").write_bytes(b"wav")
        (mp3_root / f"{asset}.mp3").write_bytes(b"mp3")

    monkeypatch.setattr(readiness, "_AUDIO_ROOT", audio_root)
    monkeypatch.setattr(readiness, "_AUDIO_MANIFEST", manifest)
    assert readiness._approved_audio_ready() is True

    (mp3_root / "INS-02.mp3").unlink()
    assert readiness._approved_audio_ready() is False


def test_ready_endpoint_returns_200_or_503_from_readiness_state(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "readiness_report",
        lambda: {
            "status": "ready",
            "service": "himma-api",
            "checks": {
                "config": "ok",
                "database": "ok",
                "content": "ok",
                "approved_audio": "ok",
                "storage": "ok",
                "redis": "ok",
            },
        },
    )
    assert client.get("/ready").status_code == 200

    monkeypatch.setattr(
        main,
        "readiness_report",
        lambda: {
            "status": "not_ready",
            "service": "himma-api",
            "checks": {
                "config": "ok",
                "database": "ok",
                "content": "unavailable",
                "approved_audio": "ok",
                "storage": "ok",
                "redis": "ok",
            },
        },
    )
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["content"] == "unavailable"
