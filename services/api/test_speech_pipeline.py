from datetime import datetime, timezone

from conftest import TestingSessionLocal
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
from db.speech_models import SpeechAnalysis, SpeechAnalysisJob
from speech_pipeline import enqueue_submission, process_job
from speech_provider import ProviderResult, ProviderTemporaryError, ProviderWord, UnconfiguredSpeechProvider


class FakeProvider:
    name = "fixture-asr"

    def __init__(self, transcript="ذهب سالم الى المدرسة", confidence=0.95):
        self.transcript = transcript
        self.confidence = confidence

    def transcribe_reference_guided(self, **kwargs):
        return ProviderResult(
            provider_name=self.name,
            model="fixture-v1",
            transcript=self.transcript,
            confidence=self.confidence,
            request_id="fixture-request",
            duration_seconds=2.4,
            words=tuple(ProviderWord(text=word, confidence=0.9) for word in self.transcript.split()),
            raw_metadata={"fixture": True},
        )


class TemporaryFailureProvider:
    name = "fixture-temporary"

    def transcribe_reference_guided(self, **kwargs):
        raise ProviderTemporaryError("temporary outage")


def _submission(db):
    student = db.query(Student).filter(Student.access_code == "STU001").one()
    skill = Skill(skill_key="speech-test-skill", name="قراءة", level_id=3)
    db.add(skill)
    db.flush()
    item = ContentItem(
        stable_key="SPEECH-TEST-ITEM",
        kind="pretest_question",
        level_id=3,
        skill_id=skill.id,
        interaction_type="audio_record",
        order_index=1,
        version="test",
        status="approved",
        checksum="a" * 64,
    )
    db.add(item)
    db.flush()
    step = ContentStep(
        item_id=item.id,
        order_index=1,
        prompt_text="اقرأ الجملة",
        expected_reading_text="ذَهَبَ سَالِمٌ إِلَى الْمَدْرَسَةِ",
    )
    db.add(step)
    session = AssessmentSession(student_id=student.id, session_type="pretest", status="in_progress")
    db.add(session)
    db.flush()
    attempt = Attempt(session_id=session.id, item_id=item.id, status="completed")
    db.add(attempt)
    db.flush()
    response = AttemptResponse(attempt_id=attempt.id, step_id=step.id, is_correct=None)
    db.add(response)
    db.flush()
    audio = AudioSubmission(
        response_id=response.id,
        storage_key=f"audio/{student.id}/fixture.webm",
        file_size=4000,
        mime_type="audio/webm",
        duration_seconds=2.4,
        status="uploaded",
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


def test_enqueue_is_idempotent():
    db = TestingSessionLocal()
    try:
        audio = _submission(db)
        first = enqueue_submission(db, audio.id)
        db.flush()
        second = enqueue_submission(db, audio.id)
        assert first.id == second.id
    finally:
        db.close()


def test_provider_absence_blocks_without_fake_analysis(monkeypatch):
    db = TestingSessionLocal()
    try:
        audio = _submission(db)
        job = enqueue_submission(db, audio.id)
        db.commit()
        monkeypatch.setattr("speech_pipeline._audio_bytes", lambda submission: b"real-audio-placeholder")
        process_job(db, job.id, provider=UnconfiguredSpeechProvider())
        db.commit()
        db.refresh(job)
        assert job.status == "blocked_provider"
        assert job.attempt_count == 0
        assert db.query(SpeechAnalysis).filter(SpeechAnalysis.job_id == job.id).count() == 0
    finally:
        db.close()


def test_valid_provider_result_stays_human_review_until_calibrated(monkeypatch):
    monkeypatch.delenv("HIMMA_ASR_CONFIDENCE_THRESHOLD", raising=False)
    monkeypatch.delenv("HIMMA_ASR_CALIBRATION_VERSION", raising=False)
    monkeypatch.setattr("speech_pipeline._audio_bytes", lambda submission: b"real-audio-placeholder")
    db = TestingSessionLocal()
    try:
        audio = _submission(db)
        job = enqueue_submission(db, audio.id)
        db.commit()
        process_job(db, job.id, provider=FakeProvider())
        db.commit()
        analysis = db.query(SpeechAnalysis).filter(SpeechAnalysis.job_id == job.id).one()
        assert job.status == "review_required"
        assert analysis.decision == "review_required"
        assert analysis.correct_count == 4
        assert analysis.deletion_count == 0
        assert analysis.insertion_count == 0
        assert analysis.substitution_count == 0
    finally:
        db.close()


def test_calibrated_threshold_can_auto_accept_high_confidence(monkeypatch):
    monkeypatch.setenv("HIMMA_ASR_CONFIDENCE_THRESHOLD", "0.90")
    monkeypatch.setenv("HIMMA_ASR_CALIBRATION_VERSION", "pilot-001")
    monkeypatch.setattr("speech_pipeline._audio_bytes", lambda submission: b"real-audio-placeholder")
    db = TestingSessionLocal()
    try:
        audio = _submission(db)
        job = enqueue_submission(db, audio.id)
        db.commit()
        process_job(db, job.id, provider=FakeProvider(confidence=0.95))
        db.commit()
        analysis = db.query(SpeechAnalysis).filter(SpeechAnalysis.job_id == job.id).one()
        assert job.status == "completed"
        assert analysis.decision == "auto_accepted"
        assert analysis.calibration_version == "pilot-001"
    finally:
        db.close()


def test_temporary_failures_retry_then_dead_letter(monkeypatch):
    monkeypatch.setattr("speech_pipeline._audio_bytes", lambda submission: b"real-audio-placeholder")
    db = TestingSessionLocal()
    try:
        audio = _submission(db)
        job = enqueue_submission(db, audio.id)
        job.max_attempts = 2
        db.commit()
        now = datetime.now(timezone.utc)
        process_job(db, job.id, provider=TemporaryFailureProvider(), now=now)
        db.commit()
        assert job.status == "retry_wait"
        assert job.attempt_count == 1
        process_job(db, job.id, provider=TemporaryFailureProvider(), now=job.next_attempt_at)
        db.commit()
        assert job.status == "dead_letter"
        assert job.attempt_count == 2
    finally:
        db.close()
