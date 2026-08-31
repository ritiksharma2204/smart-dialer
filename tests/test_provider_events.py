from datetime import datetime, timezone, timedelta

from app.models.agent import Agent
from app.models.borrower import Borrower, BorrowerStatus
from app.models.call import Call
from app.models.campaign import Campaign
from app.services.provider_event_processor import process_provider_event
from app.state.agent_state import AgentState
from app.state.call_state import CallState


def create_test_call(db):
    campaign = Campaign(name="Event Campaign")

    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Event Agent",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Event Borrower",
        phone_number="+919999999999",
        status=BorrowerStatus.RESERVED,
    )

    db.add_all([agent, borrower])
    db.flush()

    call = Call(
        campaign_id=campaign.id,
        agent_id=agent.id,
        borrower_id=borrower.id,
        provider="provider_a",
        status=CallState.RESERVED,
    )

    db.add(call)
    db.commit()
    db.refresh(call)

    return call


def test_answered_event_updates_call(db):
    call = create_test_call(db)

    timestamp = datetime.now(timezone.utc)

    result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="event-1",
        call_id=call.id,
        event_type="ANSWERED",
        event_timestamp=timestamp,
        payload={},
    )

    db.commit()
    db.refresh(call)

    assert result is True
    assert call.status == CallState.ANSWERED
    assert call.last_provider_event == "ANSWERED"


def test_duplicate_event_is_ignored(db):
    call = create_test_call(db)

    timestamp = datetime.now(timezone.utc)

    process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="event-duplicate",
        call_id=call.id,
        event_type="ANSWERED",
        event_timestamp=timestamp,
        payload={},
    )

    db.commit()

    result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="event-duplicate",
        call_id=call.id,
        event_type="ANSWERED",
        event_timestamp=timestamp,
        payload={},
    )

    assert result is False

def test_out_of_order_completed_then_answered_stays_completed(db):
    call = create_test_call(db)

    now = datetime.now(timezone.utc)

    completed_result = process_provider_event(
        db,
        provider="provider_b",
        provider_event_id="event-completed",
        call_id=call.id,
        event_type="COMPLETED",
        event_timestamp=now,
        payload={},
    )

    db.commit()
    db.refresh(call)

    assert completed_result is True
    assert call.status == CallState.COMPLETED

    answered_result = process_provider_event(
        db,
        provider="provider_b",
        provider_event_id="event-answered-late",
        call_id=call.id,
        event_type="ANSWERED",
        event_timestamp=now - timedelta(seconds=5),
        payload={},
    )

    db.commit()
    db.refresh(call)

    assert answered_result is False
    assert call.status == CallState.COMPLETED

def test_unknown_provider_event_does_not_change_call_state(db):
    call = create_test_call(db)

    result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="unknown-event-1",
        call_id=call.id,
        event_type="SOMETHING_UNKNOWN",
        event_timestamp=datetime.now(timezone.utc),
        payload={"unexpected": True},
    )

    db.commit()
    db.refresh(call)

    assert result is False
    assert call.status == CallState.RESERVED