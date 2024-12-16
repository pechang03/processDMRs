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
        'triconnected_components',
        'dominating_sets'
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

def test_master_gene_id_schema(engine):
    """Test MasterGeneID table schema and case-insensitive index."""
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('master_gene_ids')}
    
    assert 'id' in columns
    assert 'gene_symbol' in columns
    assert columns['gene_symbol']['nullable'] is False
    
    # Check for case-insensitive index using sqlite_master
    with engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='index' AND name='ix_master_gene_ids_gene_symbol_lower'")
        ).scalar()

        assert result is not None, "Case-insensitive index not found"
        assert 'lower' in result.lower(), "Index is not case-insensitive"

def test_annotation_schemas(engine):
    """Test gene and DMR annotation table schemas."""
    inspector = inspect(engine)
    
    # Test gene annotation columns
    gene_cols = {col['name']: col for col in inspector.get_columns('gene_timepoint_annotations')}
    assert all(col in gene_cols for col in [
        'timepoint_id', 'gene_id', 'component_id', 'triconnected_id',
        'degree', 'node_type', 'gene_type', 'is_isolate', 'biclique_ids'
    ])
    
    # Test DMR annotation columns
    dmr_cols = {col['name']: col for col in inspector.get_columns('dmr_timepoint_annotations')}
    assert all(col in dmr_cols for col in [
        'timepoint_id', 'dmr_id', 'component_id', 'triconnected_id',
        'degree', 'node_type', 'is_isolate', 'biclique_ids'
    ])

def test_triconnected_component_schema(engine):
    """Test TriconnectedComponent table schema."""
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns('triconnected_components')}
    
    # Check required columns
    required_columns = {
        'id', 'timepoint_id', 'component_id', 'dmr_ids', 'gene_ids',
        'category', 'size', 'dmr_count', 'gene_count', 'edge_count',
        'density', 'nodes', 'separation_pairs', 'avg_dmrs', 'avg_genes'
    }
    assert all(col in columns for col in required_columns)

def test_component_relationships(session):
    """Test relationships between components and other entities."""
    # Create test data
    timepoint = Timepoint(name="test_timepoint")
    session.add(timepoint)
    session.flush()
    
    # Create original component
    orig_component = Component(
        timepoint_id=timepoint.id,
        graph_type='original',
        size=5,
        dmr_count=2,
        gene_count=3
    )
    session.add(orig_component)
    
    # Create split component
    split_component = Component(
        timepoint_id=timepoint.id,
        graph_type='split',
        size=7,
        dmr_count=3,
        gene_count=4
    )
    session.add(split_component)
    session.flush()
    
    # Create bicliques for split component
    biclique1 = Biclique(
        timepoint_id=timepoint.id,
        component_id=split_component.id,
        dmr_ids=[1, 2],
        gene_ids=[1, 2]
    )
    biclique2 = Biclique(
        timepoint_id=timepoint.id,
        component_id=split_component.id,
        dmr_ids=[2, 3],
        gene_ids=[3, 4]
    )
    session.add_all([biclique1, biclique2])
    session.flush()
    
    # Test relationships
    assert len(split_component.bicliques) == 2
    assert all(b.component_id == split_component.id for b in split_component.bicliques)
    assert len(orig_component.bicliques) == 0

def test_annotation_relationships(session):
    """Test relationships between annotations and their related entities."""
    # Create base data
    timepoint = Timepoint(name="test_timepoint")
    session.add(timepoint)
    session.flush()
    
    # Create gene and DMR
    gene = Gene(symbol="TEST1")
    dmr = DMR(timepoint_id=timepoint.id, dmr_number=1)
    session.add_all([gene, dmr])
    session.flush()
    
    # Create annotations
    gene_annotation = GeneTimepointAnnotation(
        timepoint_id=timepoint.id,
        gene_id=gene.id,
        degree=3,
        node_type='regular_gene',
        gene_type='Nearby',
        is_isolate=False,
        biclique_ids="1,2,3"
    )
    
    dmr_annotation = DMRTimepointAnnotation(
        timepoint_id=timepoint.id,
        dmr_id=dmr.id,
        degree=2,
        node_type='regular',
        is_isolate=False,
        biclique_ids="1,2"
    )
    
    session.add_all([gene_annotation, dmr_annotation])
    session.commit()
    
    # Test retrieval and relationships
    loaded_gene_annot = session.query(GeneTimepointAnnotation).first()
    assert loaded_gene_annot.gene_id == gene.id
    assert loaded_gene_annot.degree == 3
    assert loaded_gene_annot.biclique_ids == "1,2,3"
    
    loaded_dmr_annot = session.query(DMRTimepointAnnotation).first()
    assert loaded_dmr_annot.dmr_id == dmr.id
    assert loaded_dmr_annot.degree == 2
    assert loaded_dmr_annot.biclique_ids == "1,2"

def test_metadata_and_statistics(session):
    """Test metadata and statistics tables."""
    # Create test data
    timepoint = Timepoint(name="test_timepoint")
    session.add(timepoint)
    session.flush()
    
    # Add statistics
    stat1 = Statistic(
        category="graph_metrics",
        key="total_nodes",
        value="100"
    )
    stat2 = Statistic(
        category="component_metrics",
        key="avg_size",
        value="5.5"
    )
    session.add_all([stat1, stat2])
    
    # Add metadata
    meta1 = Metadata(
        entity_type="biclique",
        entity_id=1,
        key="density",
        value="0.75"
    )
    meta2 = Metadata(
        entity_type="component",
        entity_id=1,
        key="classification",
        value="complex"
    )
    session.add_all([meta1, meta2])
    session.commit()
    
    # Test queries
    graph_stats = session.query(Statistic).filter_by(category="graph_metrics").all()
    assert len(graph_stats) == 1
    assert graph_stats[0].value == "100"
    
    biclique_meta = session.query(Metadata).filter_by(entity_type="biclique").all()
    assert len(biclique_meta) == 1
    assert biclique_meta[0].value == "0.75"
