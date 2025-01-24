"""Database cleanup operations."""

from sqlalchemy.orm import Session
from .models import Base
from .models import (
    DMR,
    Gene,
    Timepoint,
    MasterGeneID,
    ComponentBiclique,
    Relationship,
    Metadata,
    Statistic,
    Biclique,
    Component,
    TriconnectedComponent,
    DMRTimepointAnnotation,
    GeneTimepointAnnotation,
)


def clean_edge_details(session: Session):
    """Clean edge details table."""
    try:
        session.query(EdgeDetails).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error cleaning edge details: {str(e)}")
        raise

def clean_database(session: Session):
    """Clean out existing data from all tables."""
    print("Cleaning existing data from database...")
    try:
        clean_edge_details(session)
        # Drop all tables
        Base.metadata.drop_all(session.bind)
        # Recreate all tables
        Base.metadata.create_all(session.bind)
        session.commit()
        print("Database cleaned and recreated successfully")
    except Exception as e:
        session.rollback()
        print(f"Warning: Error cleaning database: {str(e)}")
        raise
