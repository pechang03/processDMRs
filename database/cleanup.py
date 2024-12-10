"""Database cleanup operations."""

from sqlalchemy.orm import Session
from .models import (
    ComponentBiclique,
    Relationship, 
    Metadata,
    Statistic,
    Biclique,
    Component,
    DMR,
    Gene,
    Timepoint
)

def clean_database(session: Session):
    """Clean out existing data from all tables."""
    print("Cleaning existing data from database...")
    try:
        # Delete data from all tables in correct order
        session.query(ComponentBiclique).delete()
        session.query(Relationship).delete()
        session.query(Metadata).delete()
        session.query(Statistic).delete()
        session.query(Biclique).delete()
        session.query(Component).delete()
        session.query(DMR).delete()
        session.query(Gene).delete()
        session.query(Timepoint).delete()
        session.commit()
        print("Database cleaned successfully")
    except Exception as e:
        session.rollback()
        print(f"Warning: Error cleaning existing data: {str(e)}")
        raise
