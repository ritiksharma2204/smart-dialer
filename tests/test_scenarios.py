from app.models import Agent, Borrower, Campaign
from app.models.borrower import BorrowerStatus
from app.services.dialer import SmartDialer
from app.services.pacing_engine import (
    PacingMetrics,
    PredictivePacingEngine,
)
from app.services.progressive_dialer import ProgressiveDialer
from app.services.safety_controller import SafetyController
from app.state.agent_state import AgentState

from app.state.call_state import CallState


def test_scenario_a_healthy_campaign(db):
    campaign = Campaign(name="Scenario A")
    db.add(campaign)
    db.flush()

    agents = [
        Agent(
            name=f"Scenario A Agent {i}",
            status=AgentState.AVAILABLE,
        )
        for i in range(5)
    ]

    borrowers = [
        Borrower(
            campaign_id=campaign.id,
            name=f"Scenario A Borrower {i}",
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
        max_calls=5,
    )

    db.commit()

    assert len(calls) == 5

def test_scenario_b_low_answer_rate_is_capped_by_safety():
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

    assert pacing.requested_calls > 10
    assert safety.allowed_calls == 10
    assert safety.allowed_calls < pacing.requested_calls

def test_scenario_c_provider_degradation_triggers_fallback():
    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(),
    )

    metrics = PacingMetrics(
        available_agents=10,
        ringing_calls=3,
        connected_calls=2,
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
    assert safety.approved is False
    assert safety.fallback_to_progressive is True

def test_scenario_d_high_ringing_load_limits_new_calls():
    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(
            max_total_ringing=10,
        ),
    )

    metrics = PacingMetrics(
        available_agents=10,
        ringing_calls=8,
        connected_calls=2,
        historical_answer_rate=0.8,
        avg_talk_time_seconds=120,
        provider_healthy=True,
    )

    pacing, safety = dialer.calculate_safe_dial_count(
        metrics=metrics,
        reserved_agents=0,
    )

    assert pacing.requested_calls > 0
    assert safety.approved is True
    assert safety.allowed_calls == 2
    assert safety.allowed_calls < pacing.requested_calls

def test_scenario_d_provider_call_failure_releases_resources(db):
    campaign = Campaign(name="Scenario D")
    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Scenario D Agent",
        status=AgentState.AVAILABLE,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Scenario D Borrower",
        phone_number="+919999999999",
        status=BorrowerStatus.READY,
    )

    db.add_all([agent, borrower])
    db.commit()

    class FailingProvider:
        def initiate_call(self, call_id, phone_number, event_callback):
            raise RuntimeError("Provider unavailable")

    class TestRegistry:
        def get(self, provider):
            return FailingProvider()

    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(),
        provider_registry=TestRegistry(),
    )

    metrics = PacingMetrics(
        available_agents=1,
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

    assert len(calls) == 1
    assert calls[0].status == CallState.FAILED

    db.refresh(agent)
    db.refresh(borrower)

    assert agent.status == AgentState.AVAILABLE
    assert borrower.status == BorrowerStatus.READY