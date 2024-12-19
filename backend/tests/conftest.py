import pytest
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from backend.app.database.models import Base, MasterGeneID
from backend.app.database.connection import get_db_engine

def verify_tables(engine):
    """Verify that all required tables exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Created tables: {tables}")
    return tables
@pytest.fixture(scope="session", autouse=True)
def test_env():
    """Configure test environment."""
    # Store original environment
    original_env = dict(os.environ)
    
    # Set test environment
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture(scope="session")
def db_engine(test_env):
    """Create a database engine for testing."""
    # Force in-memory SQLite for tests
    engine = create_engine('sqlite:///:memory:')
    
    # Create master_gene_ids table first
    Base.metadata.create_all(engine)
    
    # Verify tables
    tables = verify_tables(engine)
    if 'master_gene_ids' not in tables:
        raise Exception("master_gene_ids table not created!")
    if 'genes' not in tables:
        raise Exception("genes table not created!")
        
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a new database session for each test function."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def session(db_session):
    """Alias for db_session for backward compatibility."""
    return db_session
