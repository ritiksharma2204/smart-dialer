import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""
Basic evaluation/simulation for the Smart Dialer prototype.

Run from the repository root:
    python scripts/simulate.py

This exercises the predictive pacing and safety boundary under the
assignment scenarios A-D, including provider degradation.
"""

from dataclasses import dataclass

from app.services.pacing_engine import PacingMetrics, PredictivePacingEngine
from app.services.safety_controller import SafetyController


@dataclass
class ProviderScenario:
    latency_ms: int
    failure_rate: float
    healthy: bool


SCENARIOS = [
    ("A", 0.20, 120, ProviderScenario(100, 0.02, True)),
    ("B", 0.50, 90, ProviderScenario(250, 0.05, True)),
    ("C", 0.70, 180, ProviderScenario(500, 0.10, True)),
    ("D", 0.50, 120, ProviderScenario(800, 0.30, False)),
]


def run():
    pacing = PredictivePacingEngine()
    safety = SafetyController()

    print("\nSMART DIALER BASIC EVALUATION")
    print("=" * 78)
    print(
        f"{'Scenario':<10}{'Answer':<10}{'Talk(s)':<10}"
        f"{'Latency':<10}{'Failure':<10}{'Requested':<12}"
        f"{'Allowed':<10}{'Approved':<10}{'Fallback':<10}"
    )
    print("-" * 78)

    for name, answer_rate, talk_time, provider in SCENARIOS:
        available_agents = 10
        ringing_calls = 3 if name != "D" else 5
        connected_calls = 2

        metrics = PacingMetrics(
            available_agents=available_agents,
            ringing_calls=ringing_calls,
            connected_calls=connected_calls,
            historical_answer_rate=answer_rate,
            avg_talk_time_seconds=talk_time,
            provider_healthy=provider.healthy,
        )

        decision = pacing.calculate(metrics)

        safety_decision = safety.evaluate(
            requested_calls=decision.requested_calls,
            available_agents=available_agents,
            reserved_agents=0,
            ringing_calls=ringing_calls,
            provider_healthy=provider.healthy,
        )

        print(
            f"{name:<10}{answer_rate:<10.0%}{talk_time:<10}"
            f"{provider.latency_ms:<10}{provider.failure_rate:<10.0%}"
            f"{decision.requested_calls:<12}"
            f"{safety_decision.allowed_calls:<10}"
            f"{str(safety_decision.approved):<10}"
            f"{str(safety_decision.fallback_to_progressive):<10}"
        )

    print("\nInterpretation")
    print("-" * 78)
    print("* Lower answer rates increase the predictive dial request.")
    print("* The Safety Controller caps the request by available capacity.")
    print("* Ringing-call limits independently reduce the safe dial count.")
    print("* Provider degradation stops predictive dialing and requests fallback.")
    print("* Provider latency/failure values are simulation inputs; they do not")
    print("  change database state because this script is a deterministic eval.")
    print("\nFor end-to-end failure behavior, run:")
    print("    pytest -q")
    print("and for HTTP/load behavior:")
    print("    k6 run --env BASE_URL=http://127.0.0.1:8000 "
          "--env CAMPAIGN_ID=1 load-tests/dial-cycle.js")


if __name__ == "__main__":
    run()
