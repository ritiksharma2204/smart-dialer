from datetime import datetime, timezone

from app.models.agent import Agent
from app.models.borrower import Borrower, BorrowerStatus
from app.models.call import Call
from app.models.campaign import Campaign
from app.services.provider_event_processor import process_provider_event
from app.state.agent_state import AgentState
from app.state.call_state import CallState


def create_test_call(db):
    campaign = Campaign(name="Lifecycle Campaign")

    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Lifecycle Agent",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Lifecycle Borrower",
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
        status=CallState.INITIATED,
    )

    db.add(call)
    db.commit()
    db.refresh(call)

    return call, agent, borrower


def test_completed_call_releases_agent_and_completes_borrower(db):
    call, agent, borrower = create_test_call(db)

    result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="lifecycle-completed-1",
        call_id=call.id,
        event_type="COMPLETED",
        event_timestamp=datetime.now(timezone.utc),
        payload={},
    )

    db.commit()
    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert result is True
    assert call.status == CallState.COMPLETED

    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.COMPLETED


def test_failed_call_releases_agent(db):
    call, agent, borrower = create_test_call(db)

    result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="lifecycle-failed-1",
        call_id=call.id,
        event_type="FAILED",
        event_timestamp=datetime.now(timezone.utc),
        payload={},
    )

    db.commit()
    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert result is True
    assert call.status == CallState.FAILED

    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.FAILED

def test_late_failed_event_does_not_change_completed_call(db):
    call, agent, borrower = create_test_call(db)

    completed_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="lifecycle-terminal-completed",
        call_id=call.id,
        event_type="COMPLETED",
        event_timestamp=datetime.now(timezone.utc),
        payload={},
    )

    db.commit()
    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert completed_result is True
    assert call.status == CallState.COMPLETED
    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.COMPLETED

    failed_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="lifecycle-late-failed",
        call_id=call.id,
        event_type="FAILED",
        event_timestamp=datetime.now(timezone.utc),
        payload={},
    )

    db.commit()
    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert failed_result is False

    # Terminal call must remain completed.
    assert call.status == CallState.COMPLETED

    # Resources must remain in their completed-call state.
    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.COMPLETED

def test_duplicate_failed_event_is_ignored(db):
    call, agent, borrower = create_test_call(db)

    timestamp = datetime.now(timezone.utc)

    first_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="duplicate-failed-1",
        call_id=call.id,
        event_type="FAILED",
        event_timestamp=timestamp,
        payload={},
    )

    db.commit()

    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert first_result is True
    assert call.status == CallState.FAILED
    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.FAILED

    second_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="duplicate-failed-1",
        call_id=call.id,
        event_type="FAILED",
        event_timestamp=timestamp,
        payload={},
    )

    db.commit()

    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert second_result is False
    assert call.status == CallState.FAILED
    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.FAILED

def test_out_of_order_failed_after_completed_stays_completed(db):
    call, agent, borrower = create_test_call(db)

    timestamp = datetime.now(timezone.utc)

    completed_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="completed-before-failed",
        call_id=call.id,
        event_type="COMPLETED",
        event_timestamp=timestamp,
        payload={},
    )

    db.commit()

    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert completed_result is True
    assert call.status == CallState.COMPLETED
    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.COMPLETED

    failed_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="failed-after-completed",
        call_id=call.id,
        event_type="FAILED",
        event_timestamp=timestamp,
        payload={},
    )

    db.commit()

    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert failed_result is False
    assert call.status == CallState.COMPLETED
    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.COMPLETED

def test_cancelled_call_releases_agent_and_resets_borrower(db):
    call, agent, borrower = create_test_call(db)

    result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="lifecycle-cancelled-1",
        call_id=call.id,
        event_type="CANCELLED",
        event_timestamp=datetime.now(timezone.utc),
        payload={},
    )

    db.commit()

    db.refresh(call)
    db.refresh(agent)
    db.refresh(borrower)

    assert result is True
    assert call.status == CallState.CANCELLED
    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.READY