"""Regression tests for the posttest journey gate.

Posttest is a measurement after the required learning journey, never an exit
from L1/L2 simply because ten activities in the current level were completed.
"""

from datetime import datetime, timezone

import seed
from conftest import TestingSessionLocal
from db.models import AssessmentSession, Attempt, ContentItem, Student


def _complete_core_level(db, student_id: int, level_id: int) -> AssessmentSession:
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
        .filter(ContentItem.kind == "core_activity", ContentItem.level_id == level_id)
        .order_by(ContentItem.order_index)
        .all()
    )
    assert len(items) == 10
    for item in items:
        db.add(Attempt(
            session_id=session.id,
            item_id=item.id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        ))
    db.flush()
    return session


def _complete_pretest(db, student_id: int, assigned_level: int) -> None:
    db.add(AssessmentSession(
        student_id=student_id,
        session_type="pretest",
        status="completed",
        assigned_level=assigned_level,
        final_score=50,
        completed_at=datetime.now(timezone.utc),
    ))
    db.flush()


def test_supervisor_cannot_open_posttest_after_completed_l1_only(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 1
    _complete_pretest(db, student.id, 1)
    _complete_core_level(db, student.id, 1)
    student_id = student.id
    db.commit()
    db.close()

    response = researcher_client.post(
        f"/researcher/students/{student_id}/posttest-access",
        json={"enabled": True},
    )
    assert response.status_code == 409
    assert "المستوى الثالث" in response.json()["detail"]

    student_state = researcher_client.get(f"/researcher/students/{student_id}")
    assert student_state.status_code == 200
    assert student_state.json()["posttest_eligible"] is False


def test_profile_stays_in_learning_after_completed_l2_even_if_flag_is_stale(student_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 2
    student.posttest_enabled = True  # simulate legacy/stale flag; journey remains authoritative
    _complete_pretest(db, student.id, 2)
    _complete_core_level(db, student.id, 2)
    db.commit()
    db.close()

    profile = student_client.get("/profile")
    assert profile.status_code == 200
    assert profile.json()["next_action"] == "learning"


def test_supervisor_can_open_posttest_after_completed_l3(researcher_client):
    seed.run_seed()
    db = TestingSessionLocal()
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    student.current_level = 3
    _complete_pretest(db, student.id, 3)
    _complete_core_level(db, student.id, 3)
    student_id = student.id
    db.commit()
    db.close()

    state_before = researcher_client.get(f"/researcher/students/{student_id}")
    assert state_before.status_code == 200
    assert state_before.json()["posttest_eligible"] is True

    response = researcher_client.post(
        f"/researcher/students/{student_id}/posttest-access",
        json={"enabled": True},
    )
    assert response.status_code == 200
    assert response.json()["posttest_enabled"] is True
