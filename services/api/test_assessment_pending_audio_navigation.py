"""Phase F regression: uploaded assessment audio must block learner navigation.

The assessment submission row may already exist for persistence/history, but an
``uploaded`` recording is not reviewed evidence. Neither the raw assessment
navigation endpoint nor the clean student-view endpoint may advance past it,
and progress must not count it as completed until supervisor review.
"""

import assessment
import seed
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student


def test_uploaded_assessment_audio_blocks_next_and_progress_until_review(client, monkeypatch):
    seed.run_seed()
    monkeypatch.setattr(assessment.storage, "verify_audio", lambda *_args: None)

    assert client.post(
        "/auth/student-login", json={"access_code": "STU001"}
    ).status_code == 200
    session_id = client.post(
        "/assessment/start", json={"session_type": "pretest"}
    ).json()["id"]

    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        session = db.query(AssessmentSession).filter(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == student.id,
        ).one()
        audio_item = db.query(ContentItem).filter(
            ContentItem.kind == "pretest_question",
            ContentItem.interaction_type == "read_aloud",
        ).order_by(ContentItem.order_index).first()
        assert audio_item is not None
        attempt = Attempt(session_id=session.id, item_id=audio_item.id, status="in_progress")
        db.add(attempt)
        db.commit()
        student_id = student.id
        item_id = audio_item.id
        step_id = audio_item.steps[0].id
    finally:
        db.close()

    submitted = client.post(
        f"/assessment/session/{session_id}/attempt/{item_id}/submit",
        headers={"Idempotency-Key": "phase-f-pending-audio-0001"},
        json={
            "step_id": step_id,
            "audio_storage_key": f"audio/{student_id}/phase-f-pending.webm",
            "audio_file_size": 512,
            "audio_mime_type": "audio/webm",
            "audio_duration_seconds": 4,
            "elapsed_seconds": 4,
        },
    )
    assert submitted.status_code == 200
    assert submitted.json()["is_correct"] is None

    progress = client.get(f"/assessment/session/{session_id}/progress")
    assert progress.status_code == 200
    assert progress.json()["completed_items"] == 0
    assert progress.json()["completed_steps"] == 0
    assert progress.json()["has_pending_item"] is True

    raw_next = client.get(f"/assessment/session/{session_id}/next")
    assert raw_next.status_code == 409
    assert "انتظار المراجعة" in raw_next.json()["detail"]

    clean_next = client.get(f"/assessment-view/session/{session_id}/next")
    assert clean_next.status_code == 409
    assert "انتظار المراجعة" in clean_next.json()["detail"]

    assert client.post(
        "/auth/login",
        json={
            "username": "researcher1",
            "password": "test-only-researcher-password",
        },
    ).status_code == 200
    pending = client.get("/review/pending-audio")
    assert pending.status_code == 200
    submission_id = next(
        row["id"] for row in pending.json()
        if row["student_id"] == student_id
    )
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
    assert graded.status_code == 200

    assert client.post(
        "/auth/student-login", json={"access_code": "STU001"}
    ).status_code == 200
    resumed = client.get(f"/assessment/session/{session_id}/next")
    assert resumed.status_code == 200
    assert resumed.json() is not None
    assert resumed.json()["id"] != item_id
