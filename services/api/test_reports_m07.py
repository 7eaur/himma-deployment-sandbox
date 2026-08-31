from decimal import Decimal

from conftest import TestingSessionLocal
from db.models import AssessmentSession, Student


def _student(db):
    return db.query(Student).filter(Student.access_code == "STU001").one()


def test_report_summary_uses_persisted_scores_without_recalculating(researcher_client):
    db = TestingSessionLocal()
    student = _student(db)
    db.add_all([
        AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            final_score=Decimal("40.0000"),
            assigned_level=1,
            elapsed_seconds=120,
        ),
        AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="completed",
            assigned_level=1,
            elapsed_seconds=300,
        ),
        AssessmentSession(
            student_id=student.id,
            session_type="posttest",
            status="completed",
            final_score=Decimal("70.0000"),
            assigned_level=2,
            elapsed_seconds=90,
        ),
    ])
    db.commit()
    db.close()

    response = researcher_client.get("/researcher/reports/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["cohort"]["students"] == 1
    assert payload["cohort"]["completed_pretests"] == 1
    assert payload["cohort"]["completed_posttests"] == 1
    assert payload["cohort"]["paired_pre_post"] == 1
    assert payload["cohort"]["average_pretest_score"] == 40.0
    assert payload["cohort"]["average_posttest_score"] == 70.0
    assert payload["cohort"]["average_absolute_improvement_points"] == 30.0

    report = payload["students"][0]
    assert report["starting_level"] == 1
    assert report["final_level"] == 2
    assert report["pretest"]["score"] == 40.0
    assert report["posttest"]["score"] == 70.0
    assert report["improvement"]["absolute_percentage_points"] == 30.0
    assert report["improvement"]["relative_percent"] == 75.0
    assert report["engagement"]["assessment_seconds"] == 210
    assert report["engagement"]["learning_seconds"] == 300
    assert report["speech_evidence"]["calibrated"] is False
    assert report["speech_evidence"]["error_categories"] is None


def test_relative_improvement_is_null_when_pretest_score_is_zero(researcher_client):
    db = TestingSessionLocal()
    student = _student(db)
    student_id = student.id
    db.add_all([
        AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            final_score=Decimal("0.0000"),
            assigned_level=1,
        ),
        AssessmentSession(
            student_id=student.id,
            session_type="posttest",
            status="completed",
            final_score=Decimal("50.0000"),
            assigned_level=2,
        ),
    ])
    db.commit()
    db.close()

    response = researcher_client.get(f"/researcher/reports/students/{student_id}")
    assert response.status_code == 200
    improvement = response.json()["improvement"]
    assert improvement["absolute_percentage_points"] == 50.0
    assert improvement["relative_percent"] is None
    assert improvement["relative_percent_defined"] is False


def test_incomplete_posttest_does_not_invent_improvement(researcher_client):
    db = TestingSessionLocal()
    student = _student(db)
    db.add_all([
        AssessmentSession(
            student_id=student.id,
            session_type="pretest",
            status="completed",
            final_score=Decimal("65.0000"),
            assigned_level=2,
        ),
        AssessmentSession(
            student_id=student.id,
            session_type="posttest",
            status="in_progress",
            final_score=None,
            assigned_level=None,
        ),
    ])
    db.commit()
    db.close()

    response = researcher_client.get("/researcher/reports/summary")
    assert response.status_code == 200
    report = response.json()["students"][0]
    assert report["posttest"]["score"] is None
    assert report["final_level"] is None
    assert report["improvement"]["absolute_percentage_points"] is None
    assert report["improvement"]["relative_percent"] is None


def test_student_report_requires_existing_student(researcher_client):
    response = researcher_client.get("/researcher/reports/students/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "الطالب غير موجود"
