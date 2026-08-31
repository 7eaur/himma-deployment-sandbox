"""Regression coverage for the temporary no-microphone demo path."""

from decimal import Decimal

import seed
from adaptation import _attempt_signal, ensure_rewards
from content_runtime import canonical_interaction
from db.adaptation_models import RewardEvent
from db.database import SessionLocal
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    OperationIdempotency,
    Student,
)


AUDIO_INTERACTIONS = {"read_aloud", "timed_read_aloud"}


def _pending_audio_item(student_client):
    seed.run_seed()
    started = student_client.post("/assessment/start", json={"session_type": "pretest"})
    assert started.status_code == 200
    session = started.json()

    db = SessionLocal()
    item = next(
        candidate
        for candidate in db.query(ContentItem).filter(ContentItem.kind == "pretest_question").order_by(ContentItem.order_index).all()
        if canonical_interaction(candidate) in AUDIO_INTERACTIONS
    )
    db.add(Attempt(session_id=session["id"], item_id=item.id, status="in_progress"))
    db.commit()
    item_id = item.id
    db.close()

    payload = student_client.get(f"/assessment/session/{session['id']}/next")
    assert payload.status_code == 200
    return session, payload.json(), item_id


def test_temporary_skip_is_enabled_and_creates_no_audio(student_client):
    flags = student_client.get("/runtime-flags")
    assert flags.status_code == 200
    assert flags.json()["temporary_audio_skip"] is True

    session, payload, item_id = _pending_audio_item(student_client)
    step = payload["steps"][0]
    skipped = student_client.post(
        f"/temporary-audio/session/{session['id']}/attempt/{item_id}/skip",
        headers={"Idempotency-Key": "temporary-audio-skip-0001"},
        json={"step_id": step["id"], "elapsed_seconds": 0},
    )
    assert skipped.status_code == 200
    assert skipped.json()["temporary_audio_skip"] is True
    assert skipped.json()["is_correct"] is None
    assert skipped.json()["academically_neutral"] is True

    db = SessionLocal()
    attempt = db.query(Attempt).filter(Attempt.session_id == session["id"], Attempt.item_id == item_id).one()
    response = db.query(AttemptResponse).filter(AttemptResponse.attempt_id == attempt.id).one()
    assert response.is_correct is None
    assert response.selected_option_id is None
    assert db.query(AudioSubmission).filter(AudioSubmission.response_id == response.id).count() == 0
    marker = db.query(OperationIdempotency).filter(
        OperationIdempotency.operation == f"temporary_audio_skip:{session['id']}:{item_id}:{step['id']}"
    ).one()
    assert marker.response_json["temporary_audio_skip"] is True
    assert attempt.status == "completed"
    db.close()


def test_temporary_skip_is_rejected_when_flag_is_disabled(student_client, monkeypatch):
    session, payload, item_id = _pending_audio_item(student_client)
    step = payload["steps"][0]
    monkeypatch.setenv("HIMMA_TEMP_AUDIO_SKIP", "false")

    flags = student_client.get("/runtime-flags")
    assert flags.json()["temporary_audio_skip"] is False
    skipped = student_client.post(
        f"/temporary-audio/session/{session['id']}/attempt/{item_id}/skip",
        headers={"Idempotency-Key": "temporary-audio-skip-0002"},
        json={"step_id": step["id"]},
    )
    assert skipped.status_code == 403

    db = SessionLocal()
    assert db.query(AttemptResponse).count() == 0
    assert db.query(AudioSubmission).count() == 0
    db.close()


def test_temporary_skip_is_neutral_for_adaptation_and_rewards(student_client):
    seed.run_seed()
    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    item = next(
        candidate
        for candidate in db.query(ContentItem).filter(
            ContentItem.kind.in_(["core_activity", "reinforcement_activity"])
        ).all()
        if canonical_interaction(candidate) in AUDIO_INTERACTIONS
    )
    session = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=item.level_id,
    )
    db.add(session)
    db.flush()
    attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
    db.add(attempt)
    db.flush()
    step = item.steps[0]
    db.add(AttemptResponse(
        attempt_id=attempt.id,
        step_id=step.id,
        selected_option_id=None,
        is_correct=None,
        elapsed_seconds=0,
    ))
    db.add(OperationIdempotency(
        actor_role="student",
        actor_id=student.id,
        operation=f"temporary_audio_skip:{session.id}:{item.id}:{step.id}",
        idempotency_key="temporary-audio-neutral-0001",
        request_hash="0" * 64,
        response_json={"temporary_audio_skip": True, "academically_neutral": True},
        status_code=200,
    ))
    db.commit()

    assert _attempt_signal(db, attempt, item) is None
    ensure_rewards(db, student.id)
    assert db.query(RewardEvent).filter(RewardEvent.attempt_id == attempt.id).count() == 0
    db.close()


def test_pretest_scoring_excludes_temporary_audio_skips_from_denominator(student_client):
    seed.run_seed()
    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    session = AssessmentSession(student_id=student.id, session_type="pretest", status="in_progress")
    db.add(session)
    db.flush()

    items = db.query(ContentItem).filter(ContentItem.kind == "pretest_question").order_by(ContentItem.order_index).all()
    assert len(items) == 30
    skipped_count = 0
    for item in items:
        attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
        db.add(attempt)
        db.flush()
        step = item.steps[0]
        if canonical_interaction(item) in AUDIO_INTERACTIONS:
            skipped_count += 1
            db.add(AttemptResponse(
                attempt_id=attempt.id,
                step_id=step.id,
                selected_option_id=None,
                is_correct=None,
                elapsed_seconds=0,
            ))
            db.add(OperationIdempotency(
                actor_role="student",
                actor_id=student.id,
                operation=f"temporary_audio_skip:{session.id}:{item.id}:{step.id}",
                idempotency_key=f"temporary-score-skip-{item.id:04d}",
                request_hash="1" * 64,
                response_json={"temporary_audio_skip": True, "academically_neutral": True},
                status_code=200,
            ))
        else:
            db.add(AttemptResponse(
                attempt_id=attempt.id,
                step_id=step.id,
                selected_option_id=None,
                is_correct=True,
                elapsed_seconds=0,
            ))
    db.commit()
    session_id = session.id
    db.close()

    assert skipped_count > 0
    finished = student_client.post(f"/assessment/session/{session_id}/finish")
    assert finished.status_code == 200, finished.text
    result = finished.json()
    assert Decimal(str(result["final_score"])) == Decimal("100")
    # The source requires word-reading and text-accuracy gates for L3 but does
    # not approve their numeric thresholds.  A perfect test/demo score therefore
    # remains academically provisional at L2 instead of fabricating a gate.
    assert result["assigned_level"] == 2
    assert result["placement_provisional"] is True
    assert result["placement_reason"] == "l3_gate_thresholds_not_approved_or_configured"
    assert result["temporary_audio_skips"] == skipped_count
    assert result["scorable_units"] == 30 - skipped_count

    db = SessionLocal()
    assert db.query(AudioSubmission).count() == 0
    db.close()
