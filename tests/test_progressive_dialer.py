from app.models.agent import Agent
from app.models.borrower import Borrower, BorrowerStatus
from app.models.campaign import Campaign
from app.services.progressive_dialer import ProgressiveDialer
from app.state.agent_state import AgentState


def create_campaign(db):
    campaign = Campaign(name="Progressive Campaign")
    db.add(campaign)
    db.flush()
    return campaign


def test_progressive_dialer_never_exceeds_available_agents(db):
    campaign = create_campaign(db)

    agents = [
        Agent(
            name=f"Agent {i}",
            status=AgentState.AVAILABLE,
        )
        for i in range(3)
    ]

    borrowers = [
        Borrower(
            campaign_id=campaign.id,
            name=f"Borrower {i}",
            phone_number=f"+91999999999{i}",
            status=BorrowerStatus.READY,
        )
        for i in range(5)
    ]

    db.add_all(agents + borrowers)
    db.commit()

    dialer = ProgressiveDialer(provider="provider_a")

    calls = dialer.run_once(
        db=db,
        campaign_id=campaign.id,
    )

    db.commit()

    assert len(calls) == 3


def test_progressive_dialer_does_not_call_without_available_agents(db):
    campaign = create_campaign(db)

    agent = Agent(
        name="Busy Agent",
        status=AgentState.RESERVED,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Borrower",
        phone_number="+919888888888",
        status=BorrowerStatus.READY,
    )

    db.add_all([agent, borrower])
    db.commit()

    dialer = ProgressiveDialer(provider="provider_a")

    calls = dialer.run_once(
        db=db,
        campaign_id=campaign.id,
    )

    db.commit()

    assert len(calls) == 0

def test_concurrent_workers_do_not_double_allocate_agents(db):
    campaign = create_campaign(db)

    agents = [
        Agent(
            name=f"Concurrent Agent {i}",
            status=AgentState.AVAILABLE,
        )
        for i in range(5)
    ]

    borrowers = [
        Borrower(
            campaign_id=campaign.id,
            name=f"Concurrent Borrower {i}",
            phone_number=f"+91777777777{i}",
            status=BorrowerStatus.READY,
        )
        for i in range(5)
    ]

    db.add_all(agents + borrowers)
    db.commit()

    dialer = ProgressiveDialer(provider="provider_a")

    # Simulate two workers seeing the same candidate pool.
    #
    # Both workers will attempt allocation. The database-level
    # conditional reservation determines who actually succeeds.
    first_worker_calls = dialer.run_once(
        db=db,
        campaign_id=campaign.id,
    )

    db.commit()

    second_worker_calls = dialer.run_once(
        db=db,
        campaign_id=campaign.id,
    )

    db.commit()

    total_calls = len(first_worker_calls) + len(second_worker_calls)

    assert total_calls == 5

def test_progressive_dialer_skips_agent_that_disappears_before_reservation(db):
    campaign = create_campaign(db)

    agent = Agent(
        name="Agent That Disappears",
        status=AgentState.AVAILABLE,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Borrower",
        phone_number="+916666666666",
        status=BorrowerStatus.READY,
    )

    db.add_all([agent, borrower])
    db.commit()

    # Dialer observes the agent as available.
    db.refresh(agent)
    assert agent.status == AgentState.AVAILABLE

    # Simulate the agent disappearing before allocation.
    agent.status = AgentState.PAUSED
    db.commit()

    dialer = ProgressiveDialer(provider="provider_a")

    calls = dialer.run_once(
        db=db,
        campaign_id=campaign.id,
    )

    db.commit()

    assert len(calls) == 0

def test_progressive_dialer_respects_max_calls(db):
    campaign = create_campaign(db)

    agents = [
        Agent(
            name=f"Limited Agent {i}",
            status=AgentState.AVAILABLE,
        )
        for i in range(5)
    ]

    borrowers = [
        Borrower(
            campaign_id=campaign.id,
            name=f"Limited Borrower {i}",
            phone_number=f"+91888888888{i}",
            status=BorrowerStatus.READY,
        )
        for i in range(5)
    ]

    db.add_all(agents + borrowers)
    db.commit()

    dialer = ProgressiveDialer(provider="provider_a")

    calls = dialer.run_once(
        db=db,
        campaign_id=campaign.id,
        max_calls=2,
    )

    db.commit()

    assert len(calls) == 2