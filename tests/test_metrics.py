from app.services.metrics import DialerMetrics


def test_answer_rate_with_successful_calls():
    metrics = DialerMetrics(
        total_calls=10,
        queued_calls=0,
        reserved_calls=0,
        initiated_calls=2,
        ringing_calls=2,
        answered_calls=2,
        connected_calls=1,
        completed_calls=2,
        failed_calls=1,
        cancelled_calls=0,
    )

    # Attempted = 10
    # Successful = 2 + 1 + 2 = 5
    assert metrics.answer_rate == 0.5


def test_answer_rate_is_zero_when_no_calls_attempted():
    metrics = DialerMetrics(
        total_calls=0,
        queued_calls=0,
        reserved_calls=0,
        initiated_calls=0,
        ringing_calls=0,
        answered_calls=0,
        connected_calls=0,
        completed_calls=0,
        failed_calls=0,
        cancelled_calls=0,
    )

    assert metrics.answer_rate == 0.0


def test_answer_rate_counts_completed_calls_as_successful():
    metrics = DialerMetrics(
        total_calls=5,
        queued_calls=0,
        reserved_calls=0,
        initiated_calls=0,
        ringing_calls=0,
        answered_calls=0,
        connected_calls=0,
        completed_calls=5,
        failed_calls=0,
        cancelled_calls=0,
    )

    assert metrics.answer_rate == 1.0


def test_answer_rate_excludes_queued_and_reserved_calls():
    metrics = DialerMetrics(
        total_calls=10,
        queued_calls=4,
        reserved_calls=3,
        initiated_calls=1,
        ringing_calls=1,
        answered_calls=1,
        connected_calls=0,
        completed_calls=0,
        failed_calls=0,
        cancelled_calls=0,
    )

    # Only 3 calls are attempted:
    # initiated + ringing + answered
    # 1 successful / 3 attempted
    assert metrics.answer_rate == 1 / 3