"""Database connection handling for DMR analysis system."""

from sqlalchemy import create_engine
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DATABASE_URL')

def get_db_engine():
    """Create and return a database engine."""
    # Try multiple .env locations
    env_files = [
        '.env',  # Root directory
        '../.env',  # One level up
        '../../.env',  # Two levels up
        os.path.join(os.path.dirname(__file__), '.env'),  # Same directory as this file
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            break
            
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        # Provide a default SQLite URL if none specified
        db_url = 'sqlite:///dmr_analysis.db'
        
    if not database_exists(db_url):
        create_database(db_url)

    engine = create_engine(db_url, echo=True)
    return engine

def get_db_session(engine):
    """Create and return a database session."""
    Session = sessionmaker(bind=engine)
    return Session()

Base = declarative_base()
