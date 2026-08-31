from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.borrower import Borrower, BorrowerStatus
from app.models.call import Call
from app.models.provider_event import ProviderEvent
from app.state.agent_state import AgentState
from app.state.call_state import CallState


# Events that are allowed to move a call forward.
EVENT_STATE_MAP = {
    "INITIATED": CallState.INITIATED,
    "RINGING": CallState.RINGING,
    "ANSWERED": CallState.ANSWERED,
    "CONNECTED": CallState.CONNECTED,
    "COMPLETED": CallState.COMPLETED,
    "FAILED": CallState.FAILED,
    "CANCELLED": CallState.CANCELLED,
}


# Higher number = further along in the normal lifecycle.
STATE_ORDER = {
    CallState.QUEUED: 0,
    CallState.RESERVED: 1,
    CallState.INITIATED: 2,
    CallState.RINGING: 3,
    CallState.ANSWERED: 4,
    CallState.CONNECTED: 5,
    CallState.COMPLETED: 6,
    CallState.FAILED: 6,
    CallState.CANCELLED: 6,
}


def process_provider_event(
    db: Session,
    *,
    provider: str,
    provider_event_id: str,
    call_id: int,
    event_type: str,
    event_timestamp: datetime,
    payload: dict,
) -> bool:
    """
    Process one provider event.

    Returns:
        True  -> event caused a state update
        False -> duplicate, stale, or invalid event
    """

    # Lock the call so two workers cannot update it simultaneously.
    call = db.execute(
        select(Call)
        .where(Call.id == call_id)
        .with_for_update()
    ).scalar_one_or_none()

    if call is None:
        raise ValueError(f"Call {call_id} does not exist")

    # Check whether this exact provider event was already processed.
    existing_event = db.execute(
        select(ProviderEvent)
        .where(
            ProviderEvent.provider == provider,
            ProviderEvent.provider_event_id == provider_event_id,
        )
    ).scalar_one_or_none()

    if existing_event is not None:
        return False

    # Store the event first.
    event = ProviderEvent(
        provider=provider,
        provider_event_id=provider_event_id,
        call_id=call_id,
        event_type=event_type,
        event_timestamp=event_timestamp,
        payload=payload,
        processed=False,
    )

    db.add(event)

    # Unknown events are stored but don't change call state.
    target_state = EVENT_STATE_MAP.get(event_type)

    if target_state is None:
        event.processed = True
        return False

    current_order = STATE_ORDER[call.status]
    target_order = STATE_ORDER[target_state]

    # Ignore events that try to move the call backwards.
    if target_order < current_order:
        event.processed = True
        return False

    # Terminal states cannot be changed by later events.
    if call.status in {
        CallState.COMPLETED,
        CallState.FAILED,
        CallState.CANCELLED,
    }:
        event.processed = True
        return False

    # Apply the state transition.
    call.status = target_state
    call.last_provider_event = event_type

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if target_state == CallState.INITIATED:
        call.initiated_at = event_timestamp

    elif target_state == CallState.ANSWERED:
        call.answered_at = event_timestamp

    elif target_state == CallState.COMPLETED:
        call.completed_at = event_timestamp

        # Release agent and finalize borrower when the call ends.
    if target_state in{
        CallState.COMPLETED,
        CallState.FAILED,
        CallState.CANCELLED,
    }:
        agent = db.get(Agent, call.agent_id)
        borrower = db.get(Borrower, call.borrower_id)

        if agent is not None:
            agent.status = AgentState.AVAILABLE

        if borrower is not None:
            if target_state == CallState.COMPLETED:
                borrower.status = BorrowerStatus.COMPLETED
            elif target_state == CallState.FAILED:
                borrower.status = BorrowerStatus.FAILED
            elif target_state == CallState.CANCELLED:
                borrower.status = BorrowerStatus.READY

    call.updated_at = now

    event.processed = True

    return True