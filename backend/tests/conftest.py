import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database.models import Base
from backend.app.database.connection import get_db_engine

@pytest.fixture(scope="session")
def db_engine():
    """Create a database engine for testing."""
    engine = get_db_engine()
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for each test function."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    timepoint = Timepoint(name="test_timepoint", sheet_name="test_timepoint_TSS", description="Test Description")
    session.add(timepoint)
    session.commit()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
