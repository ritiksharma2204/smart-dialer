from datetime import datetime, timezone

from app.services.dial_executor import DialExecutor


def test_provider_outage_marks_call_failed_and_releases_resources(db):
    from app.models import Agent, Borrower, Campaign, Call
    from app.models.borrower import BorrowerStatus
    from app.state.agent_state import AgentState
    from app.state.call_state import CallState

    campaign = Campaign(name="Provider Outage Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Outage Agent",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Outage Borrower",
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
    db.flush()

    class OutageProvider:
        def initiate_call(self, call_id, phone_number, event_callback):
            raise RuntimeError("Provider outage")

    class OutageRegistry:
        def get(self, provider):
            return OutageProvider()

    executor = DialExecutor(
        provider_registry=OutageRegistry(),
    )

    result = executor.execute(
        db=db,
        call=call,
        phone_number=borrower.phone_number,
    )

    db.refresh(agent)
    db.refresh(borrower)

    assert result.status == CallState.FAILED
    assert result.provider_call_id is None

    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.READY

def test_duplicate_provider_event_is_safe_to_replay(db):
    from datetime import datetime

    from app.models import Agent, Borrower, Campaign, Call
    from app.models.borrower import BorrowerStatus
    from app.services.provider_event_processor import process_provider_event
    from app.state.agent_state import AgentState
    from app.state.call_state import CallState

    campaign = Campaign(name="Replay Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Replay Agent",
        status=AgentState.DIALING,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Replay Borrower",
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

    timestamp = datetime.now(timezone.utc)

    first_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="replay-event-1",
        call_id=call.id,
        event_type="ANSWERED",
        event_timestamp=timestamp,
        payload={"attempt": 1},
    )

    db.commit()
    db.refresh(call)

    assert first_result is True
    assert call.status == CallState.ANSWERED

    second_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="replay-event-1",
        call_id=call.id,
        event_type="ANSWERED",
        event_timestamp=timestamp,
        payload={"attempt": 2},
    )

    db.commit()
    db.refresh(call)

    assert second_result is False
    assert call.status == CallState.ANSWERED

def test_late_event_after_terminal_state_is_ignored(db):
    from datetime import datetime, timedelta

    from app.models import Agent, Borrower, Campaign, Call
    from app.models.borrower import BorrowerStatus
    from app.services.provider_event_processor import process_provider_event
    from app.state.agent_state import AgentState
    from app.state.call_state import CallState

    campaign = Campaign(name="Terminal State Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Terminal Agent",
        status=AgentState.DIALING,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Terminal Borrower",
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

    completed_time = datetime.now(timezone.utc)

    completed_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="terminal-completed-1",
        call_id=call.id,
        event_type="COMPLETED",
        event_timestamp=completed_time,
        payload={},
    )

    db.commit()
    db.refresh(call)

    assert completed_result is True
    assert call.status == CallState.COMPLETED

    # A late ANSWERED event arrives after the call is already terminal.
    late_result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="terminal-answered-late",
        call_id=call.id,
        event_type="ANSWERED",
        event_timestamp=completed_time - timedelta(seconds=5),
        payload={},
    )

    db.commit()
    db.refresh(call)

    assert late_result is False
    assert call.status == CallState.COMPLETED

def test_cancelled_call_releases_agent_and_resets_borrower(db):
    from datetime import datetime

    from app.models import Agent, Borrower, Campaign, Call
    from app.models.borrower import BorrowerStatus
    from app.services.provider_event_processor import process_provider_event
    from app.state.agent_state import AgentState
    from app.state.call_state import CallState

    campaign = Campaign(name="Cancellation Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Cancellation Agent",
        status=AgentState.DIALING,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Cancellation Borrower",
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

    result = process_provider_event(
        db,
        provider="provider_a",
        provider_event_id="cancelled-call-1",
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