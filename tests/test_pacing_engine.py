from app.services.pacing_engine import (
    PacingMetrics,
    PredictivePacingEngine,
)


def test_no_agents_means_no_calls():
    engine = PredictivePacingEngine()

    decision = engine.calculate(
        PacingMetrics(
            available_agents=0,
            ringing_calls=0,
            connected_calls=0,
            historical_answer_rate=0.5,
            avg_talk_time_seconds=120,
        )
    )

    assert decision.requested_calls == 0


def test_unhealthy_provider_stops_predictive_dialing():
    engine = PredictivePacingEngine()

    decision = engine.calculate(
        PacingMetrics(
            available_agents=10,
            ringing_calls=0,
            connected_calls=0,
            historical_answer_rate=0.5,
            avg_talk_time_seconds=120,
            provider_healthy=False,
        )
    )

    assert decision.requested_calls == 0


def test_lower_answer_rate_requires_more_dials():
    engine = PredictivePacingEngine()

    low_answer = engine.calculate(
        PacingMetrics(
            available_agents=10,
            ringing_calls=0,
            connected_calls=0,
            historical_answer_rate=0.2,
            avg_talk_time_seconds=120,
        )
    )

    high_answer = engine.calculate(
        PacingMetrics(
            available_agents=10,
            ringing_calls=0,
            connected_calls=0,
            historical_answer_rate=0.7,
            avg_talk_time_seconds=120,
        )
    )

    assert low_answer.requested_calls > high_answer.requested_calls


def test_ringing_calls_reduce_new_requests():
    engine = PredictivePacingEngine()

    without_ringing = engine.calculate(
        PacingMetrics(
            available_agents=10,
            ringing_calls=0,
            connected_calls=0,
            historical_answer_rate=0.5,
            avg_talk_time_seconds=120,
        )
    )

    with_ringing = engine.calculate(
        PacingMetrics(
            available_agents=10,
            ringing_calls=5,
            connected_calls=0,
            historical_answer_rate=0.5,
            avg_talk_time_seconds=120,
        )
    )

    assert with_ringing.requested_calls < without_ringing.requested_calls