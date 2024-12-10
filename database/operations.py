"""Core database operations for DMR analysis system."""

from typing import Set, Dict, List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func
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
    MasterGeneID,
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


from .models import TriconnectedComponent

def insert_triconnected_component(
    session: Session,
    timepoint_id: int,
    size: int,
    dmr_count: int,
    gene_count: int,
    edge_count: int,
    density: float,
    category: str,
    separation_pairs: List[Tuple[int, int]],
    nodes: List[int],
) -> int:
    """Insert a new triconnected component into the database."""
    component = TriconnectedComponent(
        timepoint_id=timepoint_id,
        size=size,
        dmr_count=dmr_count,
        gene_count=gene_count,
        edge_count=edge_count,
        density=density,
        category=category,
        separation_pairs=separation_pairs,
        nodes=nodes,
    )
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
    # Skip invalid gene symbols
    if not symbol:  # Handle None or empty string
        return None

    # Clean and lowercase the symbol
    symbol = str(symbol).strip().lower()

    # Extended validation for unnamed columns and invalid symbols
    invalid_patterns = ["unnamed:", "nan", ".", "n/a", ""]
    if any(symbol.startswith(pat) for pat in invalid_patterns) or not symbol:
        return None  # Skip invalid symbols instead of raising error

    # Check for duplicate gene symbols (case-insensitive)
    existing_gene = session.query(Gene).filter(func.lower(Gene.symbol) == symbol).first()
    if existing_gene:
        return existing_gene.id

    try:
        # Create or get MasterGeneID if master_gene_id is provided
        if master_gene_id is not None:
            # Try to get existing master gene ID (case-insensitive)
            master_gene = (
                session.query(MasterGeneID)
                .filter(func.lower(MasterGeneID.gene_symbol) == symbol.lower())
                .first()
            )
        
            if master_gene:
                master_gene_id = master_gene.id
            else:
                # Create new master gene ID
                master_gene = MasterGeneID(id=master_gene_id, gene_symbol=symbol)
                session.add(master_gene)
                try:
                    session.flush()
                except Exception as e:
                    session.rollback()
                    print(f"Error creating master gene ID for {symbol}: {str(e)}")
                    return None

        # Create the gene
        gene = Gene(
            symbol=symbol,
            description=description,
            master_gene_id=master_gene_id,
            node_type="regular_gene",
            degree=0,
            is_hub=False,
        )
        session.add(gene)
        try:
            session.commit()
            return gene.id
        except Exception as e:
            session.rollback()
            raise ValueError(f"Error creating gene: {str(e)}")

    except Exception as e:
        session.rollback()
        raise ValueError(f"Error inserting gene {symbol}: {str(e)}")


def update_gene_metadata(
    session: Session,
    gene_symbol: str,
    timepoint: str,
    degree: int = None,
    node_type: str = None,
    is_hub: bool = None,
):
    """Update gene metadata for a specific timepoint."""
    gene = (
        session.query(Gene)
        .filter(func.lower(Gene.symbol) == gene_symbol.lower())
        .first()
    )
    if gene:
        if degree is not None:
            gene.degree = max(
                gene.degree, degree
            )  # Keep highest degree across timepoints
        if node_type:
            if node_type == "split_gene":  # Once split, always split
                gene.node_type = "split_gene"
        if is_hub is not None:
            gene.is_hub = gene.is_hub or is_hub  # True if hub in any timepoint
        session.commit()


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


def update_gene_hub_status(
    session: Session,
    timepoint: str,
    dominating_set: Set[int],
    gene_id_mapping: Dict[str, int],
):
    """Update hub status for genes in dominating set."""
    reverse_mapping = {v: k for k, v in gene_id_mapping.items()}

    for gene_id in dominating_set:
        if gene_id in reverse_mapping:
            gene_symbol = reverse_mapping[gene_id]
            update_gene_metadata(session, gene_symbol, timepoint, is_hub=True)
