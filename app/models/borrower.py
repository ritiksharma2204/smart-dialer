from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BorrowerStatus(str, Enum):
    READY = "READY"
    RESERVED = "RESERVED"
    IN_CALL = "IN_CALL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Borrower(Base):
    __tablename__ = "borrowers"

    id: Mapped[int] = mapped_column(primary_key=True)

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    phone_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    status: Mapped[BorrowerStatus] = mapped_column(
        SQLEnum(BorrowerStatus),
        default=BorrowerStatus.READY,
        nullable=False,
    )

    attempt_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    last_called_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )