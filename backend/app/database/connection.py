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

def get_db_engine():
    """Create and return a database engine."""
    # First check environment variable
    db_url = os.environ.get('DATABASE_URL')
    
    # Fall back to Flask app config if available
    if db_url is None and app:
        db_url = app.config.get('DATABASE_URL')
        
    # Finally fall back to default
    if db_url is None:
        db_url = 'sqlite:///dmr_analysis.db'
        
    logger.info(f"Creating database engine with URL: {db_url}")
    logger.debug(f"Current app config: {app.config if app else 'No Flask app'}")
    
    engine = create_engine(db_url)
    return engine

from sqlalchemy.orm import sessionmaker

def get_db_session(engine):
    """Create and return a database session."""
    Session = sessionmaker(bind=engine)
    return Session()

Base = declarative_base()
