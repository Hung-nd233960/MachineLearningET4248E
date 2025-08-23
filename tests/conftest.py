import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from medfabric.db.models import Base


@pytest.fixture
def db_session(postgresql):
    """Create a fresh DB and session per test."""
    # Build SQLAlchemy URL from the fixture info
    user = postgresql.info.user
    password = postgresql.info.password or ""
    host = postgresql.info.host
    port = postgresql.info.port
    dbname = postgresql.info.dbname

    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_engine(url, echo=False)

    Base.metadata.create_all(engine)  # create tables

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
