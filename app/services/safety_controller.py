from dataclasses import dataclass


@dataclass
class SafetyDecision:
    approved: bool
    allowed_calls: int
    reason: str
    fallback_to_progressive: bool = False


class SafetyController:
    """
    Deterministic safety boundary between pacing logic and the telecom provider.

    The pacing engine can request N calls, but it can never directly place them.
    """

    def __init__(
        self,
        max_agent_utilization: float = 1.0,
        max_ringing_per_agent: float = 1.0,
        max_total_ringing: int = 100,
    ):
        self.max_agent_utilization = max_agent_utilization
        self.max_ringing_per_agent = max_ringing_per_agent
        self.max_total_ringing = max_total_ringing

    def evaluate(
        self,
        requested_calls: int,
        available_agents: int,
        reserved_agents: int,
        ringing_calls: int,
        provider_healthy: bool,
    ) -> SafetyDecision:

        if not provider_healthy:
            return SafetyDecision(
                approved=False,
                allowed_calls=0,
                reason="Provider unhealthy",
                fallback_to_progressive=True
            )

        if requested_calls <= 0:
            return SafetyDecision(
                approved=False,
                allowed_calls=0,
                reason="No calls requested",
                
            )

        usable_agents = max(
            0,
            available_agents - reserved_agents,
        )

        if usable_agents == 0:
            return SafetyDecision(
                approved=False,
                allowed_calls=0,
                reason="No usable agents available",
            )

        # Safety rule:
        # never allow more outstanding calls than the
        # configured capacity of the available agents.
        agent_capacity = int(
            usable_agents * self.max_agent_utilization
        )

        # Independent ringing protection.
        ringing_capacity = max(
            0,
            self.max_total_ringing - ringing_calls,
        )

        allowed_calls = min(
            requested_calls,
            agent_capacity,
            ringing_capacity,
        )

        if allowed_calls <= 0:
            return SafetyDecision(
                approved=False,
                allowed_calls=0,
                reason="Safety limits reached",
            )

        if allowed_calls < requested_calls:
            return SafetyDecision(
                approved=True,
                allowed_calls=allowed_calls,
                reason="Request reduced by safety limits",
            )

        return SafetyDecision(
            approved=True,
            allowed_calls=allowed_calls,
            reason="Request approved",
        )