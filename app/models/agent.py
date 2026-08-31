from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.state.agent_state import AgentState


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[AgentState] = mapped_column(
        Enum(AgentState),
        default=AgentState.OFFLINE,
        nullable=False,
    )

    reserved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_state_change: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
    )