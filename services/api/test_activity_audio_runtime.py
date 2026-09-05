"""Regression tests for supervisor-reviewed learning audio evidence."""

from datetime import datetime, timezone

import activity_runtime
import seed_all
from content_runtime import canonical_interaction
from db.database import SessionLocal
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    Student,
)


def _complete_pretest(level: int = 1) -> int:
    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = level
    db.add(AssessmentSession(
        student_id=student.id,
        session_type="pretest",
        status="completed",
        assigned_level=level,
        completed_at=datetime.now(timezone.utc),
    ))
    db.commit()
    student_id = student.id
    db.close()
    return student_id


def _create_audio_attempt(student_client):
    seed_all.run_seed_all()
    student_id = _complete_pretest(level=2)
    started = student_client.post("/activities/start")
    assert started.status_code == 200, started.text
    session_id = started.json()["session_id"]

    db = SessionLocal()
    candidates = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == 2,
        ContentItem.status == "approved",
    ).order_by(ContentItem.order_index).all()
    item = next(candidate for candidate in candidates if canonical_interaction(candidate) in activity_runtime.AUDIO_INTERACTIONS)
    step = sorted(item.steps, key=lambda value: value.order_index)[0]
    attempt = Attempt(session_id=session_id, item_id=item.id, status="in_progress")
    db.add(attempt)
    db.commit()
    result = (student_id, session_id, item.id, step.id, attempt.id)
    db.close()
    return result


def _audio_payload(student_id: int, step_id: int, suffix: str = "one") -> dict:
    return {
        "step_id": step_id,
        "selected_option_ids": [],
        "hint_used": False,
        "elapsed_seconds": 2,
        "declared_media_gap_skip": False,
        "audio_storage_key": f"audio/{student_id}/{suffix}.webm",
        "audio_file_size": 128,
        "audio_mime_type": "audio/webm",
        "audio_duration_seconds": 1.25,
    }


def _student_login(client):
    response = client.post("/auth/student-login", json={"access_code": "STU001"})
    assert response.status_code == 200


def _researcher_login(client):
    response = client.post("/auth/login", json={
        "username": "researcher1",
        "password": "test-only-researcher-password",
    })
    assert response.status_code == 200


class TestLearningAudioRuntime:
    def test_uploaded_audio_stays_pending_until_supervisor_grade(self, client, monkeypatch):
        _student_login(client)
        student_id, session_id, item_id, step_id, attempt_id = _create_audio_attempt(client)
        monkeypatch.setattr(activity_runtime.storage, "verify_audio", lambda *args, **kwargs: None)

        submitted = client.post(
            f"/activities/session/{session_id}/attempt/{item_id}/submit",
            json=_audio_payload(student_id, step_id),
            headers={"Idempotency-Key": "learning-audio-pending-0001"},
        )
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["awaiting_review"] is True
        assert submitted.json()["is_correct"] is None
        assert submitted.json()["activity_complete"] is False

        db = SessionLocal()
        attempt = db.query(Attempt).filter(Attempt.id == attempt_id).one()
        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt_id,
            AttemptResponse.step_id == step_id,
        ).one()
        audio = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).one()
        assert attempt.status == "in_progress"
        assert response.is_correct is None
        assert audio.status == "uploaded"
        submission_id = audio.id
        db.close()

        current = client.get(f"/activities/session/{session_id}/next")
        assert current.status_code == 200, current.text
        assert current.json()["item"]["id"] == item_id
        assert current.json()["awaiting_audio_review"] is True
        assert current.json()["audio_review_status"] == "uploaded"

        learning_view = client.get(f"/learning-experience/session/{session_id}")
        assert learning_view.status_code == 200, learning_view.text
        assert learning_view.json()["awaiting_audio_review"] is True
        assert learning_view.json()["audio_review_status"] == "uploaded"

        _researcher_login(client)
        graded = client.post(
            f"/review/audio/{submission_id}/grade",
            json={
                "is_valid": True,
                "target_units": 1,
                "deletions": 0,
                "substitutions": 0,
                "insertions": 0,
            },
        )
        assert graded.status_code == 200, graded.text

        _student_login(client)
        advanced = client.get(f"/activities/session/{session_id}/next")
        assert advanced.status_code == 200, advanced.text
        assert advanced.json()["item"]["id"] == item_id
        assert advanced.json()["step"]["id"] != step_id
        assert advanced.json()["awaiting_audio_review"] is False

        db = SessionLocal()
        attempt = db.query(Attempt).filter(Attempt.id == attempt_id).one()
        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt_id,
            AttemptResponse.step_id == step_id,
        ).one()
        audio = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).one()
        assert attempt.status == "in_progress"
        assert audio.status == "graded"
        db.close()

    def test_invalid_review_reopens_same_reading_step_for_rerecord(self, client, monkeypatch):
        _student_login(client)
        student_id, session_id, item_id, step_id, attempt_id = _create_audio_attempt(client)
        monkeypatch.setattr(activity_runtime.storage, "verify_audio", lambda *args, **kwargs: None)

        first = client.post(
            f"/activities/session/{session_id}/attempt/{item_id}/submit",
            json=_audio_payload(student_id, step_id, "first"),
            headers={"Idempotency-Key": "learning-audio-rerecord-0001"},
        )
        assert first.status_code == 200, first.text

        db = SessionLocal()
        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt_id,
            AttemptResponse.step_id == step_id,
        ).one()
        submission_id = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).one().id
        db.close()

        _researcher_login(client)
        rejected = client.post(
            f"/review/audio/{submission_id}/grade",
            json={"is_valid": False},
        )
        assert rejected.status_code == 200, rejected.text

        _student_login(client)
        current = client.get(f"/activities/session/{session_id}/next")
        assert current.status_code == 200, current.text
        assert current.json()["item"]["id"] == item_id
        assert current.json()["audio_review_status"] == "rerecord_required"
        assert current.json()["awaiting_audio_review"] is False
        assert current.json()["retry"] is True

        second = client.post(
            f"/activities/session/{session_id}/attempt/{item_id}/submit",
            json=_audio_payload(student_id, step_id, "second"),
            headers={"Idempotency-Key": "learning-audio-rerecord-0002"},
        )
        assert second.status_code == 200, second.text
        assert second.json()["awaiting_review"] is True

        db = SessionLocal()
        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt_id,
            AttemptResponse.step_id == step_id,
        ).one()
        audio = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).one()
        assert audio.status == "uploaded"
        assert audio.storage_key.endswith("second.webm")
        assert response.is_correct is None
        assert db.query(Attempt).filter(Attempt.id == attempt_id).one().status == "in_progress"
        db.close()

    def test_declared_media_gap_skip_cannot_create_completion_evidence(self, client):
        _student_login(client)
        _, session_id, item_id, step_id, attempt_id = _create_audio_attempt(client)

        rejected = client.post(
            f"/activities/session/{session_id}/attempt/{item_id}/submit",
            json={
                "step_id": step_id,
                "selected_option_ids": [],
                "hint_used": False,
                "elapsed_seconds": 1,
                "declared_media_gap_skip": True,
            },
            headers={"Idempotency-Key": "learning-skip-rejected-0001"},
        )
        assert rejected.status_code == 409
        assert "لا يمكن تجاوز" in rejected.json()["detail"]

        db = SessionLocal()
        assert db.query(Attempt).filter(Attempt.id == attempt_id).one().status == "in_progress"
        assert db.query(AttemptResponse).filter(AttemptResponse.attempt_id == attempt_id).count() == 0
        db.close()
