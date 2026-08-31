from app.services.dialer import SmartDialer
from app.services.pacing_engine import (
    PacingMetrics,
    PredictivePacingEngine,
)
from app.services.safety_controller import SafetyController
from app.models.agent import Agent
from app.models.borrower import Borrower, BorrowerStatus
from app.models.campaign import Campaign
from app.state.agent_state import AgentState


def test_dialer_applies_safety_after_pacing():
    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(),
    )

    metrics = PacingMetrics(
        available_agents=10,
        ringing_calls=0,
        connected_calls=0,
        historical_answer_rate=0.20,
        avg_talk_time_seconds=120,
        provider_healthy=True,
    )

    pacing, safety = dialer.calculate_safe_dial_count(
        metrics=metrics,
        reserved_agents=0,
    )

    # Predictive engine can request more than the agent capacity.
    assert pacing.requested_calls > 10

    # Safety controller must cap it.
    assert safety.allowed_calls <= 10


def test_dialer_stops_when_provider_is_unhealthy():
    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(),
    )

    metrics = PacingMetrics(
        available_agents=10,
        ringing_calls=0,
        connected_calls=0,
        historical_answer_rate=0.5,
        avg_talk_time_seconds=120,
        provider_healthy=False,
    )

    pacing, safety = dialer.calculate_safe_dial_count(
        metrics=metrics,
        reserved_agents=0,
    )

    assert pacing.requested_calls == 0
    assert safety.allowed_calls == 0
    assert safety.fallback_to_progressive is True


def test_reserved_agents_reduce_safe_capacity():
    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(),
    )

    metrics = PacingMetrics(
        available_agents=10,
        ringing_calls=0,
        connected_calls=0,
        historical_answer_rate=0.5,
        avg_talk_time_seconds=120,
        provider_healthy=True,
    )

    _, safety = dialer.calculate_safe_dial_count(
        metrics=metrics,
        reserved_agents=8,
    )

    assert safety.allowed_calls <= 2

from app.models.agent import Agent
from app.models.borrower import Borrower, BorrowerStatus
from app.models.campaign import Campaign
from app.state.agent_state import AgentState
from app.state.call_state import CallState


def test_dialer_runs_safe_calls_end_to_end(db):
    campaign = Campaign(name="End To End Campaign")
    db.add(campaign)
    db.flush()

    agents = [
        Agent(
            name=f"E2E Agent {i}",
            status=AgentState.AVAILABLE,
        )
        for i in range(3)
    ]

    borrowers = [
        Borrower(
            campaign_id=campaign.id,
            name=f"E2E Borrower {i}",
            phone_number=f"+91999999999{i}",
            status=BorrowerStatus.READY,
        )
        for i in range(3)
    ]

    db.add_all(agents + borrowers)
    db.commit()

    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(),
    )

    metrics = PacingMetrics(
        available_agents=3,
        ringing_calls=0,
        connected_calls=0,
        historical_answer_rate=1.0,
        avg_talk_time_seconds=120,
        provider_healthy=True,
    )

    calls = dialer.run_once(
        db=db,
        campaign_id=campaign.id,
        metrics=metrics,
        reserved_agents=0,
        provider="provider_a",
    )

    db.commit()

    assert len(calls) == 3

    for call in calls:
        assert call.status == CallState.INITIATED
        assert call.provider_call_id is not None

def test_dialer_stops_new_calls_when_provider_becomes_unhealthy(db):
    campaign = Campaign(name="Provider Outage Campaign")
    db.add(campaign)
    db.flush()

    agents = [
        Agent(
            name=f"Outage Agent {i}",
            status=AgentState.AVAILABLE,
        )
        for i in range(3)
    ]

    borrowers = [
        Borrower(
            campaign_id=campaign.id,
            name=f"Outage Borrower {i}",
            phone_number=f"+91888888888{i}",
            status=BorrowerStatus.READY,
        )
        for i in range(3)
    ]

    db.add_all(agents + borrowers)
    db.commit()

    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(),
    )

    metrics = PacingMetrics(
        available_agents=3,
        ringing_calls=0,
        connected_calls=0,
        historical_answer_rate=1.0,
        avg_talk_time_seconds=120,
        provider_healthy=False,
    )

    calls = dialer.run_once(
        db=db,
        campaign_id=campaign.id,
        metrics=metrics,
        reserved_agents=0,
        provider="provider_a",
    )

    db.commit()

    assert calls == []

    db.refresh(agents[0])
    db.refresh(agents[1])
    db.refresh(agents[2])

    assert all(
        agent.status == AgentState.AVAILABLE
        for agent in agents
    )