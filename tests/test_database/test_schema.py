"""Tests for database schema/models."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from database.models import (
    Base, Timepoint, Gene, DMR, Biclique, Component,
    ComponentBiclique, Statistic, Metadata, Relationship,
    MasterGeneID, GeneTimepointAnnotation, DMRTimepointAnnotation,
    TriconnectedComponent
)

@pytest.fixture(scope="function")
def engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def session(engine):
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

def test_table_creation(engine):
    """Test that all expected tables are created."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = {
        'timepoints',
        'genes',
        'dmrs',
        'bicliques',
        'components',
        'component_bicliques',
        'statistics',
        'metadata',
        'relationships',
        'master_gene_ids',
        'gene_timepoint_annotations',
        'dmr_timepoint_annotations',
        'triconnected_components'
    }
    
    assert set(tables) == expected_tables

def test_timepoint_schema(engine):
    """Test Timepoint table schema."""
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('timepoints')}
    
    assert 'id' in columns
    assert 'name' in columns
    assert 'description' in columns
    assert 'dmr_id_offset' in columns
    
    assert columns['name']['nullable'] is False
    assert columns['dmr_id_offset']['nullable'] is True

def test_gene_schema(engine):
    """Test Gene table schema."""
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('genes')}
    
    assert 'id' in columns
    assert 'symbol' in columns
    assert 'description' in columns
    assert 'master_gene_id' in columns
    assert 'interaction_source' in columns
    assert 'promoter_info' in columns
    
    assert columns['symbol']['nullable'] is False

def test_dmr_schema(engine):
    """Test DMR table schema."""
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('dmrs')}
    
    assert 'id' in columns
    assert 'timepoint_id' in columns
    assert 'dmr_number' in columns
    assert 'area_stat' in columns
    assert 'description' in columns
    assert 'chromosome' in columns
    assert 'start_position' in columns
    assert 'end_position' in columns
    
    assert columns['dmr_number']['nullable'] is False

def test_biclique_schema(engine):
    """Test Biclique table schema."""
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('bicliques')}
    
    assert 'id' in columns
    assert 'timepoint_id' in columns
    assert 'component_id' in columns
    assert 'dmr_ids' in columns
    assert 'gene_ids' in columns
    assert 'category' in columns

def test_foreign_key_constraints(engine):
    """Test that foreign key constraints are properly set up."""
    inspector = inspect(engine)
    
    # Test ComponentBiclique foreign keys
    fkeys = inspector.get_foreign_keys('component_bicliques')
    fkey_cols = {fk['referred_columns'][0] for fk in fkeys}
    assert 'id' in fkey_cols  # Should reference both component.id and biclique.id
    
    # Test Gene foreign keys
    fkeys = inspector.get_foreign_keys('genes')
    fkey_cols = {fk['referred_columns'][0] for fk in fkeys}
    assert 'id' in fkey_cols  # Should reference master_gene_ids.id

def test_unique_constraints(engine):
    """Test that unique constraints are properly set up."""
    inspector = inspect(engine)
    
    # Test Timepoint unique constraint
    unique_constraints = inspector.get_unique_constraints('timepoints')
    assert any(constraint['column_names'] == ['name'] 
              for constraint in unique_constraints)
    
    # Test DMR unique constraint
    unique_constraints = inspector.get_unique_constraints('dmrs')
    assert any('timepoint_id' in constraint['column_names'] 
              and 'dmr_number' in constraint['column_names']
              for constraint in unique_constraints)

def test_relationship_creation(session):
    """Test creating related records."""
    # Create a timepoint
    timepoint = Timepoint(name="test_timepoint", description="Test Description")
    session.add(timepoint)
    session.flush()
    
    # Create a component
    component = Component(
        timepoint_id=timepoint.id,
        graph_type='original',
        size=5,
        dmr_count=2,
        gene_count=3
    )
    session.add(component)
    session.flush()
    
    # Create a biclique
    biclique = Biclique(
        timepoint_id=timepoint.id,
        component_id=component.id,
        dmr_ids=[1, 2],
        gene_ids=[1, 2, 3]
    )
    session.add(biclique)
    session.flush()
    
    # Create component-biclique relationship
    comp_biclique = ComponentBiclique(
        timepoint_id=timepoint.id,
        component_id=component.id,
        biclique_id=biclique.id
    )
    session.add(comp_biclique)
    session.commit()
    
    # Test relationships
    assert biclique.component_id == component.id
    assert biclique.timepoint_id == timepoint.id
    loaded_comp_biclique = session.query(ComponentBiclique).first()
    assert loaded_comp_biclique.component_id == component.id
    assert loaded_comp_biclique.biclique_id == biclique.id

def test_array_type_handling(session):
    """Test handling of array types in models."""
    # Create a biclique with array data
    timepoint = Timepoint(name="test_timepoint")
    session.add(timepoint)
    session.flush()
    
    biclique = Biclique(
        timepoint_id=timepoint.id,
        dmr_ids=[1, 2, 3],
        gene_ids=[4, 5, 6]
    )
    session.add(biclique)
    session.commit()
    
    # Retrieve and verify array data
    loaded_biclique = session.query(Biclique).first()
    assert loaded_biclique.dmr_ids == [1, 2, 3]
    assert loaded_biclique.gene_ids == [4, 5, 6]

def test_cascade_behavior(session):
    """Test cascade behavior on delete."""
    # Create related records
    timepoint = Timepoint(name="test_timepoint")
    session.add(timepoint)
    session.flush()
    
    component = Component(
        timepoint_id=timepoint.id,
        graph_type='original'
    )
    session.add(component)
    session.flush()
    
    biclique = Biclique(
        timepoint_id=timepoint.id,
        component_id=component.id
    )
    session.add(biclique)
    session.commit()
    
    # Delete timepoint and verify cascading deletes
    session.delete(timepoint)
    session.commit()
    
    assert session.query(Component).count() == 0
    assert session.query(Biclique).count() == 0
