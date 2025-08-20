# tests/conftest.py
import pytest
from medfabric.db.database import SessionLocal, Base, engine


@pytest.fixture
def session():
    # Make sure tables exist (only once per test run)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
