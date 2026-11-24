from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import database_url

engine = create_engine(
    database_url(),
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"connect_timeout": 5, "read_timeout": 5},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session():
    with SessionLocal() as session:
        yield session
