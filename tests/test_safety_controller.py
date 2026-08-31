from app.services.safety_controller import SafetyController


def test_safety_controller_approves_within_capacity():
    controller = SafetyController()

    decision = controller.evaluate(
        requested_calls=5,
        available_agents=10,
        reserved_agents=0,
        ringing_calls=0,
        provider_healthy=True,
    )

    assert decision.approved is True
    assert decision.allowed_calls == 5
    assert decision.fallback_to_progressive is False


def test_safety_controller_reduces_excessive_request():
    controller = SafetyController()

    decision = controller.evaluate(
        requested_calls=15,
        available_agents=10,
        reserved_agents=2,
        ringing_calls=0,
        provider_healthy=True,
    )

    assert decision.approved is True
    assert decision.allowed_calls == 8


def test_safety_controller_rejects_when_no_agents_available():
    controller = SafetyController()

    decision = controller.evaluate(
        requested_calls=5,
        available_agents=2,
        reserved_agents=2,
        ringing_calls=0,
        provider_healthy=True,
    )

    assert decision.approved is False
    assert decision.allowed_calls == 0


def test_provider_failure_forces_progressive_fallback():
    controller = SafetyController()

    decision = controller.evaluate(
        requested_calls=10,
        available_agents=10,
        reserved_agents=0,
        ringing_calls=0,
        provider_healthy=False,
    )

    assert decision.approved is False
    assert decision.allowed_calls == 0
    assert decision.fallback_to_progressive is True


def test_ringing_limit_reduces_request():
    controller = SafetyController(
        max_total_ringing=10,
    )

    decision = controller.evaluate(
        requested_calls=8,
        available_agents=20,
        reserved_agents=0,
        ringing_calls=7,
        provider_healthy=True,
    )

    assert decision.approved is True
    assert decision.allowed_calls == 3

def test_safety_controller_never_exceeds_available_agents():
    controller = SafetyController()

    decision = controller.evaluate(
        requested_calls=100,
        available_agents=10,
        reserved_agents=0,
        ringing_calls=0,
        provider_healthy=True,
    )

    assert decision.allowed_calls <= 10


def test_reserved_agents_reduce_safe_capacity():
    controller = SafetyController()

    decision = controller.evaluate(
        requested_calls=20,
        available_agents=10,
        reserved_agents=7,
        ringing_calls=0,
        provider_healthy=True,
    )

    assert decision.allowed_calls == 3


def test_zero_requested_calls_are_rejected():
    controller = SafetyController()

    decision = controller.evaluate(
        requested_calls=0,
        available_agents=10,
        reserved_agents=0,
        ringing_calls=0,
        provider_healthy=True,
    )

    assert decision.approved is False
    assert decision.allowed_calls == 0