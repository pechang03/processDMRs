"""Database connection handling for DMR analysis system."""

from sqlalchemy import create_engine
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
import os
import logging
from ..utils.extensions import app

logger = logging.getLogger(__name__)

def get_project_root():
    """Get the project root directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up from backend/app/database to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    return project_root

def get_db_engine():
    """Create and return a database engine.
    
    The database URL is determined in the following order:
    1. DATABASE_URL environment variable
    2. Flask app configuration
    3. Default SQLite database in project root
    """
    # First check environment variable
    db_url = os.environ.get('DATABASE_URL')
    logger.debug(f"Environment DATABASE_URL: {db_url}")
    
    # Fall back to Flask app config if available
    if db_url is None and app:
        try:
            db_url = app.config.get('DATABASE_URL')
            logger.debug(f"Flask config DATABASE_URL: {db_url}")
        except Exception as e:
            logger.warning(f"Failed to get Flask config: {e}")
            
    # Finally fall back to default
    if db_url is None:
        db_path = os.path.join(get_project_root(), "dmr_analysis.db")
        db_url = f'sqlite:///{db_path}'
        logger.debug(f"Using default database path: {db_path}")
        
    logger.info(f"Creating database engine with URL: {db_url}")
    
    engine = create_engine(db_url)
    return engine

from sqlalchemy.orm import sessionmaker

def get_db_session(engine):
    """Create and return a database session."""
    Session = sessionmaker(bind=engine)
    return Session()

Base = declarative_base()
