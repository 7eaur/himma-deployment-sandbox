"""M04 regression tests for the student-facing L1 -> L2 -> L3 journey."""

from datetime import datetime, timezone

import seed
from conftest import TestingSessionLocal
from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, ContentItem, Student


def _complete_level(db, student_id: int, level_id: int) -> AssessmentSession:
    session = AssessmentSession(
        student_id=student_id,
        session_type="core",
        status="completed",
        assigned_level=level_id,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.flush()
    items = (
        db.query(ContentItem)
        .filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == level_id,
        )
        .order_by(ContentItem.order_index)
        .all()
    )
    assert len(items) == 10
    for item in items:
        db.add(
            Attempt(
                session_id=session.id,
                item_id=item.id,
                status="completed",
                completed_at=datetime.now(timezone.utc),
            )
        )
    db.flush()
    return session


def test_journey_is_locked_before_pretest(student_client):
    response = student_client.get("/journey")
    assert response.status_code == 200
    data = response.json()
    assert data["pretest_completed"] is False
    assert data["starting_level"] is None
    assert [level["state"] for level in data["levels"]] == ["locked", "locked", "locked"]
    assert data["learning_journey_completed"] is False
    assert data["posttest_ready"] is False


def test_journey_distinguishes_skipped_completed_and_active_levels(student_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 3
    db.add(
        AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            assigned_level=2,
            final_score=75,
            completed_at=datetime.now(timezone.utc),
        )
    )
    _complete_level(db, student.id, 2)
    level3 = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=3,
    )
    db.add(level3)
    db.commit()
    db.close()

    response = student_client.get("/journey")
    assert response.status_code == 200
    data = response.json()
    assert data["starting_level"] == 2
    assert data["current_level"] == 3
    assert [level["state"] for level in data["levels"]] == ["skipped", "completed", "active"]
    assert data["levels"][1]["completed_items"] == 10
    assert data["levels"][2]["completed_items"] == 0
    assert data["learning_journey_completed"] is False


def test_journey_marks_early_promoted_l1_complete_without_requiring_ten_core(student_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 2
    db.add(
        AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            assigned_level=1,
            final_score=45,
            completed_at=datetime.now(timezone.utc),
        )
    )
    level1 = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="completed",
        assigned_level=1,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(level1)
    db.flush()
    level1_items = (
        db.query(ContentItem)
        .filter(ContentItem.kind == "core_activity", ContentItem.level_id == 1)
        .order_by(ContentItem.order_index)
        .limit(6)
        .all()
    )
    assert len(level1_items) == 6
    for item in level1_items:
        db.add(
            Attempt(
                session_id=level1.id,
                item_id=item.id,
                status="completed",
                completed_at=datetime.now(timezone.utc),
            )
        )
    level2 = AssessmentSession(
        student_id=student.id,
        session_type="core",
        status="in_progress",
        assigned_level=2,
    )
    db.add(level2)
    db.flush()
    db.add(
        AdaptationDecision(
            student_id=student.id,
            decision_source="automatic",
            action="promote",
            mastery_score=95,
            previous_level=1,
            new_level=2,
            weakest_skill_id=None,
            recommended_item_id=None,
            valid_attempt_count=6,
            consecutive_low_count=0,
            snapshot_key="journey:early-promotion:l1",
            explanation={
                "policy_version": "HIMMA_ADAPTIVE_V4_PILOT",
                "reason": "early_promotion_gates_passed",
                "journey_transition": "L1->L2",
                "previous_session_id": level1.id,
                "next_session_id": level2.id,
            },
        )
    )
    db.commit()
    db.close()

    response = student_client.get("/journey")
    assert response.status_code == 200
    data = response.json()
    assert data["starting_level"] == 1
    assert data["current_level"] == 2
    assert [level["state"] for level in data["levels"]] == ["completed", "active", "locked"]
    assert data["levels"][0]["completed_items"] == 6
    assert data["levels"][0]["total_items"] == 10
    assert data["learning_journey_completed"] is False
    assert data["posttest_ready"] is False


def test_posttest_ready_only_after_completed_level_three_and_supervisor_enable(student_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 3
    student.posttest_enabled = True
    db.add(
        AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            assigned_level=3,
            final_score=90,
            completed_at=datetime.now(timezone.utc),
        )
    )
    _complete_level(db, student.id, 3)
    db.commit()
    db.close()

    response = student_client.get("/journey")
    assert response.status_code == 200
    data = response.json()
    assert [level["state"] for level in data["levels"]] == ["skipped", "skipped", "completed"]
    assert data["learning_journey_completed"] is True
    assert data["posttest_ready"] is True
