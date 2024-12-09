import pytest
from database.schema import Timepoint, Gene, DMR, Biclique, Component, ComponentBiclique, Statistic, Metadata, Relationship

def test_add_timepoint(db_session):
    """Test adding a timepoint to the database."""
    timepoint = Timepoint(name="test_timepoint", description="Test description")
    db_session.add(timepoint)
    db_session.commit()
    assert timepoint.id is not None

def test_add_gene(db_session):
    """Test adding a gene to the database."""
    gene = Gene(symbol="TEST1", description="Test gene")
    db_session.add(gene)
    db_session.commit()
    assert gene.id is not None

def test_add_dmr(db_session):
    """Test adding a DMR to the database."""
    timepoint = Timepoint(name="test_timepoint")
    db_session.add(timepoint)
    db_session.commit()
    dmr = DMR(dmr_number=1, timepoint=timepoint)
    db_session.add(dmr)
    db_session.commit()
    assert dmr.id is not None

def test_add_biclique(db_session):
    """Test adding a biclique to the database."""
    timepoint = Timepoint(name="test_timepoint")
    db_session.add(timepoint)
    db_session.commit()
    biclique = Biclique(dmr_ids=[1], gene_ids=[1], timepoint=timepoint)
    db_session.add(biclique)
    db_session.commit()
    assert biclique.id is not None

def test_add_component(db_session):
    """Test adding a component to the database."""
    timepoint = Timepoint(name="test_timepoint")
    db_session.add(timepoint)
    db_session.commit()
    component = Component(timepoint=timepoint)
    db_session.add(component)
    db_session.commit()
    assert component.id is not None

def test_add_component_biclique(db_session):
    """Test adding a component-biclique relationship to the database."""
    timepoint = Timepoint(name="test_timepoint")
    db_session.add(timepoint)
    db_session.commit()
    biclique = Biclique(dmr_ids=[1], gene_ids=[1], timepoint=timepoint)
    component = Component(timepoint=timepoint)
    db_session.add_all([biclique, component])
    db_session.commit()
    component_biclique = ComponentBiclique(component=component, biclique=biclique)
    db_session.add(component_biclique)
    db_session.commit()
    assert component_biclique.component_id is not None
    assert component_biclique.biclique_id is not None

def test_add_statistic(db_session):
    """Test adding a statistic to the database."""
    statistic = Statistic(category="test", key="test_key", value="test_value")
    db_session.add(statistic)
    db_session.commit()
    assert statistic.id is not None

def test_add_metadata(db_session):
    """Test adding metadata to the database."""
    gene = Gene(symbol="TEST1")
    db_session.add(gene)
    db_session.commit()
    metadata = Metadata(entity_type="gene", entity=gene, key="test_key", value="test_value")
    db_session.add(metadata)
    db_session.commit()
    assert metadata.id is not None

def test_add_relationship(db_session):
    """Test adding a relationship to the database."""
    gene = Gene(symbol="TEST1")
    dmr = DMR(dmr_number=1)
    db_session.add_all([gene, dmr])
    db_session.commit()
    relationship = Relationship(source_entity_type="gene", source_entity=gene, target_entity_type="dmr", target_entity=dmr, relationship_type="associated")
    db_session.add(relationship)
    db_session.commit()
    assert relationship.id is not None
