"""Stage-2 activity runtime regressions plus V4 promotion continuity."""

from datetime import datetime, timezone

import seed
from db.database import SessionLocal
from db.models import AssessmentSession, Attempt, AttemptResponse, ContentItem, ContentOption, Student


def _complete_pretest(access_code: str = "STU001", level: int = 1) -> int:
    db = SessionLocal()
    student = db.query(Student).filter(Student.access_code == access_code).one()
    student.current_level = level
    existing = db.query(AssessmentSession).filter(
        AssessmentSession.student_id == student.id,
        AssessmentSession.session_type == "pretest",
    ).first()
    if not existing:
        db.add(AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            assigned_level=level,
            completed_at=datetime.now(timezone.utc),
        ))
    else:
        existing.status = "completed"
        existing.assigned_level = level
        existing.completed_at = datetime.now(timezone.utc)
    db.commit()
    student_id = student.id
    db.close()
    return student_id


def _ordered_option_ids(step_id: int) -> list[int]:
    db = SessionLocal()
    ids = [row.id for row in db.query(ContentOption).filter(
        ContentOption.step_id == step_id
    ).order_by(ContentOption.order_index).all()]
    db.close()
    return ids


def _correct_option_id(step_id: int) -> int:
    db = SessionLocal()
    row = db.query(ContentOption).filter(
        ContentOption.step_id == step_id,
        ContentOption.is_correct.is_(True),
    ).first()
    assert row is not None
    option_id = row.id
    db.close()
    return option_id


def _mark_audio_round_reviewed(session_id: int, item_id: int, step_id: int) -> None:
    """Finish audio evidence for lifecycle routing tests only.

    Audio upload/review has dedicated tests; this helper does not invent speech
    metrics and only marks the already-targeted reading step as reviewed/correct.
    """
    db = SessionLocal()
    attempt = db.query(Attempt).filter(
        Attempt.session_id == session_id,
        Attempt.item_id == item_id,
        Attempt.status == "in_progress",
    ).one()
    existing = db.query(AttemptResponse).filter(
        AttemptResponse.attempt_id == attempt.id,
        AttemptResponse.step_id == step_id,
    ).first()
    if not existing:
        db.add(AttemptResponse(
            attempt_id=attempt.id,
            step_id=step_id,
            selected_option_id=None,
            is_correct=True,
            elapsed_seconds=1,
        ))
        db.commit()
    db.close()


def _completed_core_ids(session_id: int, level_id: int) -> list[str]:
    db = SessionLocal()
    rows = (
        db.query(ContentItem)
        .join(Attempt, Attempt.item_id == ContentItem.id)
        .filter(
            Attempt.session_id == session_id,
            Attempt.status == "completed",
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .order_by(ContentItem.order_index)
        .all()
    )
    ids = [(item.template_data or {}).get("canonical_id") for item in rows]
    db.close()
    return ids


class TestActivityLifecycle:
    def test_learning_requires_completed_pretest(self, student_client):
        status = student_client.get("/activities/status")
        assert status.status_code == 200
        assert status.json()["available"] is False
        assert status.json()["reason"] == "pretest_required"
        assert student_client.post("/activities/start").status_code == 409

    def test_level_one_resumes_and_early_promotion_switches_to_fresh_level_session(self, student_client):
        seed.run_seed()
        _complete_pretest(level=1)

        started = student_client.post("/activities/start")
        assert started.status_code == 200
        level_one_session_id = started.json()["session_id"]
        session_id = level_one_session_id
        assert started.json()["level_id"] == 1
        assert started.json()["total_items"] == 10

        resumed = student_client.post("/activities/start")
        assert resumed.status_code == 200
        assert resumed.json()["session_id"] == level_one_session_id

        seen_level_one: set[str] = set()
        promoted = False
        safety = 0
        while not promoted:
            safety += 1
            assert safety < 100, "V4 level-one promotion did not converge"
            response = student_client.get(f"/activities/session/{session_id}/next")
            assert response.status_code == 200, response.text
            activity = response.json()
            assert activity is not None

            # V4 promotion must return a payload belonging to the fresh target
            # session immediately; the client must never submit into the closed
            # historical L1 session.
            if activity["item"]["level_id"] == 2:
                assert activity["session_id"] != level_one_session_id
                session_id = activity["session_id"]
                promoted = True
                break

            assert activity["item"]["level_id"] == 1
            assert activity["session_id"] == level_one_session_id
            seen_level_one.add(activity["item"]["canonical_id"])
            step = activity["step"]
            interaction = activity["item"]["interaction_type"]

            if interaction in {"read_aloud", "timed_read_aloud"} and not step["media_gaps"]:
                _mark_audio_round_reviewed(session_id, activity["item"]["id"], step["id"])
                continue

            if step["media_gaps"]:
                payload = {
                    "step_id": step["id"],
                    "selected_option_ids": [],
                    "hint_used": False,
                    "elapsed_seconds": 1,
                    "declared_media_gap_skip": True,
                }
            elif interaction in {"sequence", "memory_sequence", "path_sequence", "build_word"}:
                payload = {
                    "step_id": step["id"],
                    "selected_option_ids": _ordered_option_ids(step["id"]),
                    "hint_used": False,
                    "elapsed_seconds": 1,
                    "declared_media_gap_skip": False,
                }
            else:
                payload = {
                    "step_id": step["id"],
                    "selected_option_ids": [_correct_option_id(step["id"])],
                    "hint_used": False,
                    "elapsed_seconds": 1,
                    "declared_media_gap_skip": False,
                }

            key = f"activity-test-{session_id}-{step['id']}-{activity['attempts_used'] + 1}"
            submitted = student_client.post(
                f"/activities/session/{session_id}/attempt/{activity['item']['id']}/submit",
                json=payload,
                headers={"Idempotency-Key": key},
            )
            assert submitted.status_code == 200, submitted.text

        assert len(seen_level_one) >= 6
        assert len(seen_level_one) < 10

        db = SessionLocal()
        old_session = db.query(AssessmentSession).filter(AssessmentSession.id == level_one_session_id).one()
        new_session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).one()
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        assert old_session.status == "completed"
        assert old_session.assigned_level == 1
        assert new_session.status == "in_progress"
        assert new_session.assigned_level == 2
        assert student.current_level == 2
        assert db.query(ContentItem).filter(ContentItem.kind == "core_activity", ContentItem.level_id == 1).count() == 10
        db.close()

    def test_structured_activity_submission_is_idempotent(self, student_client):
        seed.run_seed()
        _complete_pretest(level=1)
        session_id = student_client.post("/activities/start").json()["session_id"]
        activity = student_client.get(f"/activities/session/{session_id}/next").json()
        step = activity["step"]
        payload = {
            "step_id": step["id"],
            "selected_option_ids": [_correct_option_id(step["id"])],
            "hint_used": False,
            "elapsed_seconds": 3,
            "declared_media_gap_skip": False,
        }
        headers = {"Idempotency-Key": "activity-idempotency-0001"}
        first = student_client.post(
            f"/activities/session/{session_id}/attempt/{activity['item']['id']}/submit",
            json=payload,
            headers=headers,
        )
        replay = student_client.post(
            f"/activities/session/{session_id}/attempt/{activity['item']['id']}/submit",
            json=payload,
            headers=headers,
        )
        assert first.status_code == 200
        assert replay.status_code == 200
        assert replay.json() == first.json()

    def test_only_assigned_level_core_items_are_selected(self, student_client):
        seed.run_seed()
        _complete_pretest(level=3)
        session_id = student_client.post("/activities/start").json()["session_id"]
        activity = student_client.get(f"/activities/session/{session_id}/next").json()
        assert activity["item"]["level_id"] == 3
        assert activity["item"]["canonical_id"] == "L3-CORE-01"
        assert activity["item"]["interaction_type"] == "read_aloud"

        db = SessionLocal()
        assert db.query(ContentItem).filter(ContentItem.kind == "core_activity", ContentItem.level_id == 3).count() == 10
        db.close()
