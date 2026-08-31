from app.models.agent import Agent
from app.models.borrower import Borrower, BorrowerStatus
from app.models.campaign import Campaign
from app.services.call_allocator import allocate_call
from app.state.agent_state import AgentState


def test_failed_allocation_does_not_leave_agent_reserved(db):
    campaign = Campaign(name="Rollback Campaign")

    db.add(campaign)
    db.flush()

    agent = Agent(
        name="Agent 2",
        status=AgentState.AVAILABLE,
    )

    borrower = Borrower(
        campaign_id=campaign.id,
        name="Borrower 2",
        phone_number="+918888888888",
        status=BorrowerStatus.RESERVED,
    )

    db.add_all([agent, borrower])
    db.commit()

    call = allocate_call(
        db=db,
        agent_id=agent.id,
        borrower_id=borrower.id,
        campaign_id=campaign.id,
        provider="provider_a",
    )

    assert call is None

    db.rollback()

    db.refresh(agent)

    assert agent.status == AgentState.AVAILABLE