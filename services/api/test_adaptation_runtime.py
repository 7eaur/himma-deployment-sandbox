"""Integration-level P06 tests for recommendation and reward persistence."""

from adaptation import ensure_rewards
from adaptation_runtime import prepare_next_for_student
from db.activity_models import ActivityStepResponse
from db.database import SessionLocal
from db.models import (
    AssessmentSession,
    Attempt,
    AttemptResponse,
    AudioSubmission,
    ContentItem,
    ContentStep,
    Skill,
    Student,
)


def _item(db, *, stable_key: str, kind: str, skill_id: int, order_index: int):
    item = ContentItem(
        stable_key=stable_key,
        kind=kind,
        level_id=1,
        skill_id=skill_id,
        interaction_type="choose_one",
        order_index=order_index,
        version="test",
        status="approved",
        checksum=(stable_key * 64)[:64],
        template_data={"canonical_id": stable_key, "canonical_interaction_type": "choose_one"},
    )
    db.add(item)
    db.flush()
    step = ContentStep(item_id=item.id, order_index=1, prompt_text="اختبار")
    db.add(step)
    db.flush()
    return item, step


def test_low_mastery_prepares_exact_skill_reinforcement_once_and_rewards_once():
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        skill = Skill(skill_key="adaptive-skill-1", name="تمييز الحروف بصريًا", level_id=1)
        db.add(skill)
        db.flush()

        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()

        for index in range(1, 4):
            item, step = _item(
                db,
                stable_key=f"CORE-{index}",
                kind="core_activity",
                skill_id=skill.id,
                order_index=index,
            )
            attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
            db.add(attempt)
            db.flush()
            db.add(ActivityStepResponse(
                attempt_id=attempt.id,
                step_id=step.id,
                attempt_no=1,
                response_payload={"selected_option_ids": [999]},
                is_correct=False,
                hint_used=False,
                elapsed_seconds=3,
            ))

        reinforcement, _ = _item(
            db,
            stable_key="REIN-1",
            kind="reinforcement_activity",
            skill_id=skill.id,
            order_index=1,
        )
        db.commit()

        first = prepare_next_for_student(db, student, session)
        assert first["decision"]["action"] == "support"
        assert first["decision"]["mastery_score"] == 0.0
        assert first["decision"]["recommended_item_id"] == reinforcement.id
        assert first["recommended_attempt_id"] is not None

        second = prepare_next_for_student(db, student, session)
        assert second["decision"]["decision_id"] == first["decision"]["decision_id"]
        assert second["recommended_attempt_id"] == first["recommended_attempt_id"]
        assert db.query(Attempt).filter(
            Attempt.session_id == session.id,
            Attempt.item_id == reinforcement.id,
        ).count() == 1

        first_rewards = ensure_rewards(db, student.id)
        second_rewards = ensure_rewards(db, student.id)
        stars = [reward for reward in first_rewards if reward.reward_type == "stars"]
        assert len(stars) == 3
        assert all(reward.stars == 3 for reward in stars)
        assert len(second_rewards) == len(first_rewards)
    finally:
        db.close()


def test_declared_media_gap_is_neutral_not_a_false_failure():
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        skill = Skill(skill_key="adaptive-gap-skill", name="مهارة فجوة الوسائط", level_id=1)
        db.add(skill)
        db.flush()
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()

        item, step = _item(
            db,
            stable_key="CORE-GAP",
            kind="core_activity",
            skill_id=skill.id,
            order_index=1,
        )
        attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
        db.add(attempt)
        db.flush()
        db.add(ActivityStepResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            attempt_no=1,
            response_payload={"declared_media_gap_skip": True},
            is_correct=True,
            hint_used=False,
            elapsed_seconds=0,
        ))
        db.commit()

        # A gap-only attempt contains no scorable evidence, so it must not count
        # as one of the three valid adaptation attempts or earn a fixed reward.
        result = prepare_next_for_student(db, student, session)
        assert result["decision"]["ready"] is False
        assert result["decision"]["valid_attempt_count"] == 0
        assert ensure_rewards(db, student.id) == []
    finally:
        db.close()


def test_unresolved_audio_completion_is_neutral_until_reviewed():
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.access_code == "STU001").one()
        student.current_level = 1
        skill = Skill(skill_key="adaptive-audio-skill", name="قراءة صوتية", level_id=1)
        db.add(skill)
        db.flush()
        session = AssessmentSession(
            student_id=student.id,
            session_type="core",
            status="in_progress",
            assigned_level=1,
        )
        db.add(session)
        db.flush()

        item, step = _item(
            db,
            stable_key="CORE-AUDIO",
            kind="core_activity",
            skill_id=skill.id,
            order_index=1,
        )
        item.interaction_type = "read_aloud"
        item.template_data = {"canonical_id": "CORE-AUDIO", "canonical_interaction_type": "read_aloud"}
        attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
        db.add(attempt)
        db.flush()
        response = AttemptResponse(
            attempt_id=attempt.id,
            step_id=step.id,
            selected_option_id=None,
            is_correct=None,
            elapsed_seconds=2,
        )
        db.add(response)
        db.flush()
        db.add(AudioSubmission(
            response_id=response.id,
            storage_key="test/unresolved.webm",
            file_size=100,
            mime_type="audio/webm",
            duration_seconds=2,
            status="uploaded",
        ))
        db.commit()

        assert ensure_rewards(db, student.id) == []
        result = prepare_next_for_student(db, student, session)
        assert result["decision"]["ready"] is False
        assert result["decision"]["valid_attempt_count"] == 0
    finally:
        db.close()
