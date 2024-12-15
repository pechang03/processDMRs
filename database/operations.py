"""Core database operations for DMR analysis system."""

from typing import Set, Dict, List, Tuple
import pandas as pd

# from utils import node_info, edge_info

from sqlalchemy import and_, func
from .models import GeneTimepointAnnotation, DMRTimepointAnnotation
from .models import TriconnectedComponent
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
from utils.node_info import NodeInfo


def get_or_create_timepoint(
    session: Session, name: str, description: str = None
) -> int:
    """Get existing timepoint or create if it doesn't exist."""
    timepoint = session.query(Timepoint).filter_by(name=name).first()
    if timepoint:
        return timepoint.id
    new_timepoint = Timepoint(name=name, description=description)
    session.add(new_timepoint)
    session.commit()
    return new_timepoint.id


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
    from biclique_analysis.classifier import classify_biclique

    # Classify the biclique
    category = classify_biclique(set(dmr_ids), set(gene_ids))

    biclique = Biclique(
        timepoint_id=timepoint_id,
        component_id=component_id,
        dmr_ids=dmr_ids,
        gene_ids=gene_ids,
        category=category.name.lower(),  # Add category
    )
    session.add(biclique)
    session.commit()
    return biclique.id


def insert_component(
    session: Session, 
    timepoint_id: int, 
    graph_type: str,
    category: str = None,
    size: int = None,
    dmr_count: int = None,
    gene_count: int = None,
    edge_count: int = None,
    density: float = None,
    encoding: str = None
) -> int:
    """Insert a new component into the database."""
    try:
        # Get the next available ID
        max_id = session.query(func.max(Component.id)).scalar()
        next_id = 1 if max_id is None else max_id + 1
        
        component = Component(
            id=next_id,  # Explicitly set the ID
            timepoint_id=timepoint_id,
            graph_type=graph_type,
            category=category,
            size=size,
            dmr_count=dmr_count,
            gene_count=gene_count,
            edge_count=edge_count,
            density=density,
            endcoding=encoding
        )
        session.add(component)
        session.commit()
        return component.id
    except Exception as e:
        session.rollback()
        print(f"Error inserting component: {str(e)}")
        raise


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
    avg_dmrs: float = None,
    avg_genes: float = None,
    is_simple: bool = None,
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
        avg_dmrs=avg_dmrs,
        avg_genes=avg_genes,
        is_simple=is_simple,
    )
    session.add(component)
    session.commit()
    return component.id


def update_biclique_category(
    session: Session, biclique_id: int, dmr_ids: List[int], gene_ids: List[int]
) -> None:
    """
    Update the category field for a biclique based on its composition.

    Args:
        session: Database session
        biclique_id: ID of the biclique to update
        dmr_ids: List of DMR IDs in the biclique
        gene_ids: List of gene IDs in the biclique
    """
    from biclique_analysis.classifier import classify_biclique, BicliqueSizeCategory

    # Get the biclique
    biclique = session.query(Biclique).get(biclique_id)
    if not biclique:
        return

    # Classify the biclique
    category = classify_biclique(set(dmr_ids), set(gene_ids))

    # Update the category
    biclique.category = category.name.lower()
    session.commit()


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
    session: Session,
    symbol: str,
    description: str = None,
    master_gene_id: int = None,
    interaction_source: str = None,
    promoter_info: str = None,
):
    """Insert a new gene into the database."""
    # Skip invalid gene symbols
    if not symbol:  # Handle None or empty string
        return None

    # Clean and lowercase the symbol
    symbol = str(symbol).strip().lower()

    # Extended validation for unnamed columns and invalid symbols
    # invalid_patterns = ["unnamed:", "nan", ".", "n/a", ""] TODO check unnamed is invalid
    invalid_patterns = ["unnamed:", "nan", ".", "n/a", ""]
    if any(symbol.startswith(pat) for pat in invalid_patterns) or not symbol:
        return None  # Skip invalid symbols instead of raising error

    # Check for duplicate gene symbols (case-insensitive)
    existing_gene = (
        session.query(Gene).filter(func.lower(Gene.symbol) == symbol).first()
    )
    if existing_gene:
        return existing_gene.id

    try:
        gene = Gene(
            symbol=symbol,
            description=description,
            master_gene_id=master_gene_id,
            interaction_source=interaction_source,
            promoter_info=promoter_info,
        )
        session.add(gene)
        session.commit()
        return gene.id

    except Exception as e:
        session.rollback()
        raise ValueError(f"Error inserting gene {symbol}: {str(e)}")


def upsert_dmr_timepoint_annotation(
    session: Session,
    timepoint_id: int,
    dmr_id: int,
    component_id: int = None,
    triconnected_id: int = None,
    degree: int = None,
    node_type: str = None,
    is_isolate: bool = False,
    biclique_ids: str = None,
):
    """
    Update or insert DMR annotation for a specific timepoint.

    Args:
        session: Database session
        timepoint_id: Timepoint ID
        dmr_id: DMR ID
        component_id: Optional component ID
        triconnected_id: Optional triconnected component ID
        degree: Optional node degree
        node_type: Optional node type
        is_isolate: Whether the DMR is isolated
        biclique_ids: Comma-separated list of biclique IDs
    """
    # Try to get existing annotation
    annotation = (
        session.query(DMRTimepointAnnotation)
        .filter(
            and_(
                DMRTimepointAnnotation.timepoint_id == timepoint_id,
                DMRTimepointAnnotation.dmr_id == dmr_id,
            )
        )
        .first()
    )

    if annotation:
        # Update existing annotation
        if component_id is not None:
            annotation.component_id = component_id
        if triconnected_id is not None:
            annotation.triconnected_id = triconnected_id
        if degree is not None:
            annotation.degree = degree
        if node_type is not None:
            annotation.node_type = node_type
        if is_isolate is not None:
            annotation.is_isolate = is_isolate
        if biclique_ids:
            # Append new biclique ID to existing list
            existing_ids = (
                set(annotation.biclique_ids.split(","))
                if annotation.biclique_ids
                else set()
            )
            existing_ids.add(str(biclique_ids))
            annotation.biclique_ids = ",".join(sorted(existing_ids))
    else:
        # Create new annotation
        annotation = DMRTimepointAnnotation(
            timepoint_id=timepoint_id,
            dmr_id=dmr_id,
            component_id=component_id,
            triconnected_id=triconnected_id,
            degree=degree,
            node_type=node_type,
            is_isolate=is_isolate,
            biclique_ids=str(biclique_ids) if biclique_ids else None,
        )
        session.add(annotation)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating DMR annotation: {str(e)}")
        raise


def upsert_gene_timepoint_annotation(
    session: Session,
    timepoint_id: int,
    gene_id: int,
    component_id: int = None,
    triconnected_id: int = None,
    degree: int = None,
    node_type: str = None,
    gene_type: str = None,
    is_isolate: bool = False,
    biclique_ids: str = None,
):
    """
    Update or insert gene annotation for a specific timepoint.

    Args:
        session: Database session
        timepoint_id: Timepoint ID
        gene_id: Gene ID
        component_id: Optional component ID
        triconnected_id: Optional triconnected component ID
        degree: Optional node degree
        node_type: Optional node type (regular_gene, split_gene)
        gene_type: Optional gene type (Nearby, Enhancer, Promoter)
        is_isolate: Whether the gene is isolated
        biclique_ids: Comma-separated list of biclique IDs
    """

    # Try to get existing annotation
    annotation = (
        session.query(GeneTimepointAnnotation)
        .filter(
            and_(
                GeneTimepointAnnotation.timepoint_id == timepoint_id,
                GeneTimepointAnnotation.gene_id == gene_id,
            )
        )
        .first()
    )

    if annotation:
        # Update existing annotation
        if component_id is not None:
            annotation.component_id = component_id
        if triconnected_id is not None:
            annotation.triconnected_id = triconnected_id
        if degree is not None:
            annotation.degree = degree
        if node_type is not None:
            annotation.node_type = node_type
        if gene_type is not None:
            annotation.gene_type = gene_type
        if is_isolate is not None:
            annotation.is_isolate = is_isolate
        if biclique_ids:
            # Append new biclique ID to existing list
            existing_ids = (
                set(annotation.biclique_ids.split(","))
                if annotation.biclique_ids
                else set()
            )
            existing_ids.add(str(biclique_ids))
            annotation.biclique_ids = ",".join(sorted(existing_ids))
    else:
        # Create new annotation
        annotation = GeneTimepointAnnotation(
            timepoint_id=timepoint_id,
            gene_id=gene_id,
            component_id=component_id,
            triconnected_id=triconnected_id,
            degree=degree,
            node_type=node_type,
            gene_type=gene_type,
            is_isolate=is_isolate,
            biclique_ids=str(biclique_ids) if biclique_ids else None,
        )
        session.add(annotation)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating gene annotation: {str(e)}")
        raise


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


def verify_relationships(session: Session):
    """Verify that many-to-many relationships are properly populated."""
    # Check ComponentBiclique relationships
    component_bicliques = session.query(ComponentBiclique).all()
    print(f"Found {len(component_bicliques)} component-biclique relationships")

    # Check Biclique annotations
    dmr_annotations = (
        session.query(DMRTimepointAnnotation)
        .filter(DMRTimepointAnnotation.biclique_ids.isnot(None))
        .all()
    )
    print(f"Found {len(dmr_annotations)} DMR-biclique annotations")

    gene_annotations = (
        session.query(GeneTimepointAnnotation)
        .filter(GeneTimepointAnnotation.biclique_ids.isnot(None))
        .all()
    )
    print(f"Found {len(gene_annotations)} Gene-biclique annotations")

    return (
        len(component_bicliques) > 0
        and len(dmr_annotations) > 0
        and len(gene_annotations) > 0
    )


def update_gene_source_metadata(
    session: Session,
    gene_symbol: str,
    interaction_source: str = None,
    description: str = None,
    promoter_info: str = None,
):
    """Update gene source metadata.

    Args:
        session: Database session
        gene_symbol: Gene symbol to update
        interaction_source: Source of the gene interaction
        description: Gene description
        promoter_info: Additional promoter information
    """
    gene = (
        session.query(Gene)
        .filter(func.lower(Gene.symbol) == gene_symbol.lower())
        .first()
    )
    if gene:
        if interaction_source:
            gene.interaction_source = interaction_source
        if description:
            gene.description = description
        if promoter_info:
            gene.promoter_info = promoter_info
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error updating gene metadata for {gene_symbol}: {str(e)}")
            raise


def get_or_create_gene(
    session: Session, symbol: str, description: str = None, master_gene_id: int = None
) -> int:
    """Get an existing gene or create a new one if it doesn't exist."""
    gene = session.query(Gene).filter(func.lower(Gene.symbol) == symbol.lower()).first()
    if gene:
        return gene.id
    else:
        return insert_gene(session, symbol, description, master_gene_id)
