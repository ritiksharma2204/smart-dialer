import pytest
from sqlalchemy import delete

from app.database import Base, SessionLocal, engine
from app.models import (
    Agent,
    Borrower,
    Call,
    Campaign,
    ProviderEvent,
)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()

        with SessionLocal() as cleanup:
            cleanup.execute(delete(ProviderEvent))
            cleanup.execute(delete(Call))
            cleanup.execute(delete(Borrower))
            cleanup.execute(delete(Agent))
            cleanup.execute(delete(Campaign))
            cleanup.commit()