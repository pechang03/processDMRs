"""Database connection handling for DMR analysis system."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DATABASE_URL')

def get_db_engine():
    """Create and return a database engine."""
    if not DB_URL:
        raise ValueError("DATABASE_URL environment variable not set")

    if not database_exists(DB_URL):
        create_database(DB_URL)

    engine = create_engine(DB_URL, echo=True)
    return engine

def get_db_session(engine):
    """Create and return a database session."""
    Session = sessionmaker(bind=engine)
    return Session()

Base = declarative_base()
