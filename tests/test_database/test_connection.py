"""Tests for database connection handling."""

import os
import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from database.connection import get_db_engine, get_db_session

def test_get_db_engine_default():
    """Test getting database engine with default settings."""
    engine = get_db_engine()
    assert isinstance(engine, Engine)
    assert str(engine.url).startswith('sqlite:///')

def test_get_db_engine_custom_url():
    """Test getting database engine with custom URL."""
    # Set custom URL in environment
    os.environ['DATABASE_URL'] = 'sqlite:///test.db'
    engine = get_db_engine()
    assert isinstance(engine, Engine)
    assert str(engine.url) == 'sqlite:///test.db'
    # Clean up
    os.remove('test.db') if os.path.exists('test.db') else None

def test_get_db_session():
    """Test getting database session."""
    engine = get_db_engine()
    session = get_db_session(engine)
    assert isinstance(session, Session)
    session.close()

@pytest.mark.parametrize("env_file", [
    'sample.env',
    '../sample.env',
    '../../sample.env',
    os.path.join(os.path.dirname(__file__), 'sample.env')
])
def test_env_file_loading(tmp_path, env_file):
    """Test loading environment variables from different locations."""
    # Create temporary sample.env file
    env_content = "DATABASE_URL=sqlite:///custom_test.db"
    env_path = tmp_path / os.path.basename(env_file)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(env_content)
    
    # Temporarily modify environment
    old_env = os.environ.get('DATABASE_URL')
    os.environ.pop('DATABASE_URL', None)
    
    try:
        engine = get_db_engine()
        assert isinstance(engine, Engine)
    finally:
        # Restore environment
        if old_env is not None:
            os.environ['DATABASE_URL'] = old_env
        # Clean up
        if os.path.exists('custom_test.db'):
            os.remove('custom_test.db')

def test_get_db_engine_invalid_url():
    """Test engine creation with invalid URL."""
    os.environ['DATABASE_URL'] = 'invalid://url'
    with pytest.raises(Exception):
        get_db_engine()

@pytest.mark.parametrize("test_url", [
    'sqlite:///:memory:',
    'sqlite:///test_db.sqlite',
])
def test_get_db_engine_different_urls(test_url):
    """Test engine creation with different valid URLs."""
    os.environ['DATABASE_URL'] = test_url
    engine = get_db_engine()
    assert isinstance(engine, Engine)
    assert str(engine.url) == test_url
    
    # Clean up if file database
    if 'test_db.sqlite' in test_url:
        os.remove('test_db.sqlite') if os.path.exists('test_db.sqlite') else None

def test_session_transaction_handling():
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

def test_session_rollback():
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
