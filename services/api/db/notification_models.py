from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from db.models import Base


class ResearcherNotification(Base):
    """Durable supervisor-facing notification read model.

    Domain state remains authoritative; notifications are a deduplicated attention
    queue with persistent read/unread state and a direct UI destination.
    """

    __tablename__ = "researcher_notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(64), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)
    href = Column(String(500), nullable=False)
    entity_type = Column(String(80), nullable=True)
    entity_id = Column(String(100), nullable=True)
    dedupe_key = Column(String(180), nullable=False)
    is_read = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_researcher_notifications_dedupe_key"),
    )
