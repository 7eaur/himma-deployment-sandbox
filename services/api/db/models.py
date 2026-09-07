from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    and_,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    """Researcher accounts (password-based login)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), default="researcher", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Student(Base):
    """Student accounts (access-code-based login)."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    access_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)  # Pseudonym only
    grade_level = Column(Integer, default=3, server_default="3", nullable=False)
    current_level = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    posttest_enabled = Column(Boolean, default=False, server_default="false", nullable=False)
    posttest_enabled_at = Column(DateTime(timezone=True), nullable=True)
    posttest_enabled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("grade_level = 3", name="ck_students_grade_level_third"),
        CheckConstraint("current_level BETWEEN 1 AND 3", name="ck_students_current_level"),
    )


class AuditLog(Base):
    """Immutable audit trail for security-sensitive actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_role = Column(String(50), nullable=False)
    actor_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    details = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ContentKind(str, enum.Enum):
    pretest_question = "pretest_question"
    posttest_question = "posttest_question"
    core_activity = "core_activity"
    reinforcement_activity = "reinforcement_activity"


class Skill(Base):
    """Educational skills and levels."""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_key = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String)
    level_id = Column(Integer, nullable=False)
    canonical_skill_id = Column(String(100), nullable=True)


class ContentRelease(Base):
    """Release tracking to prevent changing published content."""
    __tablename__ = "content_releases"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    released_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ContentItem(Base):
    """Unified content model for pre/post tests and activities."""
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    stable_key = Column(String(100), unique=True, index=True, nullable=False)
    kind = Column(String(50), nullable=False)
    level_id = Column(Integer, nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    order_index = Column(Integer, nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(String(50), default="draft", nullable=False)
    checksum = Column(String(64), nullable=False)
    template_data = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    skill = relationship("Skill")
    steps = relationship("ContentStep", back_populates="item", cascade="all, delete", order_by="ContentStep.order_index")
    assets = relationship("ContentAssetLink", back_populates="item", cascade="all, delete")


class ContentStep(Base):
    """Individual rounds within a content item."""
    __tablename__ = "content_steps"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)
    prompt_text = Column(String, nullable=False)
    expected_reading_text = Column(String, nullable=True)

    item = relationship("ContentItem", back_populates="steps")
    # Published responses may point at retired ContentOption rows.  Runtime code
    # intentionally sees active choices only; retired rows stay in the table so
    # old AttemptResponse foreign keys remain valid and reports stay auditable.
    options = relationship(
        "ContentOption",
        primaryjoin=lambda: and_(
            ContentStep.id == ContentOption.step_id,
            ContentOption.is_active.is_(True),
        ),
        back_populates="step",
        cascade="all, delete",
        passive_deletes=True,
        order_by="ContentOption.order_index",
    )
    assets = relationship("ContentAssetLink", back_populates="step", cascade="all, delete")


class ContentOption(Base):
    """Version-safe choices for multiple choice or similar templates."""
    __tablename__ = "content_options"

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("content_steps.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)
    order_index = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)

    step = relationship("ContentStep", back_populates="options")


class ContentAssetLink(Base):
    """Links content items or steps to manifest assets."""
    __tablename__ = "content_asset_links"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=True)
    step_id = Column(Integer, ForeignKey("content_steps.id", ondelete="CASCADE"), nullable=True)
    manifest_asset_id = Column(String(200), nullable=False)
    asset_type = Column(String(50), nullable=False)
    usage_context = Column(String(50), nullable=True)

    item = relationship("ContentItem", back_populates="assets")
    step = relationship("ContentStep", back_populates="assets")


class ScoringPolicy(Base):
    """Academic scoring policies ensuring immutability when locked."""
    __tablename__ = "scoring_policies"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False)
    status = Column(String(50), default="draft", nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    checksum = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ScoringRule(Base):
    """Specific scoring rules and rubrics tied to a policy and an item."""
    __tablename__ = "scoring_rules"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("scoring_policies.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    max_raw_score = Column(Numeric(precision=10, scale=2), nullable=False, default=1.0)
    rubric = Column(String, nullable=True)

    policy = relationship("ScoringPolicy")
    item = relationship("ContentItem")


class AssessmentSession(Base):
    """A durable assessment/learning session for one student."""
    __tablename__ = "assessment_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="in_progress")
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    final_score = Column(Numeric(precision=10, scale=4), nullable=True)
    assigned_level = Column(Integer, nullable=True)
    elapsed_seconds = Column(Integer, default=0, server_default="0", nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    assessment_attempt_no = Column(Integer, default=1, server_default="1", nullable=False)
    supersedes_session_id = Column(Integer, ForeignKey("assessment_sessions.id", ondelete="SET NULL"), nullable=True)
    official_for_reporting = Column(Boolean, default=False, server_default="false", nullable=False)

    __table_args__ = (
        CheckConstraint("session_type IN ('pretest', 'posttest', 'core')", name="ck_assessment_sessions_type"),
        CheckConstraint("status IN ('in_progress', 'completed')", name="ck_assessment_sessions_status"),
        CheckConstraint("elapsed_seconds >= 0", name="ck_assessment_sessions_elapsed"),
        CheckConstraint("assessment_attempt_no >= 1", name="ck_assessment_sessions_attempt_no"),
        Index(
            "uq_assessment_sessions_active_student",
            "student_id",
            unique=True,
            postgresql_where=text("status = 'in_progress'"),
            sqlite_where=text("status = 'in_progress'"),
        ),
        Index(
            "uq_assessment_sessions_prepost_attempt_no",
            "student_id",
            "session_type",
            "assessment_attempt_no",
            unique=True,
            postgresql_where=text("session_type IN ('pretest', 'posttest')"),
            sqlite_where=text("session_type IN ('pretest', 'posttest')"),
        ),
    )


class AssessmentRetakeAuthorization(Base):
    """Supervisor authorization for one additional pre/post assessment attempt."""
    __tablename__ = "assessment_retake_authorizations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    session_type = Column(String(50), nullable=False)
    previous_session_id = Column(Integer, ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False)
    authorized_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String(20), default="pending", server_default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    new_session_id = Column(Integer, ForeignKey("assessment_sessions.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        CheckConstraint("session_type IN ('pretest','posttest')", name="ck_assessment_retake_type"),
        CheckConstraint("status IN ('pending','consumed','revoked')", name="ck_assessment_retake_status"),
        Index(
            "uq_assessment_retake_pending",
            "student_id",
            "session_type",
            unique=True,
            postgresql_where=text("status = 'pending'"),
            sqlite_where=text("status = 'pending'"),
        ),
    )


class Attempt(Base):
    """An attempt of a ContentItem within a session."""
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    status = Column(String(50), nullable=False, default="in_progress")
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    elapsed_seconds = Column(Integer, default=0, server_default="0", nullable=False)

    __table_args__ = (
        UniqueConstraint("session_id", "item_id", name="uq_attempts_session_item"),
        CheckConstraint("status IN ('in_progress', 'completed')", name="ck_attempts_status"),
        CheckConstraint("elapsed_seconds >= 0", name="ck_attempts_elapsed"),
    )


class AttemptResponse(Base):
    """An answer given to a ContentStep."""
    __tablename__ = "attempt_responses"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("content_steps.id"), nullable=False)
    selected_option_id = Column(Integer, ForeignKey("content_options.id"), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    elapsed_seconds = Column(Integer, default=0, server_default="0", nullable=False)

    __table_args__ = (
        UniqueConstraint("attempt_id", "step_id", name="uq_attempt_responses_attempt_step"),
        CheckConstraint("elapsed_seconds >= 0", name="ck_attempt_responses_elapsed"),
    )


class OperationIdempotency(Base):
    """Durable replay protection for student write operations."""
    __tablename__ = "operation_idempotency"

    id = Column(Integer, primary_key=True, index=True)
    actor_role = Column(String(50), nullable=False)
    actor_id = Column(Integer, nullable=False)
    operation = Column(String(100), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    status_code = Column(Integer, nullable=False, default=200, server_default="200")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("actor_role", "actor_id", "operation", "idempotency_key", name="uq_operation_idempotency_scope_key"),
    )


class AudioSubmission(Base):
    """Audio recordings submitted for AttemptResponses."""
    __tablename__ = "audio_submissions"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("attempt_responses.id"), nullable=False)
    storage_key = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    duration_seconds = Column(Numeric(precision=10, scale=2), nullable=True)
    status = Column(String(50), nullable=False, default="uploaded")
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AudioReview(Base):
    """Manual grading of an audio submission."""
    __tablename__ = "audio_reviews"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("audio_submissions.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_units = Column(Integer, nullable=False)
    deletions = Column(Integer, default=0, nullable=False)
    substitutions = Column(Integer, default=0, nullable=False)
    insertions = Column(Integer, default=0, nullable=False)
    rubric_score = Column(Numeric(precision=10, scale=4), nullable=False)
    supersedes_review_id = Column(Integer, ForeignKey("audio_reviews.id"), nullable=True)
    pronunciation_notes = Column(String, nullable=True)
    fluency_notes = Column(String, nullable=True)
    time_notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
