from sqlalchemy.orm import Session

from app.models.call import Call
from app.state.call_state import CallState
from app.providers.registry import ProviderRegistry

from app.repositories.agent_repository import release_agent
from app.repositories.borrower_repository import release_borrower

from app.state.agent_state import AgentState
from app.models.agent import Agent


class DialExecutor:
    def __init__(self, provider_registry: ProviderRegistry):
        self.provider_registry = provider_registry

    def execute(
        self,
        db: Session,
        call: Call,
        phone_number: str,
    ) -> Call:

        provider = self.provider_registry.get(call.provider)

        try:
            provider_call = provider.initiate_call(
                call_id=call.id,
                phone_number=phone_number,
                event_callback=lambda event: None,
            )

        except Exception:
            call.status = CallState.FAILED
            
            release_agent(db, call.agent_id)
            release_borrower(db, call.borrower_id)

            db.flush()
            return call

        call.provider_call_id = provider_call.provider_call_id
        call.status = CallState.INITIATED

        call_agent = db.get(Agent, call.agent_id)
        if call_agent is None:
            raise ValueError(f"Agent not found: {call.agent_id}")
        if call_agent.status != AgentState.RESERVED:
            raise ValueError(
                f"Agent {call.agent_id} is not reserved"
            )
        call_agent.status = AgentState.DIALING

        db.flush()

        return call