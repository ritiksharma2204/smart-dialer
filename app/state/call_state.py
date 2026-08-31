from enum import Enum


class CallState(str, Enum):
    QUEUED = "QUEUED"
    RESERVED = "RESERVED"
    INITIATED = "INITIATED"
    RINGING = "RINGING"
    ANSWERED = "ANSWERED"
    CONNECTED = "CONNECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


CALL_TRANSITIONS = {
    CallState.QUEUED: {
        CallState.RESERVED,
        CallState.CANCELLED,
    },
    CallState.RESERVED: {
        CallState.INITIATED,
        CallState.CANCELLED,
    },
    CallState.INITIATED: {
        CallState.RINGING,
        CallState.ANSWERED,
        CallState.FAILED,
        CallState.CANCELLED,
    },
    CallState.RINGING: {
        CallState.ANSWERED,
        CallState.FAILED,
        CallState.CANCELLED,
    },
    CallState.ANSWERED: {
        CallState.CONNECTED,
        CallState.COMPLETED,
    },
    CallState.CONNECTED: {
        CallState.COMPLETED,
        CallState.FAILED,
    },
    CallState.COMPLETED: set(),
    CallState.FAILED: set(),
    CallState.CANCELLED: set(),
}


def can_transition(
    current: CallState,
    target: CallState,
) -> bool:
    return target in CALL_TRANSITIONS.get(current, set())