"""Tests for database connection handling."""

import os
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db_engine, get_db_session

@pytest.fixture
def test_env(tmp_path):
    """Setup test environment with database configuration."""
    env_path = tmp_path / "test_processDMR.env"
    env_content = "DATABASE_URL=sqlite:///:memory:"
    env_path.write_text(env_content)
    
    # Store original env var
    original_env = dict(os.environ)
    
    # Set up test environment
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

def test_get_db_engine_default(test_env):
    """Test getting database engine with default settings."""
    engine = get_db_engine()
    assert isinstance(engine, Engine)
    assert str(engine.url) == 'sqlite:///:memory:'

def test_get_db_session(test_env):
    """Test getting database session."""
    engine = get_db_engine()
    session = get_db_session(engine)
    assert isinstance(session, Session)
    session.close()

def test_get_db_engine_invalid_url(test_env):
    """Test engine creation with invalid URL."""
    os.environ['DATABASE_URL'] = 'invalid://url'
    with pytest.raises(Exception):
        get_db_engine()

def test_session_transaction_handling(test_env):
    """Test session transaction handling."""
    engine = get_db_engine()
    session = get_db_session(engine)
    
    try:
        # Start transaction
        session.begin()
        # Simulate some database operations
        from sqlalchemy import text
        session.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)"))
        session.execute(text("INSERT INTO test (id) VALUES (1)"))
        # Commit transaction
        session.commit()
        
        # Verify data was committed
        result = session.execute(text("SELECT * FROM test")).fetchall()
        assert len(result) == 1
        assert result[0][0] == 1
        
    finally:
        # Clean up
        session.execute(text("DROP TABLE IF EXISTS test"))
        session.commit()
        session.close()

def test_session_rollback(test_env):
    """Test session rollback functionality."""
    engine = get_db_engine()
    session = get_db_session(engine)
    
    from sqlalchemy import text
    # Create test table
    session.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)"))
    session.commit()
    
    try:
        # Start transaction
        session.begin()
        # Insert data
        session.execute(text("INSERT INTO test (id) VALUES (1)"))
        # Rollback transaction
        session.rollback()
        
        # Verify data was not committed
        result = session.execute(text("SELECT * FROM test")).fetchall()
        assert len(result) == 0
        
    finally:
        # Clean up
        session.execute(text("DROP TABLE IF EXISTS test"))
        session.commit()
        session.close()
