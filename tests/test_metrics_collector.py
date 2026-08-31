from app.models import Agent, Borrower, Campaign, Call
from app.models.borrower import BorrowerStatus
from app.services.metrics_collector import collect_metrics
from app.state.agent_state import AgentState
from app.state.call_state import CallState


def test_collect_metrics_from_database(db):
    campaign = Campaign(name="Metrics Campaign")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Metrics Agent",
        status=AgentState.AVAILABLE,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Metrics Borrower",
        phone_number="+919999999999",
        status=BorrowerStatus.READY,
    )

    db.add_all([agent, borrower])
    db.flush()

    statuses = [
        CallState.QUEUED,
        CallState.RESERVED,
        CallState.INITIATED,
        CallState.RINGING,
        CallState.ANSWERED,
        CallState.CONNECTED,
        CallState.COMPLETED,
        CallState.FAILED,
        CallState.CANCELLED,
    ]

    for status in statuses:
        db.add(
            Call(
                campaign_id=campaign.id,
                agent_id=agent.id,
                borrower_id=borrower.id,
                provider="provider_a",
                status=status,
            )
        )

    db.commit()

    metrics = collect_metrics(
        db,
        campaign_id=campaign.id,
    )

    assert metrics.total_calls == 9
    assert metrics.queued_calls == 1
    assert metrics.reserved_calls == 1
    assert metrics.initiated_calls == 1
    assert metrics.ringing_calls == 1
    assert metrics.answered_calls == 1
    assert metrics.connected_calls == 1
    assert metrics.completed_calls == 1
    assert metrics.failed_calls == 1
    assert metrics.cancelled_calls == 1


def test_collect_metrics_can_filter_by_campaign(db):
    campaign_a = Campaign(name="Campaign A")
    campaign_b = Campaign(name="Campaign B")

    db.add_all([campaign_a, campaign_b])
    db.flush()

    agent = Agent(
        name="Metrics Agent",
        status=AgentState.AVAILABLE,
    )

    borrower_a = Borrower(
        campaign_id=campaign_a.id,
        name="Borrower A",
        phone_number="+911111111111",
        status=BorrowerStatus.READY,
    )

    borrower_b = Borrower(
        campaign_id=campaign_b.id,
        name="Borrower B",
        phone_number="+922222222222",
        status=BorrowerStatus.READY,
    )

    db.add_all([agent, borrower_a, borrower_b])
    db.flush()

    db.add_all([
        Call(
            campaign_id=campaign_a.id,
            agent_id=agent.id,
            borrower_id=borrower_a.id,
            provider="provider_a",
            status=CallState.COMPLETED,
        ),
        Call(
            campaign_id=campaign_b.id,
            agent_id=agent.id,
            borrower_id=borrower_b.id,
            provider="provider_a",
            status=CallState.FAILED,
        ),
    ])

    db.commit()

    metrics = collect_metrics(
        db,
        campaign_id=campaign_a.id,
    )

    assert metrics.total_calls == 1
    assert metrics.completed_calls == 1
    assert metrics.failed_calls == 0

def test_count_available_agents(db):
    agents = [
        Agent(
            name="Available Agent",
            status=AgentState.AVAILABLE,
        ),
        Agent(
            name="Busy Agent",
            status=AgentState.CONNECTED,
        ),
        Agent(
            name="Paused Agent",
            status=AgentState.PAUSED,
        ),
    ]

    db.add_all(agents)
    db.commit()

    from app.services.metrics_collector import count_available_agents

    assert count_available_agents(db) == 1