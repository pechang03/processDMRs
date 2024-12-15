"""Core database operations for DMR analysis system."""

from collections import defaultdict
import networkx as nx
from typing import Dict, List, Set, Tuple
import pandas as pd

# from utils import node_info, edge_info
from .operations import (
    get_or_create_timepoint,
    # insert_timepoint,
    insert_dmr,
    insert_biclique,
    insert_component,
    insert_triconnected_component,
    update_biclique_category,
    insert_component_biclique,
    insert_statistics,
    insert_metadata,
    insert_relationship,
    insert_gene,
    upsert_dmr_timepoint_annotation,
    upsert_gene_timepoint_annotation,
    update_gene_metadata,
    # get_or_create_gene,
    # query_timepoints,
    # query_genes,
    # query_dmrs,
    # query_bicliques,
    # query_components,
    # query_statistics,
    # query_metadata,
    # query_relationships,
    # update_gene_hub_status,
)
from sqlalchemy import and_
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
    symbol: str = None,
    master_gene_id: int = None,
    description: str = None,
    interaction_source: str = None,
    promoter_info: str = None,
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


def populate_core_genes(
    session: Session,
    gene_id_mapping: dict,
):
    """Populate core gene data (symbols and master gene IDs)."""
    print("\nPopulating core gene tables...")
    print(f"Received {len(gene_id_mapping)} genes in mapping")
    sample_genes = list(gene_id_mapping.items())[:5]
    print(f"Sample genes: {sample_genes}")

    genes_added = 0
    for gene_symbol, gene_id in gene_id_mapping.items():
        # Clean and lowercase the symbol
        gene_symbol = str(gene_symbol).strip().lower()

        print(f"Processing gene: {gene_symbol} with ID: {gene_id}")  # Debug line

        # Skip invalid symbols - now using exact matching
        invalid_values = {
            "unnamed:",
            "nan",
            ".",
            "n/a",
            "",
            "none",
            "null",
        }  # Set of exact matches
        if gene_symbol in invalid_values:
            print(f"Skipping invalid gene symbol: {gene_symbol}")
            continue

        # Check if master gene ID already exists
        existing = (
            session.query(MasterGeneID)
            .filter(func.lower(MasterGeneID.gene_symbol) == gene_symbol)
            .first()
        )

        if not existing:
            try:
                print(f"Adding new master gene: {gene_symbol}")  # Debug line
                master_gene = MasterGeneID(id=gene_id, gene_symbol=gene_symbol)
                session.add(master_gene)
                genes_added += 1

                # Create corresponding gene entry
                gene = Gene(symbol=gene_symbol, master_gene_id=gene_id)
                session.add(gene)

                # Commit in smaller batches
                if genes_added % 1000 == 0:
                    session.commit()
                    print(f"Added {genes_added} master gene IDs")

            except Exception as e:
                session.rollback()
                print(f"Error adding master gene ID for {gene_symbol}: {str(e)}")
                continue

    try:
        session.commit()
        print(f"Added {genes_added} master gene IDs")
        return genes_added
    except Exception as e:
        session.rollback()
        print(f"Error adding master gene IDs: {str(e)}")
        raise


def populate_timepoint_genes(
    session: Session,
    gene_id_mapping: dict,
    df: pd.DataFrame,
    timepoint_id: int,
):
    """Populate timepoint-specific gene data and annotations."""
    if timepoint_id is None:
        raise ValueError("timepoint_id must be provided")

    # First ensure core gene entries exist
    # populate_core_genes(session, gene_id_mapping) (this should have been called before)

    # Then process timepoint-specific data
    if df is not None:
        print("\nProcessing timepoint-specific gene data...")
        process_gene_sources(df, gene_id_mapping, session, timepoint_id)


def process_gene_sources(
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    session: Session,
    timepoint_id: int,
):
    """
    Process genes from different sources and update their metadata.
    Each row represents a DMR, but contains gene information we can use
    to update gene metadata if it hasn't been set.

    Args:
        df: DataFrame containing DMR and gene information
        gene_id_mapping: Mapping of gene symbols to IDs
        session: Database session
        timepoint_id: ID of the timepoint being processed
    """
    print("\nProcessing gene interaction sources...")
    processed_genes = set()

    from .operations import update_gene_source_metadata

    # Process each DMR row in the dataframe
    for _, row in df.iterrows():
        # Process nearby genes - if Gene_Symbol_Nearby matches a gene, update its description
        if "Gene_Symbol_Nearby" in df.columns and pd.notna(row["Gene_Symbol_Nearby"]):
            gene_symbol = str(row["Gene_Symbol_Nearby"]).strip().lower()
            if gene_symbol and gene_symbol != ".":
                gene_description = row.get("Gene_Description")
                if gene_description and str(gene_description).strip() != ".":
                    update_gene_source_metadata(
                        session,
                        gene_symbol,
                        interaction_source="Gene_Symbol_Nearby",
                        description=gene_description
                    )
                    processed_genes.add(gene_symbol)

        # Process enhancer interactions
        if "ENCODE_Enhancer_Interaction(BingRen_Lab)" in df.columns:
            raw_enhancer_info = row["ENCODE_Enhancer_Interaction(BingRen_Lab)"]
            if isinstance(raw_enhancer_info, str) and raw_enhancer_info.strip() and raw_enhancer_info != ".":
                from utils import process_enhancer_info
                genes = process_enhancer_info(raw_enhancer_info)
                
                for gene_symbol in genes:
                    gene_symbol = str(gene_symbol).strip().lower()
                    if gene_symbol and gene_symbol != ".":
                        enhancer_part = None
                        if "/" in raw_enhancer_info:
                            _, enhancer_part = raw_enhancer_info.split("/", 1)
                            enhancer_part = enhancer_part.strip()
                            if enhancer_part == ".":
                                enhancer_part = None

                        update_gene_source_metadata(
                            session,
                            gene_symbol,
                            interaction_source="ENCODE_Enhancer",
                            promoter_info=enhancer_part
                        )
                        processed_genes.add(gene_symbol)

        # Process promoter interactions
        if "ENCODE_Promoter_Interaction(BingRen_Lab)" in df.columns:
            raw_promoter_info = row["ENCODE_Promoter_Interaction(BingRen_Lab)"]
            if isinstance(raw_promoter_info, str) and raw_promoter_info.strip() and raw_promoter_info != ".":
                from utils import process_enhancer_info
                genes = process_enhancer_info(raw_promoter_info)
                
                for gene_symbol in genes:
                    gene_symbol = str(gene_symbol).strip().lower()
                    if gene_symbol and gene_symbol != ".":
                        update_gene_source_metadata(
                            session,
                            gene_symbol,
                            interaction_source="ENCODE_Promoter"
                        )
                        processed_genes.add(gene_symbol)

    print(f"Updated interaction sources for {len(processed_genes)} genes")


def populate_dmrs(
    session: Session, df: pd.DataFrame, timepoint_id: int, gene_id_mapping: dict
):
    """Populate DMRs table with dominating set information."""
    # Create bipartite graph
    from data_loader import create_bipartite_graph

    bipartite_graph = create_bipartite_graph(df, gene_id_mapping, "DSStimeseries")

    # Calculate dominating set
    from rb_domination import calculate_dominating_sets

    dominating_set = calculate_dominating_sets(bipartite_graph, df, "DSStimeseries")

    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
        dmr_data = {
            "dmr_number": row["DMR_No."],
            "area_stat": row.get("Area_Stat"),
            "description": row.get("Gene_Description"),
            "dmr_name": row.get("DMR_Name"),
            "gene_description": row.get("Gene_Description"),
            "chromosome": row.get("Chromosome"),
            "start_position": row.get("Start"),
            "end_position": row.get("End"),
            "strand": row.get("Strand"),
            "p_value": row.get("P-value"),
            "q_value": row.get("Q-value"),
            "mean_methylation": row.get("Mean_Methylation"),
            "is_hub": dmr_id in dominating_set,
        }
        insert_dmr(session, timepoint_id, **dmr_data)


def populate_timepoints(session: Session):
    """Populate timepoints table with names and DMR ID offsets."""
    # Define timepoints with their offsets
    timepoint_data = {
        "DSStimeseries": {
            "offset": 0,
            "description": "DSS time series analysis"
        },
        "P21-P28_TSS": {
            "offset": 10000,
            "description": "P21 to P28 comparison"
        },
        "P21-P40_TSS": {
            "offset": 20000,
            "description": "P21 to P40 comparison"
        },
        "P21-P60_TSS": {
            "offset": 30000,
            "description": "P21 to P60 comparison"
        },
        "P21-P180_TSS": {
            "offset": 40000,
            "description": "P21 to P180 comparison"
        },
        "TP28-TP180_TSS": {
            "offset": 50000,
            "description": "TP28 to TP180 comparison"
        },
        "TP40-TP180_TSS": {
            "offset": 60000,
            "description": "TP40 to TP180 comparison"
        },
        "TP60-TP180_TSS": {
            "offset": 70000,
            "description": "TP60 to TP180 comparison"
        }
    }

    print("\nPopulating timepoints table...")
    for name, data in timepoint_data.items():
        get_or_create_timepoint(
            session, 
            name=name,
            description=data["description"],
            dmr_id_offset=data["offset"]
        )
    
    session.commit()
    print("Timepoints populated successfully")


def populate_bicliques(
    session: Session,
    timepoint_id: int,
    component_id: int,
    dmr_nodes: Set[int],
    gene_nodes: Set[int],
):
    """Populate bicliques table and establish relationships."""
    # Create the biclique
    biclique_id = insert_biclique(
        session,
        timepoint_id=timepoint_id,
        component_id=component_id,
        dmr_ids=list(dmr_nodes),
        gene_ids=list(gene_nodes),
    )

    # Create the many-to-many relationship
    component_biclique = ComponentBiclique(
        timepoint_id=timepoint_id, component_id=component_id, biclique_id=biclique_id
    )
    session.add(component_biclique)
    session.commit()

    return biclique_id


def populate_gene_annotations(
    session: Session,
    timepoint_id: int,
    component_id: int,
    graph: nx.Graph,
    df: pd.DataFrame,
    is_original: bool,
    bicliques: List[Tuple[Set[int], Set[int]]] = None,
) -> None:
    """Populate gene annotations for a component."""

    gene_nodes = {n for n, d in graph.nodes(data=True) if d["bipartite"] == 1}

    for gene in gene_nodes:
        # Basic properties
        degree = graph.degree(gene)
        is_isolate = degree == 0

        # Get gene type from DataFrame
        gene_type = None
        if "Gene_Symbol_Nearby" in df.columns:
            gene_type = "Nearby"
        elif "ENCODE_Enhancer_Interaction(BingRen_Lab)" in df.columns:
            gene_type = "Enhancer"
        elif "ENCODE_Promoter_Interaction(BingRen_Lab)" in df.columns:
            gene_type = "Promoter"

        # Determine if split gene in split graph
        node_type = "regular_gene"
        biclique_ids = None
        if not is_original and bicliques:
            participating_bicliques = [
                idx for idx, (_, genes) in enumerate(bicliques) if gene in genes
            ]
            if len(participating_bicliques) > 1:
                node_type = "split_gene"
            biclique_ids = ",".join(map(str, participating_bicliques))

        upsert_gene_timepoint_annotation(
            session=session,
            timepoint_id=timepoint_id,
            gene_id=gene,
            component_id=component_id,
            degree=degree,
            node_type=node_type,
            gene_type=gene_type,
            is_isolate=is_isolate,
            biclique_ids=biclique_ids,
        )


def populate_dmr_annotations(
    session: Session,
    timepoint_id: int,
    component_id: int,
    graph: nx.Graph,
    df: pd.DataFrame,
    is_original: bool,
    bicliques: List[Tuple[Set[int], Set[int]]] = None,
) -> None:
    """Populate DMR annotations for a component."""

    dmr_nodes = {n for n, d in graph.nodes(data=True) if d["bipartite"] == 0}

    for dmr in dmr_nodes:
        # Basic properties
        degree = graph.degree(dmr)
        is_isolate = degree == 0

        # Get biclique participation if this is split graph
        biclique_ids = None
        if not is_original and bicliques:
            participating_bicliques = [
                idx for idx, (dmrs, _) in enumerate(bicliques) if dmr in dmrs
            ]
            biclique_ids = ",".join(map(str, participating_bicliques))

        upsert_dmr_timepoint_annotation(
            session=session,
            timepoint_id=timepoint_id,
            dmr_id=dmr,
            component_id=component_id,
            degree=degree,
            node_type="isolated" if is_isolate else "regular",
            is_isolate=is_isolate,
            biclique_ids=biclique_ids,
        )


def populate_statistics(session: Session, statistics: dict):
    """Populate statistics table."""
    for category, stats in statistics.items():
        for key, value in stats.items():
            insert_statistics(session, category, key, str(value))


def populate_metadata(session: Session, metadata: dict):
    """Populate metadata table."""
    for entity_type, entity_data in metadata.items():
        for entity_id, entity_metadata in entity_data.items():
            for key, value in entity_metadata.items():
                insert_metadata(session, entity_type, entity_id, key, str(value))


def populate_relationships(session: Session, relationships: list):
    """Populate relationships table."""
    for rel in relationships:
        insert_relationship(session, **rel)


def populate_master_gene_ids(session: Session, gene_id_mapping: Dict[str, int]):
    """Populate MasterGeneID table and create core Gene entries.

    Args:
        session: Database session
        gene_id_mapping: Dictionary mapping gene symbols to their IDs from master_gene_ids.csv
    """
    print("\nPopulating MasterGeneID and core Gene entries...")
    genes_added = 0

    for gene_symbol, gene_id in gene_id_mapping.items():
        # Clean and lowercase the symbol
        gene_symbol = str(gene_symbol).strip().lower()

        # Skip invalid symbols
        invalid_patterns = ["unnamed:", "nan", ".", "n/a", ""]
        if (
            any(gene_symbol.startswith(pat) for pat in invalid_patterns)
            or not gene_symbol
        ):
            continue

        try:
            # Create MasterGeneID entry
            master_gene = MasterGeneID(id=gene_id, gene_symbol=gene_symbol)
            session.add(master_gene)

            # Create corresponding core Gene entry with same ID
            gene = Gene(id=gene_id, symbol=gene_symbol, master_gene_id=gene_id)
            session.add(gene)

            genes_added += 1

            # Commit in batches
            if genes_added % 1000 == 0:
                session.commit()
                print(f"Added {genes_added} master gene IDs and core gene entries")

        except Exception as e:
            session.rollback()
            print(f"Error adding master gene ID for {gene_symbol}: {str(e)}")
            continue

    # Final commit
    try:
        session.commit()
        print(f"Added total of {genes_added} master gene IDs and core gene entries")
    except Exception as e:
        session.rollback()
        print(f"Error in final commit: {str(e)}")
        raise
