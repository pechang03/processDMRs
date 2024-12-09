"""Core database operations for DMR analysis system."""

from sqlalchemy.orm import Session
from .models import (
    Timepoint,
    Gene,
    DMR,
    Biclique,
    Component,
    ComponentBiclique,
    Statistic,
    Metadata,
    Relationship,
)


def insert_timepoint(session: Session, name: str, description: str = None):
    """Insert a new timepoint into the database."""
    timepoint = Timepoint(name=name, description=description)
    session.add(timepoint)
    session.commit()
    return timepoint.id


def insert_dmr(session: Session, timepoint_id: int, dmr_number: int, **kwargs):
    """Insert a new DMR into the database."""
    dmr = DMR(timepoint_id=timepoint_id, dmr_number=dmr_number, **kwargs)
    session.add(dmr)
    session.commit()
    return dmr.id


def insert_biclique(
    session: Session,
    timepoint_id: int,
    component_id: int,
    dmr_ids: list,
    gene_ids: list,
):
    """Insert a new biclique into the database."""
    biclique = Biclique(
        timepoint_id=timepoint_id,
        component_id=component_id,
        dmr_ids=dmr_ids,
        gene_ids=gene_ids,
    )
    session.add(biclique)
    session.commit()
    return biclique.id


def insert_component(session: Session, timepoint_id: int, **kwargs):
    """Insert a new component into the database."""
    component = Component(timepoint_id=timepoint_id, **kwargs)
    session.add(component)
    session.commit()
    return component.id


def insert_component_biclique(session: Session, component_id: int, biclique_id: int):
    """Insert a relationship between a component and a biclique."""
    comp_biclique = ComponentBiclique(
        component_id=component_id, biclique_id=biclique_id
    )
    session.add(comp_biclique)
    session.commit()


def insert_statistics(session: Session, category: str, key: str, value: str):
    """Insert new statistics into the database."""
    stat = Statistic(category=category, key=key, value=value)
    session.add(stat)
    session.commit()


def insert_metadata(
    session: Session, entity_type: str, entity_id: int, key: str, value: str
):
    """Insert new metadata into the database."""
    meta = Metadata(entity_type=entity_type, entity_id=entity_id, key=key, value=value)
    session.add(meta)
    session.commit()


def insert_relationship(
    session: Session,
    source_type: str,
    source_id: int,
    target_type: str,
    target_id: int,
    relationship_type: str,
):
    """Insert a new relationship into the database."""
    rel = Relationship(
        source_entity_type=source_type,
        source_entity_id=source_id,
        target_entity_type=target_type,
        target_entity_id=target_id,
        relationship_type=relationship_type,
    )
    session.add(rel)
    session.commit()


def insert_gene(
    session: Session, symbol: str, description: str = None, master_gene_id: int = None
):
    """Insert a new gene into the database."""
    # Check for duplicate gene symbols
    existing_gene = session.query(Gene).filter_by(symbol=symbol).first()
    if existing_gene:
        return existing_gene.id

    # Validate master_gene_id if provided
    if master_gene_id is not None:
        if not session.query(MasterGeneID).filter_by(id=master_gene_id).first():
            raise ValueError(f"Invalid master_gene_id: {master_gene_id}")

    gene = Gene(symbol=symbol, description=description, master_gene_id=master_gene_id)
    session.add(gene)
    session.commit()
    return gene.id


def get_or_create_gene(
    session: Session, symbol: str, description: str = None, master_gene_id: int = None
) -> int:
    """Get an existing gene or create a new one if it doesn't exist."""
    gene = session.query(Gene).filter_by(symbol=symbol).first()
    if gene:
        return gene.id
    else:
        return insert_gene(session, symbol, description, master_gene_id)


# Query functions
def query_timepoints(session: Session):
    """Query all timepoints."""
    return session.query(Timepoint).all()


def query_genes(session: Session):
    """Query all genes."""
    return session.query(Gene).all()


def query_dmrs(session: Session):
    """Query all DMRs."""
    return session.query(DMR).all()


def query_bicliques(session: Session):
    """Query all bicliques."""
    return session.query(Biclique).all()


def query_components(session: Session):
    """Query all components."""
    return session.query(Component).all()


def query_statistics(session: Session):
    """Query all statistics."""
    return session.query(Statistic).all()


def query_metadata(session: Session):
    """Query all metadata."""
    return session.query(Metadata).all()


def query_relationships(session: Session):
    """Query all relationships."""
    return session.query(Relationship).all()
