from sqlalchemy.orm import Session

from app.models.call import Call
from app.state.call_state import CallState
from app.repositories.agent_repository import reserve_agent
from app.repositories.borrower_repository import reserve_borrower


def allocate_call(
    db: Session,
    agent_id: int,
    borrower_id: int,
    campaign_id: int,
    provider: str,
) -> Call | None:
    """
    Atomically reserve an agent, reserve a borrower,
    and create a call.

    The caller controls the transaction.
    """

    agent = reserve_agent(db, agent_id)

    if agent is None:
        return None

    borrower = reserve_borrower(db, borrower_id)

    if borrower is None:
        return None

    call = Call(
        campaign_id=campaign_id,
        agent_id=agent.id,
        borrower_id=borrower.id,
        provider=provider,
        status=CallState.RESERVED,
    )

    db.add(call)
    db.flush()

    return call