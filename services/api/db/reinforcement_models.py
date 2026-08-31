from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from db.models import Base


class ReinforcementCycle(Base):
    """Durable weakness → reinforcement → core verification lifecycle.

    One automatic adaptation decision may own at most one cycle. The source core
    attempt is preserved so reinforcement never silently substitutes for proof
    that the original skill improved.
    """

    __tablename__ = "reinforcement_cycles"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    decision_id = Column(Integer, ForeignKey("adaptation_decisions.id", ondelete="CASCADE"), nullable=False)
    source_attempt_id = Column(Integer, ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False)
    source_step_ids = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    reinforcement_item_id = Column(Integer, ForeignKey("content_items.id"), nullable=False)
    reinforcement_attempt_id = Column(Integer, ForeignKey("attempts.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), nullable=False, default="reinforcement_pending")
    verification_round = Column(Integer, nullable=False, default=0)
    max_verification_rounds = Column(Integer, nullable=False, default=2)
    escalation_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("decision_id", name="uq_reinforcement_cycle_decision"),
        CheckConstraint(
            "status IN ('reinforcement_pending','reinforcement_in_progress','verification_pending','verified','escalated')",
            name="ck_reinforcement_cycles_status",
        ),
        CheckConstraint("verification_round >= 0", name="ck_reinforcement_cycles_verification_round"),
        CheckConstraint(
            "max_verification_rounds BETWEEN 1 AND 5",
            name="ck_reinforcement_cycles_max_verification_rounds",
        ),
    )
