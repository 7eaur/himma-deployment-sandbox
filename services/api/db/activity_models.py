from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from db.models import Base


class ActivityStepResponse(Base):
    """Structured response for activity interactions that cannot fit one option id.

    Assessment choice/audio responses keep using AttemptResponse. This additive table
    is intentionally scoped to learning activities so B02 assessment behavior remains
    backward compatible while sequence, memory, build-word and multi-select answers
    are stored without flattening the approved interaction.
    """

    __tablename__ = "activity_step_responses"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(Integer, ForeignKey("content_steps.id", ondelete="CASCADE"), nullable=False)
    attempt_no = Column(Integer, nullable=False, default=1)
    response_payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    hint_used = Column(Boolean, nullable=False, default=False)
    elapsed_seconds = Column(Integer, nullable=False, default=0)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "step_id",
            "attempt_no",
            name="uq_activity_step_response_attempt_step_no",
        ),
    )
