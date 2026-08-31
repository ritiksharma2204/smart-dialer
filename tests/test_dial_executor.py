from app.models import Agent, Borrower, Campaign, Call
from app.state.agent_state import AgentState
from app.state.call_state import CallState
from app.services.dial_executor import DialExecutor
from app.providers.registry import ProviderRegistry
from app.models.borrower import BorrowerStatus


def test_dial_executor_initiates_call(db):
    campaign = Campaign(name="Executor Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Agent Executor",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Borrower Executor",
        phone_number="+919999999999",
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

    executor = DialExecutor(
        provider_registry=ProviderRegistry(),
    )

    result = executor.execute(
        db=db,
        call=call,
        phone_number=borrower.phone_number,
    )

    assert result.id == call.id
    assert result.provider_call_id is not None
    assert result.provider_call_id.startswith("provider-a-")
    assert result.status == CallState.INITIATED

def test_dial_executor_marks_call_failed_when_provider_fails(db):
    campaign = Campaign(name="Failure Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Agent Failure",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Borrower Failure",
        phone_number="+917777777777",
    )

    db.add_all([agent, borrower])
    db.flush()

    call = Call(
        campaign_id=campaign.id,
        agent_id=agent.id,
        borrower_id=borrower.id,
        provider="provider_b",
        status=CallState.RESERVED,
    )

    db.add(call)
    db.flush()

    class FailingProvider:
        def initiate_call(self, call_id, phone_number, event_callback):
            raise RuntimeError("Provider unavailable")

    class TestRegistry:
        def get(self, provider):
            return FailingProvider()

    executor = DialExecutor(
        provider_registry=TestRegistry(),
    )

    result = executor.execute(
        db=db,
        call=call,
        phone_number=borrower.phone_number,
    )

    assert result.status == CallState.FAILED
    assert result.provider_call_id is None

def test_failed_dial_releases_agent_and_borrower(db):
    campaign = Campaign(name="Release Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Agent Release",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Borrower Release",
        phone_number="+916666666666",
        status=BorrowerStatus.RESERVED,
    )

    db.add_all([agent, borrower])
    db.flush()

    call = Call(
        campaign_id=campaign.id,
        agent_id=agent.id,
        borrower_id=borrower.id,
        provider="provider_b",
        status=CallState.RESERVED,
    )

    db.add(call)
    db.flush()

    class FailingProvider:
        def initiate_call(self, call_id, phone_number, event_callback):
            raise RuntimeError("Provider unavailable")

    class TestRegistry:
        def get(self, provider):
            return FailingProvider()

    executor = DialExecutor(
        provider_registry=TestRegistry(),
    )

    result = executor.execute(
        db=db,
        call=call,
        phone_number=borrower.phone_number,
    )

    assert result.status == CallState.FAILED

    db.refresh(agent)
    db.refresh(borrower)

    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.READY

def test_successful_dial_moves_agent_to_dialing(db):
    campaign = Campaign(name="Dialing Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Agent Dialing",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Borrower Dialing",
        phone_number="+915555555555",
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

    executor = DialExecutor(
        provider_registry=ProviderRegistry(),
    )

    result = executor.execute(
        db=db,
        call=call,
        phone_number=borrower.phone_number,
    )

    db.refresh(agent)

    assert result.status == CallState.INITIATED
    assert result.provider_call_id is not None
    assert agent.status == AgentState.DIALING

def test_provider_failure_releases_reserved_resources(db):
    campaign = Campaign(name="Provider Failure Recovery")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Failure Agent",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Failure Borrower",
        phone_number="+919111111111",
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

    class FailingProvider:
        def initiate_call(self, call_id, phone_number, event_callback):
            raise RuntimeError("provider outage")

    class TestRegistry:
        def get(self, provider):
            return FailingProvider()

    executor = DialExecutor(
        provider_registry=TestRegistry(),
    )

    result = executor.execute(
        db=db,
        call=call,
        phone_number=borrower.phone_number,
    )

    db.refresh(agent)
    db.refresh(borrower)

    assert result.status == CallState.FAILED
    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.READY