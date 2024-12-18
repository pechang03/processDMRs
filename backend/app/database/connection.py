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
    # Get database URL from Flask app config
    db_url = app.config.get('DATABASE_URL', 'sqlite:///dmr_analysis.db')
    logger.info(f"Creating database engine with URL: {db_url}")
    logger.debug(f"Current app config: {app.config}")
    
    # For SQLite, we don't need to check if database exists
    engine = create_engine(db_url)
    return engine

from sqlalchemy.orm import sessionmaker

def get_db_session(engine):
    """Create and return a database session."""
    Session = sessionmaker(bind=engine)
    return Session()

Base = declarative_base()
