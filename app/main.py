from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Agent, Borrower, Call, Campaign, ProviderEvent  # noqa: F401
from app.services.dialer import SmartDialer
from app.services.pacing_engine import PacingMetrics, PredictivePacingEngine
from app.services.safety_controller import SafetyController


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Dialer")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/campaigns/{campaign_id}/dial")
def run_dial_cycle(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    dialer = SmartDialer(
        pacing_engine=PredictivePacingEngine(),
        safety_controller=SafetyController(),
    )

    metrics = PacingMetrics(
        available_agents=0,
        ringing_calls=0,
        connected_calls=0,
        historical_answer_rate=0.5,
        avg_talk_time_seconds=120,
        provider_healthy=True,
    )

    calls = dialer.run_once(
        db=db,
        campaign_id=campaign_id,
        metrics=metrics,
        reserved_agents=0,
        provider="provider_a",
    )

    db.commit()

    return {
        "campaign_id": campaign_id,
        "calls_started": len(calls),
        "call_ids": [call.id for call in calls],
    }
