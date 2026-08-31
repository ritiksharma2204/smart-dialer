from datetime import datetime, timezone, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.state.agent_state import AgentState


def reserve_agent(
    db: Session,
    agent_id: int,
) -> Agent | None:
    """
    Atomically reserve an available agent.

    Returns the reserved agent if successful.
    Returns None if the agent is unavailable.
    """

    now = datetime.now(timezone.utc)

    result = db.execute(
        update(Agent)
        .where(
            Agent.id == agent_id,
            Agent.status == AgentState.AVAILABLE,
        )
        .values(
            status=AgentState.RESERVED,
            reserved_at=now,
            last_state_change=now,
            version=Agent.version + 1,
        )
    )

    if result.rowcount != 1:
        return None

    return db.get(Agent, agent_id)

def release_agent(
    db: Session,
    agent_id: int,
) -> None:
    db.execute(
        update(Agent)
        .where(
            Agent.id == agent_id,
            Agent.status == AgentState.RESERVED,
        )
        .values(
            status=AgentState.AVAILABLE,
        )
    )