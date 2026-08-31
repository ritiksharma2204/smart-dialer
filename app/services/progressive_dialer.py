from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.borrower import Borrower, BorrowerStatus
from app.services.call_allocator import allocate_call
from app.state.agent_state import AgentState


class ProgressiveDialer:
    """
    Progressive dialer.

    Core invariant:
        Each available agent can produce at most one
        agent-bound outbound call.

    The dialer never talks directly to a telecom provider.
    """

    def __init__(self, provider: str):
        self.provider = provider

    def run_once(
        self,
        db: Session,
        campaign_id: int,
        max_calls: int | None = None,
    ) -> list:
        """
        Attempt to allocate calls for currently available agents.

        Returns the calls successfully allocated during this run.
        """
        
        agents = db.execute(
            select(Agent)
            .where(Agent.status == AgentState.AVAILABLE)
            .order_by(Agent.id)
        ).scalars().all()
        
        if max_calls is not None:
            agents = agents[:max_calls]

        borrowers = db.execute(
            select(Borrower)
            .where(
                Borrower.campaign_id == campaign_id,
                Borrower.status == BorrowerStatus.READY,
            )
            .order_by(Borrower.id)
        ).scalars().all()

        if max_calls is not None:
            agents = agents[:max_calls]
            borrowers = borrowers[:max_calls]
                    

        calls = []

        for agent, borrower in zip(agents, borrowers):
            call = allocate_call(
                db=db,
                agent_id=agent.id,
                borrower_id=borrower.id,
                campaign_id=campaign_id,
                provider=self.provider,
            )

            if call is not None:
                calls.append(call)

        return calls