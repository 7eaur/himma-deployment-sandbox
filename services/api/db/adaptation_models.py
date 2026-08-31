from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from db.models import Base


class AdaptationDecision(Base):
    """Immutable, explainable level decision history for P06."""

    __tablename__ = "adaptation_decisions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    decision_source = Column(String(20), nullable=False)  # automatic | manual
    action = Column(String(20), nullable=False)  # promote | stay | support | demote | hold | override
    mastery_score = Column(Numeric(10, 4), nullable=True)
    previous_level = Column(Integer, nullable=False)
    new_level = Column(Integer, nullable=False)
    weakest_skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    recommended_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=True)
    valid_attempt_count = Column(Integer, nullable=False, default=0)
    consecutive_low_count = Column(Integer, nullable=False, default=0)
    snapshot_key = Column(String(200), nullable=True)
    explanation = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    manual_reason = Column(String, nullable=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "decision_source",
            "snapshot_key",
            name="uq_adaptation_decision_student_source_snapshot",
        ),
    )


class RewardEvent(Base):
    """Idempotent reward event tied to a real completed activity or milestone."""

    __tablename__ = "reward_events"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id", ondelete="CASCADE"), nullable=True)
    reward_type = Column(String(20), nullable=False)  # stars | badge
    reward_key = Column(String(120), nullable=False)
    stars = Column(Integer, nullable=True)
    label = Column(String(200), nullable=False)
    details = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "reward_key", name="uq_reward_event_student_key"),
    )
