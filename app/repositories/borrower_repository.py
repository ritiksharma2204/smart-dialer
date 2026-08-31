from datetime import datetime, timezone, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.borrower import Borrower, BorrowerStatus


def reserve_borrower(
    db: Session,
    borrower_id: int,
) -> Borrower | None:
    """
    Atomically reserve a borrower.

    Returns the borrower if successful.
    Returns None if the borrower is unavailable.
    """

    now = datetime.now(timezone.utc)

    result = db.execute(
        update(Borrower)
        .where(
            Borrower.id == borrower_id,
            Borrower.status == BorrowerStatus.READY,
        )
        .values(
            status=BorrowerStatus.RESERVED,
            last_called_at=now,
            attempt_count=Borrower.attempt_count + 1,
        )
    )

    if result.rowcount != 1:
        return None

    return db.get(Borrower, borrower_id)

def release_borrower(
    db: Session,
    borrower_id: int,
) -> None:
    db.execute(
        update(Borrower)
        .where(
            Borrower.id == borrower_id,
            Borrower.status == BorrowerStatus.RESERVED,
        )
        .values(
            status=BorrowerStatus.READY,
        )
    )