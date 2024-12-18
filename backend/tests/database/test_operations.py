"""Tests for database operations."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import networkx as nx
from backend.app.database.models import (
    Base,
    Gene,
    DMR,
    Timepoint,
    GeneTimepointAnnotation,
    DMRTimepointAnnotation,
    MasterGeneID,
)
from backend.app.database.operations import (
    get_or_create_timepoint,
    insert_gene,
    upsert_gene_timepoint_annotation,
    upsert_dmr_timepoint_annotation,
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


@pytest.fixture(scope="function")
def timepoint(session):
    """Create a test timepoint."""
    timepoint = Timepoint(
        name="test_timepoint",
        sheet_name="test_sheet_TSS",
        description="Test Description",
    )
    session.add(timepoint)
    session.commit()
    return timepoint.id  # Return the ID instead of the object


def test_get_or_create_timepoint(session):
    """Test creating and retrieving a timepoint."""
    # Create new timepoint
    timepoint_id = get_or_create_timepoint(
        session,
        "test",
        sheet_name="test_sheet",
        description="Test Description",
        dmr_id_offset=1000,
    )
    assert timepoint_id is not None

    # Retrieve existing timepoint
    same_id = get_or_create_timepoint(session, "test", sheet_name="test_sheet")
    assert same_id == timepoint_id

    # Verify timepoint in database
    timepoint = session.query(Timepoint).filter_by(name="test").first()
    assert timepoint.description == "Test Description"
    assert timepoint.dmr_id_offset == 1000


@pytest.fixture(scope="function")
def master_gene(session):
    """Create a test master gene entry."""
    master_gene = MasterGeneID(id=100001, gene_symbol="TEST_GENE")
    session.add(master_gene)
    session.commit()
    return master_gene


def test_insert_gene(session):
    """Test inserting genes with various cases."""
    import os

    os.environ["START_GENE_ID"] = "100000"  # Set start ID for testing

    # Test valid gene with master_gene_id
    gene_id = insert_gene(session, "GENE1", "Test Gene", master_gene_id=100001)
    assert gene_id is not None
    assert gene_id >= 100000  # Verify ID is at least START_GENE_ID

    # Test duplicate gene (case insensitive)
    dup_id = insert_gene(session, "gene1", "Duplicate Gene", master_gene_id=100001)
    assert dup_id == gene_id

    # Test invalid gene symbols
    assert insert_gene(session, "") is None
    assert insert_gene(session, "unnamed:1") is None
    assert insert_gene(session, "nan") is None
    assert insert_gene(session, ".") is None


def test_upsert_gene_timepoint_annotation_biclique_dedup(
    session, timepoint, master_gene
):
    """Test deduplication of biclique IDs in gene annotations."""
    # Create a test gene
    gene_id = insert_gene(session, "TEST_GENE", master_gene_id=master_gene.id)
    assert gene_id is not None

    # First annotation with duplicate biclique IDs
    upsert_gene_timepoint_annotation(
        session, timepoint_id=timepoint, gene_id=gene_id, biclique_ids="0,0,1,1"
    )

    # Verify deduplication
    annotation = session.query(GeneTimepointAnnotation).first()
    assert annotation is not None
    assert annotation.biclique_ids == "0,1"


def test_upsert_dmr_timepoint_annotation_biclique_dedup(session, timepoint):
    """Test deduplication of biclique IDs in DMR annotations."""
    # Create test DMR
    dmr = DMR(timepoint_id=timepoint, dmr_number=1)
    session.add(dmr)
    session.commit()

    # First insertion with duplicate biclique IDs
    upsert_dmr_timepoint_annotation(
        session, timepoint_id=timepoint, dmr_id=dmr.id, biclique_ids="0,0,1,1"
    )

    # Verify deduplication
    annotation = session.query(DMRTimepointAnnotation).first()
    assert annotation.biclique_ids == "0,1"

    # Add more biclique IDs with duplicates
    upsert_dmr_timepoint_annotation(
        session, timepoint_id=timepoint, dmr_id=dmr.id, biclique_ids="1,2,2,3"
    )

    # Verify merged and deduplicated
    annotation = session.query(DMRTimepointAnnotation).first()
    assert annotation.biclique_ids == "0,1,2,3"


def test_upsert_annotations_with_component_info(session, timepoint):
    """Test updating annotations with component information."""
    # First create a master gene ID entry
    from backend.app.database.models import MasterGeneID

    master_gene = MasterGeneID(id=100001, gene_symbol="TEST_GENE")
    session.add(master_gene)
    session.commit()

    # Create a valid gene
    gene_id = insert_gene(session, "TEST_GENE", master_gene_id=master_gene.id)
    assert gene_id is not None

    # Test gene annotation
    upsert_gene_timepoint_annotation(
        session,
        timepoint_id=timepoint,
        gene_id=gene_id,
        component_id=1,
        degree=3,
        node_type="split_gene",
        gene_type="Nearby",
        is_isolate=False,
    )

    # Verify annotation
    gene_annot = session.query(GeneTimepointAnnotation).first()
    assert gene_annot is not None
    assert gene_annot.component_id == 1
    assert gene_annot.degree == 3
    assert gene_annot.node_type == "split_gene"
    assert gene_annot.gene_type == "Nearby"
    assert not gene_annot.is_isolate
