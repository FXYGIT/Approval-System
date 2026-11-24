from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction(session: Session):
    # Authentication may already have begun a read transaction on this request's Session.
    # The service owns its commit/rollback; repositories and dependencies never commit.
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise
