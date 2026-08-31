from app.state.agent_state import (
    AgentState,
    can_transition as can_agent_transition,
)

from app.state.call_state import (
    CallState,
    can_transition as can_call_transition,
)


def test_agent_can_be_reserved_from_available():
    assert can_agent_transition(
        AgentState.AVAILABLE,
        AgentState.RESERVED,
    )


def test_agent_cannot_go_directly_from_available_to_connected():
    assert not can_agent_transition(
        AgentState.AVAILABLE,
        AgentState.CONNECTED,
    )


def test_call_can_move_from_ringing_to_answered():
    assert can_call_transition(
        CallState.RINGING,
        CallState.ANSWERED,
    )


def test_completed_call_cannot_be_resurrected():
    assert not can_call_transition(
        CallState.COMPLETED,
        CallState.ANSWERED,
    )