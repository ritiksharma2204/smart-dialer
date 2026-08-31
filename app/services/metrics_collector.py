from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.call import Call
from app.models.agent import Agent
from app.state.agent_state import AgentState
from app.services.metrics import DialerMetrics
from app.state.call_state import CallState


def collect_metrics(
    db: Session,
    campaign_id: int | None = None,
) -> DialerMetrics:
    query = select(
        func.count(Call.id),
        func.count().filter(Call.status == CallState.QUEUED),
        func.count().filter(Call.status == CallState.RESERVED),
        func.count().filter(Call.status == CallState.INITIATED),
        func.count().filter(Call.status == CallState.RINGING),
        func.count().filter(Call.status == CallState.ANSWERED),
        func.count().filter(Call.status == CallState.CONNECTED),
        func.count().filter(Call.status == CallState.COMPLETED),
        func.count().filter(Call.status == CallState.FAILED),
        func.count().filter(Call.status == CallState.CANCELLED),
    )

    if campaign_id is not None:
        query = query.where(Call.campaign_id == campaign_id)

    result = db.execute(query).one()

    (
        total_calls,
        queued_calls,
        reserved_calls,
        initiated_calls,
        ringing_calls,
        answered_calls,
        connected_calls,
        completed_calls,
        failed_calls,
        cancelled_calls,
    ) = result

    return DialerMetrics(
        total_calls=total_calls,
        queued_calls=queued_calls,
        reserved_calls=reserved_calls,
        initiated_calls=initiated_calls,
        ringing_calls=ringing_calls,
        answered_calls=answered_calls,
        connected_calls=connected_calls,
        completed_calls=completed_calls,
        failed_calls=failed_calls,
        cancelled_calls=cancelled_calls,
    )

def count_available_agents(db: Session) -> int:
    return db.scalar(
        select(func.count(Agent.id)).where(
            Agent.status == AgentState.AVAILABLE
        )
    ) or 0
