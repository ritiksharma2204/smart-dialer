from app.models.agent import Agent
from app.services.agent_service import reserve_agent_for_call
from app.state.agent_state import AgentState


def test_available_agent_can_be_reserved(db):
    agent = Agent(
        name="Agent 1",
        status=AgentState.AVAILABLE,
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    reserved = reserve_agent_for_call(
        db,
        agent.id,
    )

    db.commit()

    assert reserved is not None
    assert reserved.status == AgentState.RESERVED

def test_unavailable_agent_cannot_be_reserved(db):
    agent = Agent(
        name="Agent 2",
        status=AgentState.RESERVED,
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    result = reserve_agent_for_call(
        db,
        agent.id,
    )

    assert result is None

from concurrent.futures import ThreadPoolExecutor

from app.database import SessionLocal


def attempt_reservation(agent_id: int):
    db = SessionLocal()

    try:
        agent = reserve_agent_for_call(
            db,
            agent_id,
        )

        if agent is None:
            db.rollback()
            return False

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def test_concurrent_workers_only_one_can_reserve_agent(db):
    agent = Agent(
        name="Concurrent Agent",
        status=AgentState.AVAILABLE,
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    agent_id = agent.id

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(
            executor.map(
                attempt_reservation,
                [agent_id] * 5,
            )
        )

    assert sum(results) == 1