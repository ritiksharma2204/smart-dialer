from sqlalchemy.orm import Session

from app.repositories.agent_repository import reserve_agent


def reserve_agent_for_call(
    db: Session,
    agent_id: int,
):
    agent = reserve_agent(db, agent_id)

    if agent is None:
        return None

    return agent