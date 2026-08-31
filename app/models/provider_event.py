from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProviderEvent(Base):
    __tablename__ = "provider_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    provider_event_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    call_id: Mapped[int] = mapped_column(
        ForeignKey("calls.id"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_event_id",
            name="uq_provider_event",
        ),
    )