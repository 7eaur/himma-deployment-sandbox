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
    def test_uploaded_audio_stays_pending_but_navigation_continues(self, client, monkeypatch):
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

        db = SessionLocal()
        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt_id,
            AttemptResponse.step_id == step_id,
        ).one()
        audio = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).one()
        submission_id = audio.id
        assert response.is_correct is None
        assert audio.status == "uploaded"
        db.close()

        # The submitted recording remains unresolved, but the learner is allowed
        # to leave that reading round and continue their remaining learning work.
        current = client.get(f"/activities/session/{session_id}/next")
        assert current.status_code == 200, current.text
        current_payload = current.json()
        assert current_payload is None or not (
            current_payload["item"]["id"] == item_id
            and current_payload["step"]["id"] == step_id
        )

        status = client.get("/activities/status")
        assert status.status_code == 200, status.text
        assert status.json()["audio_review_pending"] is True
        assert status.json()["pending_count"] >= 1

        dashboard_tasks = client.get("/review/student-audio")
        assert dashboard_tasks.status_code == 200, dashboard_tasks.text
        task = next(row for row in dashboard_tasks.json() if row["id"] == submission_id)
        assert task["status"] == "uploaded"
        assert task["can_rerecord"] is False

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
        dashboard_tasks = client.get("/review/student-audio")
        assert dashboard_tasks.status_code == 200
        assert all(row["id"] != submission_id for row in dashboard_tasks.json())

        db = SessionLocal()
        response = db.query(AttemptResponse).filter(
            AttemptResponse.attempt_id == attempt_id,
            AttemptResponse.step_id == step_id,
        ).one()
        audio = db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).one()
        assert audio.status == "graded"
        db.close()

    def test_invalid_learning_review_waits_for_dashboard_open_before_rerecord(self, client, monkeypatch):
        _student_login(client)
        student_id, session_id, item_id, step_id, attempt_id = _create_audio_attempt(client)
        monkeypatch.setattr(activity_runtime.storage, "verify_audio", lambda *args, **kwargs: None)

        first = client.post(
            f"/activities/session/{session_id}/attempt/{item_id}/submit",
            json=_audio_payload(student_id, step_id, "first"),
            headers={"Idempotency-Key": "learning-audio-rerecord-0001"},
        )
        assert first.status_code == 200, first.text

        # Move the learner forward once so the audio attempt is no longer the
        # active navigation target while the supervisor is reviewing it.
        advanced_before_review = client.get(f"/activities/session/{session_id}/next")
        assert advanced_before_review.status_code == 200

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
        assert rejected.json()["rerecord_queued"] is True

        _student_login(client)
        tasks = client.get("/review/student-audio")
        assert tasks.status_code == 200, tasks.text
        task = next(row for row in tasks.json() if row["id"] == submission_id)
        assert task["status"] == "rerecord_required"
        assert task["can_rerecord"] is True

        # A reviewer request alone must not pull the learner back into the old
        # reading round. Reopening happens only after their dashboard action.
        current = client.get(f"/activities/session/{session_id}/next")
        assert current.status_code == 200, current.text
        current_payload = current.json()
        assert current_payload is None or not (
            current_payload["item"]["id"] == item_id
            and current_payload["step"]["id"] == step_id
        )

        opened = client.post(f"/review/student-audio/{submission_id}/begin-rerecord")
        assert opened.status_code == 200, opened.text
        assert opened.json()["item_id"] == item_id
        assert opened.json()["step_id"] == step_id

        rerecord = client.get(f"/activities/session/{session_id}/next")
        assert rerecord.status_code == 200, rerecord.text
        assert rerecord.json()["item"]["id"] == item_id
        assert rerecord.json()["step"]["id"] == step_id
        assert rerecord.json()["audio_review_status"] == "rerecord_required"
        assert rerecord.json()["retry"] is True

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
