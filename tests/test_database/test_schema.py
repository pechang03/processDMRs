import pytest
from sqlalchemy import inspect
from database.schema import Base, Timepoint, Gene, DMR, Biclique, Component, ComponentBiclique, Statistic, Metadata, Relationship

@pytest.mark.parametrize("table", [
    Timepoint, Gene, DMR, Biclique, Component, ComponentBiclique, Statistic, Metadata, Relationship
])
def test_table_creation(db_engine, table):
    """Test that all tables are created in the database."""
    inspector = inspect(db_engine)
    assert inspector.has_table(table.__tablename__)

def test_relationships(db_session):
    """Test relationships between tables."""
    # Create test data
    timepoint = Timepoint(name="test_timepoint")
    gene = Gene(symbol="test_gene")
    dmr = DMR(dmr_number=1, timepoint=timepoint)
    biclique = Biclique(dmr_ids=[1], gene_ids=[1], timepoint=timepoint)
    component = Component(timepoint=timepoint)
    component_biclique = ComponentBiclique(component=component, biclique=biclique)
    statistic = Statistic(category="test", key="test_key", value="test_value")
    metadata = Metadata(entity_type="gene", entity=gene, key="test_key", value="test_value")
    relationship = Relationship(source_entity_type="gene", source_entity=gene, target_entity_type="dmr", target_entity=dmr, relationship_type="associated")

    # Add to session and commit
    db_session.add_all([timepoint, gene, dmr, biclique, component, component_biclique, statistic, metadata, relationship])
    db_session.commit()

    # Check relationships
    assert gene.master_gene_id == dmr.master_gene_id
    assert biclique.timepoint == timepoint
    assert component_biclique.component == component
    assert component_biclique.biclique == biclique
    assert metadata.entity == gene
    assert relationship.source_entity == gene
    assert relationship.target_entity == dmr
