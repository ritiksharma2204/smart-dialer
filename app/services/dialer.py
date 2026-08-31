from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.providers.registry import ProviderRegistry
from app.services.dial_executor import DialExecutor
from app.services.pacing_engine import (
    PacingMetrics,
    PredictivePacingEngine,
)
from app.services.progressive_dialer import ProgressiveDialer
from app.services.safety_controller import SafetyController


class SmartDialer:
    """
    Orchestrates the complete dialing pipeline.

    Metrics
       ↓
    Pacing Engine
       ↓
    Safety Controller
       ↓
    Progressive Dialer
       ↓
    Dial Executor
       ↓
    Telecom Provider
    """

    def __init__(
        self,
        pacing_engine: PredictivePacingEngine,
        safety_controller: SafetyController,
        provider_registry: ProviderRegistry | None = None,
    ):
        self.pacing_engine = pacing_engine
        self.safety_controller = safety_controller
        self.provider_registry = (
            provider_registry
            if provider_registry is not None
            else ProviderRegistry()
        )

    def calculate_safe_dial_count(
        self,
        metrics: PacingMetrics,
        reserved_agents: int,
    ):
        """
        Calculate how many calls may actually be started.

        The pacing engine produces a recommendation.
        The safety controller independently enforces limits.
        """

        pacing_decision = self.pacing_engine.calculate(metrics)

        safety_decision = self.safety_controller.evaluate(
            requested_calls=pacing_decision.requested_calls,
            available_agents=metrics.available_agents,
            reserved_agents=reserved_agents,
            ringing_calls=metrics.ringing_calls,
            provider_healthy=metrics.provider_healthy,
        )

        return pacing_decision, safety_decision

    def run_once(
        self,
        db: Session,
        campaign_id: int,
        metrics: PacingMetrics,
        reserved_agents: int,
        provider: str,
    ):
        """
        Execute one safe dialing cycle.

        Returns the calls successfully initiated.
        """

        pacing, safety = self.calculate_safe_dial_count(
            metrics=metrics,
            reserved_agents=reserved_agents,
        )

        if safety.allowed_calls <= 0:
            return []

        progressive_dialer = ProgressiveDialer(
            provider=provider,
        )

        calls = progressive_dialer.run_once(
            db=db,
            campaign_id=campaign_id,
            max_calls=safety.allowed_calls,
        )

        executor = DialExecutor(
            provider_registry=self.provider_registry,
        )

        executed_calls = []

        for call in calls:
            borrower = db.get(
                Borrower,
                call.borrower_id,
            )

            if borrower is None:
                continue

            executed_call = executor.execute(
                db=db,
                call=call,
                phone_number=borrower.phone_number,
            )

            executed_calls.append(executed_call)

        return executed_calls