from dataclasses import dataclass


@dataclass
class PacingMetrics:
    available_agents: int
    ringing_calls: int
    connected_calls: int
    historical_answer_rate: float
    avg_talk_time_seconds: float
    provider_healthy: bool = True


@dataclass
class PacingDecision:
    requested_calls: int
    reason: str


class PredictivePacingEngine:
    """
    Predicts how many calls should be started.

    IMPORTANT:
    This class only recommends a number.
    It does NOT reserve agents, borrowers, or call the provider.
    The Safety Controller is responsible for enforcing hard limits.
    """

    def __init__(
        self,
        target_utilization: float = 0.90,
        max_overdial_ratio: float = 1.5,
    ):
        self.target_utilization = target_utilization
        self.max_overdial_ratio = max_overdial_ratio

    def calculate(self, metrics: PacingMetrics) -> PacingDecision:
        # No agents -> nothing should be dialed.
        if metrics.available_agents <= 0:
            return PacingDecision(
                requested_calls=0,
                reason="no available agents",
            )

        # Provider is unhealthy -> stop predictive dialing.
        if not metrics.provider_healthy:
            return PacingDecision(
                requested_calls=0,
                reason="provider unhealthy",
            )

        answer_rate = max(
            0.05,
            min(metrics.historical_answer_rate, 1.0),
        )

        # Number of agents we expect to become available.
        expected_capacity = (
            metrics.available_agents
            * self.target_utilization
        )

        # Predictive dialing compensates for calls that won't be answered.
        predicted_dials = expected_capacity / answer_rate

        # Never request an unreasonable amount of over-dialing.
        max_allowed = (
            metrics.available_agents
            * self.max_overdial_ratio
        )

        predicted_dials = min(
            predicted_dials,
            max_allowed,
        )

        # Existing ringing calls are already consuming predictive capacity.
        remaining = predicted_dials - metrics.ringing_calls

        requested = max(0, int(remaining))
        if answer_rate >= 1.0:
            requested = metrics.available_agents

        return PacingDecision(
            requested_calls=requested,
            reason=(
                f"answer_rate={answer_rate:.2f}, "
                f"expected_capacity={expected_capacity:.1f}, "
                f"ringing={metrics.ringing_calls}"
            ),
        )