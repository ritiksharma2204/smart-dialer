from enum import Enum


class AgentState(str, Enum):
    OFFLINE = "OFFLINE"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    DIALING = "DIALING"
    CONNECTED = "CONNECTED"
    WRAP_UP = "WRAP_UP"
    PAUSED = "PAUSED"


AGENT_TRANSITIONS = {
    AgentState.OFFLINE: {
        AgentState.AVAILABLE,
    },
    AgentState.AVAILABLE: {
        AgentState.RESERVED,
        AgentState.PAUSED,
        AgentState.OFFLINE,
    },
    AgentState.RESERVED: {
        AgentState.DIALING,
        AgentState.AVAILABLE,
    },
    AgentState.DIALING: {
        AgentState.CONNECTED,
        AgentState.AVAILABLE,
    },
    AgentState.CONNECTED: {
        AgentState.WRAP_UP,
    },
    AgentState.WRAP_UP: {
        AgentState.AVAILABLE,
        AgentState.OFFLINE,
    },
    AgentState.PAUSED: {
        AgentState.AVAILABLE,
        AgentState.OFFLINE,
    },
}


def can_transition(
    current: AgentState,
    target: AgentState,
) -> bool:
    return target in AGENT_TRANSITIONS.get(current, set())