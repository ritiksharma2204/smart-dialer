from datetime import datetime, timezone, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.state.call_state import CallState


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(primary_key=True)

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )

    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id"),
        nullable=False,
        index=True,
    )

    borrower_id: Mapped[int] = mapped_column(
        ForeignKey("borrowers.id"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    provider_call_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    status: Mapped[CallState] = mapped_column(
        Enum(CallState),
        default=CallState.QUEUED,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    initiated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_provider_event: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )