"""M09 longitudinal UAT contract for one synthetic candidate.

This test closes the missing *cross-slice* evidence gap: one student keeps the
same identity and immutable history from placement through L1/L2 promotion,
targeted reinforcement + source verification, full L3 evidence, supervisor
posttest authorization, posttest result, reports, and XLSX/PDF exports.

It deliberately does not duplicate the real browser/MinIO recording mechanics:
the exact-candidate Quality Gate also runs ``vertical-slice.spec.ts``, which
proves the 30-item assessment UI, browser recording upload, and manual audio
review.  Here assessment sessions are persisted snapshots so this test can
focus on the previously missing longitudinal handoffs without inventing speech
scores or making report data a mastery source.
"""

from __future__ import annotations

from datetime import datetime, timezone

import seed_all
from adaptation import _load_policy
from adaptation_runtime import prepare_next_for_student
from conftest import TestingSessionLocal
from content_runtime import canonical_interaction
from db.activity_models import ActivityStepResponse
from db.adaptation_models import AdaptationDecision
from db.models import AssessmentSession, Attempt, AttemptResponse, AuditLog, ContentItem, Skill, Student
from db.reinforcement_models import ReinforcementCycle
from journey import build_journey_summary
from reinforcement_cycles import ensure_cycle, finish_verification_step, mark_reinforcement_completed


AUDIO_INTERACTIONS = {"read_aloud", "timed_read_aloud"}


def _canonical_item(db, canonical_id: str) -> ContentItem:
    for item in db.query(ContentItem).all():
        if (item.template_data or {}).get("canonical_id") == canonical_id:
            return item
    raise AssertionError(f"Missing seeded content item {canonical_id}")


def _persist_assessment_snapshot(
    db,
    *,
    student: Student,
    session_type: str,
    score: float,
    assigned_level: int,
) -> AssessmentSession:
    """Persist the already-proven assessment outcome plus all 30 item attempts."""
    kind = "pretest_question" if session_type == "pretest" else "posttest_question"
    items = db.query(ContentItem).filter(ContentItem.kind == kind).order_by(ContentItem.order_index).all()
    assert len(items) == 30
    session = AssessmentSession(
        student_id=student.id,
        session_type=session_type,
        status="completed",
        final_score=score,
        assigned_level=assigned_level,
        elapsed_seconds=900,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.flush()
    for item in items:
        db.add(Attempt(
            session_id=session.id,
            item_id=item.id,
            status="completed",
            elapsed_seconds=20,
            completed_at=datetime.now(timezone.utc),
        ))
    student.current_level = assigned_level
    db.flush()
    return session


def _complete_learning_item(db, session: AssessmentSession, item: ContentItem, *, correct: bool = True) -> Attempt:
    """Persist valid learning evidence without fabricating speech-analysis metrics."""
    attempt = Attempt(
        session_id=session.id,
        item_id=item.id,
        status="completed",
        elapsed_seconds=max(1, len(item.steps)),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(attempt)
    db.flush()
    assert item.steps
    interaction = canonical_interaction(item)
    for step in item.steps:
        if interaction in AUDIO_INTERACTIONS:
            # Human-reviewed learning evidence may be represented by the final
            # correctness only. No ASR/phoneme/WER claim is invented here.
            db.add(AttemptResponse(
                attempt_id=attempt.id,
                step_id=step.id,
                selected_option_id=None,
                is_correct=correct,
                elapsed_seconds=1,
            ))
        else:
            db.add(ActivityStepResponse(
                attempt_id=attempt.id,
                step_id=step.id,
                attempt_no=1,
                response_payload={"uat_evidence": True},
                is_correct=correct,
                hint_used=False,
                elapsed_seconds=1,
            ))
    db.flush()
    return attempt


def _promotion_evidence_order(db, level_id: int) -> list[ContentItem]:
    """Supply full critical coverage before non-critical evidence.

    The runtime itself already prioritizes configured critical skills. The
    longitudinal UAT uses the same policy intent so it proves that L1/L2 can
    promote once *all* gates are satisfied; raw catalog order must not
    accidentally postpone the last critical skill until item ten and turn this
    into a false legacy-10/10 regression signal.
    """
    core_items = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == level_id,
    ).order_by(ContentItem.order_index, ContentItem.id).all()
    assert len(core_items) == 10

    policy = _load_policy()
    critical_codes = tuple(
        str(code)
        for code in (policy.get("critical_skill_codes_by_level", {}).get(str(level_id), []) or [])
        if str(code).strip()
    )
    assert critical_codes, f"L{level_id} critical promotion policy is not configured"

    skill_code_by_id = {
        skill.id: skill.canonical_skill_id
        for skill in db.query(Skill).filter(Skill.level_id == level_id).all()
    }
    first_core_by_code: dict[str, ContentItem] = {}
    for item in core_items:
        code = skill_code_by_id.get(item.skill_id)
        if code in critical_codes and code not in first_core_by_code:
            first_core_by_code[code] = item

    missing = [code for code in critical_codes if code not in first_core_by_code]
    assert not missing, f"L{level_id} cannot satisfy configured critical coverage: {missing}"

    prioritized = [first_core_by_code[code] for code in critical_codes]
    prioritized_ids = {item.id for item in prioritized}
    return prioritized + [item for item in core_items if item.id not in prioritized_ids]


def _promote_with_strong_core_evidence(db, student: Student, session: AssessmentSession) -> tuple[AssessmentSession, int]:
    level_id = int(session.assigned_level)
    assert level_id in {1, 2}
    existing_ids = {
        row[0]
        for row in db.query(Attempt.item_id).filter(Attempt.session_id == session.id).all()
    }
    core_items = _promotion_evidence_order(db, level_id)

    last_result = None
    for item in core_items:
        if item.id in existing_ids:
            continue
        _complete_learning_item(db, session, item, correct=True)
        db.commit()
        student = db.query(Student).filter(Student.id == student.id).one()
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session.id).one()
        last_result = prepare_next_for_student(db, student, session)
        if last_result.get("level_transitioned"):
            next_session = db.query(AssessmentSession).filter(
                AssessmentSession.id == last_result["session_id"]
            ).one()
            completed = db.query(Attempt.id).join(ContentItem, ContentItem.id == Attempt.item_id).filter(
                Attempt.session_id == session.id,
                Attempt.status == "completed",
                ContentItem.kind == "core_activity",
                ContentItem.level_id == level_id,
            ).count()
            assert 6 <= completed < 10, (
                f"L{level_id} should early-promote after minimum evidence plus full critical coverage; "
                f"got {completed} completed Core items"
            )
            return next_session, completed

    raise AssertionError(f"L{level_id} did not early-promote with approved strong evidence: {last_result}")


def _run_targeted_reinforcement_and_verification(db, student: Student, session: AssessmentSession) -> ReinforcementCycle:
    """Create one real same-level weakness → reinforcement → source verification cycle."""
    assert session.assigned_level == 2
    skill = db.query(Skill).filter(
        Skill.level_id == 2,
        Skill.canonical_skill_id == "shadda_word_reading",
    ).one()
    source_item = db.query(ContentItem).filter(
        ContentItem.kind == "core_activity",
        ContentItem.level_id == 2,
        ContentItem.skill_id == skill.id,
    ).order_by(ContentItem.order_index).first()
    assert source_item is not None
    reinforcement = _canonical_item(db, "L2-REIN-09")
    assert reinforcement.kind == "reinforcement_activity"
    assert reinforcement.level_id == 2
    assert reinforcement.skill_id == skill.id
    assert reinforcement.status == "approved"

    source_attempt = _complete_learning_item(db, session, source_item, correct=False)
    decision = AdaptationDecision(
        student_id=student.id,
        decision_source="automatic",
        action="support",
        mastery_score=40,
        previous_level=2,
        new_level=2,
        weakest_skill_id=skill.id,
        recommended_item_id=reinforcement.id,
        valid_attempt_count=1,
        consecutive_low_count=1,
        snapshot_key=f"m09-full-journey-support:{source_attempt.id}",
        explanation={
            "reason": "activity_below_reinforcement_threshold",
            "source_attempt_id": source_attempt.id,
        },
    )
    db.add(decision)
    db.flush()

    reinforcement_attempt = _complete_learning_item(db, session, reinforcement, correct=True)
    cycle = ensure_cycle(
        db,
        student=student,
        session_id=session.id,
        decision=decision,
        reinforcement_attempt_id=reinforcement_attempt.id,
    )
    assert cycle is not None
    assert cycle.source_attempt_id == source_attempt.id
    assert cycle.reinforcement_item_id == reinforcement.id
    assert cycle.reinforcement_item_id != source_item.id
    assert cycle.status == "reinforcement_in_progress"

    reopened = mark_reinforcement_completed(db, cycle=cycle)
    assert reopened is not None
    assert reopened.id == source_attempt.id
    assert reopened.status == "in_progress"
    assert cycle.status == "verification_pending"

    # Verify every failed source step and preserve the original failed rows.
    for step_id in cycle.source_step_ids:
        existing = db.query(ActivityStepResponse).filter(
            ActivityStepResponse.attempt_id == source_attempt.id,
            ActivityStepResponse.step_id == step_id,
        ).count()
        db.add(ActivityStepResponse(
            attempt_id=source_attempt.id,
            step_id=step_id,
            attempt_no=existing + 1,
            response_payload={
                "reinforcement_cycle_id": cycle.id,
                "reinforcement_verification": True,
                "uat_evidence": True,
            },
            is_correct=True,
            hint_used=False,
            elapsed_seconds=1,
        ))
        db.flush()
        assert finish_verification_step(db, cycle=cycle, step_id=step_id, is_correct=True) in {
            "verification_pending",
            "verified",
        }

    assert cycle.status == "verified"
    source_attempt.status = "completed"
    source_attempt.completed_at = datetime.now(timezone.utc)
    db.commit()
    return cycle


def test_full_single_candidate_journey_keeps_history_and_reaches_exports(client):
    seeded = seed_all.run_seed_all()
    assert seeded["total_items"] == 125
    assert seeded["reinforcement_items"] == 35

    db = TestingSessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        pretest = _persist_assessment_snapshot(
            db,
            student=student,
            session_type="pretest",
            score=45,
            assigned_level=1,
        )
        db.commit()
        assert pretest.assigned_level == 1

        level1 = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(level1)
        db.commit()
        db.refresh(level1)

        level2, l1_core_count = _promote_with_strong_core_evidence(db, student, level1)
        assert level2.assigned_level == 2
        cycle = _run_targeted_reinforcement_and_verification(db, student, level2)

        student = db.query(Student).filter(Student.id == student.id).one()
        level2 = db.query(AssessmentSession).filter(AssessmentSession.id == level2.id).one()
        level3, l2_core_count = _promote_with_strong_core_evidence(db, student, level2)
        assert level3.assigned_level == 3

        # L3 must never unlock posttest on partial evidence.
        l3_items = db.query(ContentItem).filter(
            ContentItem.kind == "core_activity",
            ContentItem.level_id == 3,
        ).order_by(ContentItem.order_index).all()
        assert len(l3_items) == 10
        for item in l3_items[:9]:
            _complete_learning_item(db, level3, item, correct=True)
            db.commit()
            student = db.query(Student).filter(Student.id == student.id).one()
            level3 = db.query(AssessmentSession).filter(AssessmentSession.id == level3.id).one()
            partial = prepare_next_for_student(db, student, level3)
            assert partial.get("journey_completed") is not True

        assert client.post("/auth/login", json={
            "username": "researcher1",
            "password": "test-only-researcher-password",
        }).status_code == 200
        too_early = client.post(
            f"/researcher/students/{student.id}/posttest-access",
            json={"enabled": True},
        )
        assert too_early.status_code == 409

        _complete_learning_item(db, level3, l3_items[9], correct=True)
        db.commit()
        student = db.query(Student).filter(Student.id == student.id).one()
        level3 = db.query(AssessmentSession).filter(AssessmentSession.id == level3.id).one()
        completed_l3 = prepare_next_for_student(db, student, level3)
        assert completed_l3.get("journey_completed") is True

        student = db.query(Student).filter(Student.id == student.id).one()
        journey = build_journey_summary(db, student)
        assert [level["state"] for level in journey["levels"]] == ["completed", "completed", "completed"]
        assert journey["levels"][0]["completed_items"] == l1_core_count
        assert journey["levels"][1]["completed_items"] == l2_core_count
        assert 6 <= l1_core_count < 10
        assert 6 <= l2_core_count < 10
        assert journey["levels"][2]["completed_items"] == 10
        assert journey["learning_journey_completed"] is True
        assert journey["posttest_ready"] is False

        enabled = client.post(
            f"/researcher/students/{student.id}/posttest-access",
            json={"enabled": True},
        )
        assert enabled.status_code == 200, enabled.text
        assert enabled.json()["posttest_enabled"] is True

        # Persist the completed posttest outcome for this same candidate. The
        # assessment engine and audio-review mechanics are covered separately by
        # the exact-SHA E2E gate; reports must consume this stored result only.
        student = db.query(Student).filter(Student.id == student.id).one()
        posttest = _persist_assessment_snapshot(
            db,
            student=student,
            session_type="posttest",
            score=95,
            assigned_level=3,
        )
        student.posttest_enabled = False
        student.posttest_enabled_at = None
        student.posttest_enabled_by = None
        db.commit()
        assert posttest.final_score == 95

        decisions_before_reports = db.query(AdaptationDecision).filter(
            AdaptationDecision.student_id == student.id
        ).count()
        old_history = {
            session.id: db.query(Attempt.id).filter(Attempt.session_id == session.id).count()
            for session in db.query(AssessmentSession).filter(
                AssessmentSession.student_id == student.id,
                AssessmentSession.session_type == "core",
            ).all()
        }
        assert len(old_history) == 3
        assert db.query(ReinforcementCycle).filter(
            ReinforcementCycle.id == cycle.id,
            ReinforcementCycle.status == "verified",
        ).one()

        summary = client.get("/researcher/reports/summary")
        detail = client.get(f"/researcher/reports/students/{student.id}")
        xlsx = client.get("/researcher/reports/exports/cohort.xlsx")
        cohort_pdf = client.get("/researcher/reports/exports/cohort.pdf")
        student_pdf = client.get(f"/researcher/reports/students/{student.id}/export.pdf")
        assert summary.status_code == 200
        assert detail.status_code == 200
        report = detail.json()
        assert report["starting_level"] == 1
        assert report["pretest"]["score"] == 45.0
        assert report["posttest"]["score"] == 95.0
        assert report["improvement"]["absolute_percentage_points"] == 50.0
        assert report["reinforcement"]["verified"] >= 1
        assert xlsx.status_code == 200 and xlsx.content.startswith(b"PK")
        assert cohort_pdf.status_code == 200 and cohort_pdf.content.startswith(b"%PDF-")
        assert student_pdf.status_code == 200 and student_pdf.content.startswith(b"%PDF-")

        db.expire_all()
        decisions_after_reports = db.query(AdaptationDecision).filter(
            AdaptationDecision.student_id == student.id
        ).count()
        assert decisions_after_reports == decisions_before_reports, "Reports must never become mastery evidence"
        assert {
            session.id: db.query(Attempt.id).filter(Attempt.session_id == session.id).count()
            for session in db.query(AssessmentSession).filter(
                AssessmentSession.student_id == student.id,
                AssessmentSession.session_type == "core",
            ).all()
        } == old_history
        assert db.query(AuditLog).filter(
            AuditLog.action == "research_report_export"
        ).count() >= 3
    finally:
        db.close()