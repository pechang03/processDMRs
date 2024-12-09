import pytest
from database.connection import get_db_engine, get_db_session

def test_get_db_engine():
    """Test that we can get a database engine."""
    engine = get_db_engine()
    assert engine is not None

def test_get_db_session(db_engine):
    """Test that we can get a database session."""
    session = get_db_session(db_engine)
    assert session is not None
    session.close()
