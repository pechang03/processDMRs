"""Core database operations for DMR analysis system."""

from collections import defaultdict
from types import NoneType
import networkx as nx
from typing import Dict, List, Set, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from .models import EdgeDetails
from backend.app.database.cleanup import clean_edge_details

from collections import defaultdict
from .operations import (
    update_gene_source_metadata,
    upsert_gene_timepoint_annotation,
    upsert_dmr_timepoint_annotation,
    get_or_create_timepoint,
    update_gene_hub_status,
    insert_dmr,
    insert_biclique,
    insert_component_biclique,
    insert_statistics,
    insert_metadata,
    insert_relationship,
)
from .models import (
    Biclique,
    ComponentBiclique,
    Statistic,
    Metadata,
    Relationship,
    GeneTimepointAnnotation,
    DMRTimepointAnnotation,
    Gene,
    Timepoint,
    DMR,
    Component,
    MasterGeneID,
)
from backend.app.core.data_loader import create_bipartite_graph
from backend.app.database.dominating_sets import calculate_dominating_sets
from backend.app.utils.data_processing import process_enhancer_info
from backend.app.biclique_analysis.classifier import (
    classify_biclique,
    BicliqueSizeCategory,
)

# from utils import node_info, edge_info
from backend.app.core.rb_domination import calculate_dominating_set


def populate_master_gene_ids(
    session: Session,
    gene_id_mapping: dict,
):
    """Populate MasterGeneID table with gene symbols and IDs."""
    print("\nPopulating MasterGeneID table...")
    print(f"Received {len(gene_id_mapping)} genes in mapping")
    sample_genes = list(gene_id_mapping.items())[:5]
    print(f"Sample genes: {sample_genes}")

    # First convert all keys to lowercase in the mapping
    gene_id_mapping = {k.lower(): v for k, v in gene_id_mapping.items() if k}

    genes_added = 0
    for gene_symbol, gene_id in gene_id_mapping.items():
        # Skip None or empty symbols
        if not gene_symbol:
            continue

        # Clean symbol and ensure lowercase
        gene_symbol = str(gene_symbol).strip().lower()
        if not gene_symbol:  # Skip if empty after stripping
            continue

        try:
            # Create MasterGeneID entry - don't check for existing since table should be empty
            master_gene = MasterGeneID(id=gene_id, gene_symbol=gene_symbol)
            session.add(master_gene)
            genes_added += 1

            # Commit in batches
            if genes_added % 1000 == 0:
                try:
                    session.commit()
                    print(f"Added {genes_added} master gene IDs")
                except Exception as e:
                    session.rollback()
                    print(f"Error in batch commit: {str(e)}")
                    raise

        except Exception as e:
            session.rollback()
            print(f"Error processing gene {gene_symbol}: {str(e)}")
            continue

    # Final commit for remaining records
    try:
        session.commit()
        print(f"Total master gene IDs added: {genes_added}")
        return genes_added
    except Exception as e:
        session.rollback()
        print(f"Error in final commit: {str(e)}")
        raise
        print(f"Error in final commit: {str(e)}")
        raise


def populate_core_genes(
    session: Session,
    gene_id_mapping: dict,
):
    """Populate core gene data (symbols and master gene IDs)."""
    print("\nPopulating core gene tables...in func")
    print(f"Received {len(gene_id_mapping)} genes in mapping")
    sample_genes = list(gene_id_mapping.items())[:5]
    print(f"Sample genes: {sample_genes}")

    genes_added = 0
    for gene_symbol, gene_id in gene_id_mapping.items():
        # Clean and lowercase the symbol
        gene_symbol = str(gene_symbol).strip()  # Keep original case for storage
        gene_symbol_lower = gene_symbol.lower()  # Lowercase for comparison

        # Skip invalid symbols
        invalid_patterns = ["unnamed:", "nan", "n/a", ""]
        # any(gene_symbol_lower.startswith(pat) for pat in invalid_patterns)
        # or not gene_symbol
        if gene_symbol in invalid_patterns:
            print(f"Warning invalid symbol: {gene_symbol}")
            continue

        try:
            # Check if gene already exists (case-insensitive)
            existing = (
                session.query(MasterGeneID)
                .filter(func.lower(MasterGeneID.gene_symbol) == gene_symbol_lower)
                .first()
            )

            if not existing:
                # Create MasterGeneID entry
                master_gene = MasterGeneID(id=gene_id, gene_symbol=gene_symbol)
                session.add(master_gene)

            # Create corresponding core Gene entry with same ID
            gene = Gene(id=gene_id, symbol=gene_symbol, master_gene_id=gene_id)
            session.add(gene)

            genes_added += 1

            # Commit in batches
            if genes_added % 1000 == 0:
                try:
                    session.commit()
                    print(f"Added {genes_added} master gene IDs and core gene entries")
                except Exception as e:
                    session.rollback()
                    print(f"Error in batch commit: {str(e)}")
                    raise

        except Exception as e:
            session.rollback()
            print(f"Error processing gene {gene_symbol}: {str(e)}")
            continue

    # Final commit for remaining records
    try:
        session.commit()
        print(f"Added {genes_added} master gene IDs")
        return genes_added
    except Exception as e:
        session.rollback()
        print(f"Error in final commit: {str(e)}")
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
    promoter_info_map = defaultdict(set)  # Track promoter info per gene

    # Process each DMR row in the dataframe
    for _, row in df.iterrows():
        # Process nearby genes
        if "Gene_Symbol_Nearby" in df.columns and pd.notna(row["Gene_Symbol_Nearby"]):
            gene_symbol = str(row["Gene_Symbol_Nearby"]).strip().lower()
            if gene_symbol and gene_symbol != ".":
                gene_description = row.get("Gene_Description")
                if gene_description and str(gene_description).strip() != ".":
                    update_gene_source_metadata(
                        session,
                        gene_symbol,
                        interaction_source="Gene_Symbol_Nearby",
                        description=gene_description,
                    )
                    # Add gene type annotation
                    if gene_symbol in gene_id_mapping:
                        upsert_gene_timepoint_annotation(
                            session,
                            timepoint_id=timepoint_id,
                            gene_id=gene_id_mapping[gene_symbol],
                            gene_type="Nearby",
                        )
                    processed_genes.add(gene_symbol)

        # Process enhancer interactions
        if "ENCODE_Enhancer_Interaction(BingRen_Lab)" in df.columns:
            raw_enhancer_info = row["ENCODE_Enhancer_Interaction(BingRen_Lab)"]
            if (
                isinstance(raw_enhancer_info, str)
                and raw_enhancer_info.strip()
                and raw_enhancer_info != "."
            ):
                genes = process_enhancer_info(raw_enhancer_info)

                for gene_symbol in genes:
                    gene_symbol = str(gene_symbol).strip().lower()
                    if gene_symbol and gene_symbol != ".":
                        update_gene_source_metadata(
                            session,
                            gene_symbol,
                            interaction_source="ENCODE_Enhancer",
                        )
                        # Add gene type annotation
                        if gene_symbol in gene_id_mapping:
                            upsert_gene_timepoint_annotation(
                                session,
                                timepoint_id=timepoint_id,
                                gene_id=gene_id_mapping[gene_symbol],
                                gene_type="Enhancer",
                            )
                        processed_genes.add(gene_symbol)

        # Process promoter interactions
        if "ENCODE_Promoter_Interaction(BingRen_Lab)" in df.columns:
            raw_promoter_info = row["ENCODE_Promoter_Interaction(BingRen_Lab)"]
            if (
                isinstance(raw_promoter_info, str)
                and raw_promoter_info.strip()
                and raw_promoter_info != "."
            ):
                genes = process_enhancer_info(raw_promoter_info)

                # Extract and store unique promoter info
                if "/" in raw_promoter_info:
                    promoter_parts = raw_promoter_info.split("/")
                    for part in promoter_parts:
                        if ";" in part:
                            enhancer_id, gene = part.split(";", 1)
                            gene = gene.strip().lower()
                            if gene in gene_id_mapping:
                                promoter_info_map[gene].add(enhancer_id.strip())

                for gene_symbol in genes:
                    gene_symbol = str(gene_symbol).strip().lower()
                    if gene_symbol and gene_symbol != ".":
                        # Add gene type annotation
                        if gene_symbol in gene_id_mapping:
                            upsert_gene_timepoint_annotation(
                                session,
                                timepoint_id=timepoint_id,
                                gene_id=gene_id_mapping[gene_symbol],
                                gene_type="Promoter",
                            )
                        processed_genes.add(gene_symbol)

    # Update gene metadata with deduplicated promoter info
    for gene_symbol, promoter_ids in promoter_info_map.items():
        deduplicated_info = "/".join(sorted(promoter_ids))
        update_gene_source_metadata(
            session,
            gene_symbol,
            interaction_source="ENCODE_Promoter",
            promoter_info=deduplicated_info,
        )

    print(f"Updated interaction sources for {len(processed_genes)} genes")


def populate_dmrs(
    session: Session, df: pd.DataFrame, timepoint_id: int, gene_id_mapping: dict
):
    """Populate DMRs table with dominating set information."""
    # Create bipartite graph

    bipartite_graph = create_bipartite_graph(df, gene_id_mapping, "DSStimeseries")

    # Calculate dominating set

    dominating_set = calculate_dominating_sets(
        bipartite_graph,
        df,
        "DSStimeseries",  # timepoint name
        session,  # database session
        timepoint_id,  # timepoint ID
    )

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


def populate_timepoints(
    session: Session,
    timeseries_sheet: str,
    pairwise_sheets: List[str],
    start_gene_id: int,
):
    """
    Populate timepoints table with names and DMR ID offsets.

    Args:
        session: Database session
        timeseries_sheet: The timeseries sheet name (e.g. "DSS_Time_Series")
        pairwise_sheets: List of sheet names from pairwise file
        start_gene_id: Minimum ID value for genes (DMR IDs must be below this)
    """
    # Validate start_gene_id
    if start_gene_id <= 0:
        raise ValueError(f"start_gene_id must be positive, got {start_gene_id}")

    # Define timepoint mappings
    timepoint_data = {
        # Timeseries
        "DSS_Time_Series": {
            "name": "DSStimeseries",
            "offset": 0,
            "description": "DSS time series analysis",
        },
        # Pairwise mappings
        "P21-P28_TSS": {"name": "P21-P28", "offset": 10000},
        "P21-P40_TSS": {"name": "P21-P40", "offset": 20000},
        "P21-P60_TSS": {"name": "P21-P60", "offset": 30000},
        "P21-P180_TSS": {"name": "P21-P180", "offset": 40000},
        "TP28-TP180_TSS": {"name": "TP28-TP180", "offset": 50000},
        "TP40-TP180_TSS": {"name": "TP40-TP180", "offset": 60000},
        "TP60-TP180_TSS": {"name": "TP60-TP180", "offset": 70000},
    }

    # Validate offsets against start_gene_id
    max_offset = max(data["offset"] for data in timepoint_data.values())
    max_possible_dmr_id = max_offset + 10000

    if max_possible_dmr_id >= start_gene_id:
        raise ValueError(
            f"Maximum possible DMR ID ({max_possible_dmr_id}) would exceed or equal "
            f"start_gene_id ({start_gene_id}). Please increase start_gene_id in configuration "
            f"to at least {max_possible_dmr_id + 10000} for safety."
        )

    print("\nPopulating timepoints table...")
    print(f"Using start_gene_id: {start_gene_id}")
    print(f"Maximum DMR ID offset: {max_offset}")
    print(f"Maximum possible DMR ID: {max_possible_dmr_id}")

    # Add timeseries timepoint
    get_or_create_timepoint(
        session,
        sheet_name=timeseries_sheet,
        name=timepoint_data[timeseries_sheet]["name"],
        description=timepoint_data[timeseries_sheet]["description"],
        dmr_id_offset=timepoint_data[timeseries_sheet]["offset"],
    )

    # Add pairwise timepoints
    for sheet in pairwise_sheets:
        if sheet in timepoint_data:
            get_or_create_timepoint(
                session,
                sheet_name=sheet,
                name=timepoint_data[sheet]["name"],
                dmr_id_offset=timepoint_data[sheet]["offset"],
            )
        else:
            print(f"Warning: Unknown sheet name {sheet}, skipping...")

    session.commit()
    print("Timepoints populated successfully")
    print("\nTimepoint mappings:")
    for sheet_name, data in timepoint_data.items():
        print(f"  {sheet_name} -> {data['name']}: offset {data['offset']}")


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


def populate_edge_details(
    session: Session,
    df: pd.DataFrame,
    timepoint_id: int,
    gene_id_mapping: Dict[str, int],
):
    """Populate edge details table from dataframe."""
    print("\nPopulating edge details...")
    # Clean up any existing edge details for this timepoint
    clean_edge_details(session, timepoint_id)
    aggregated_edges = {}
    priority_map = {"direct": 3, "nearby": 2, "enhancer": 1, "promoter": 1}

    # Process nearby genes
    if "Gene_Symbol_Nearby" in df.columns:
        for _, row in df.iterrows():
            dmr_id = row["DMR_No."]  # - 1  dont Convert to 0-based index
            gene_symbol = str(row["Gene_Symbol_Nearby"]).strip().lower()
            if gene_symbol and gene_symbol != "." and gene_symbol in gene_id_mapping:
                gene_id = gene_id_mapping[gene_symbol]
                distance_from_tss = row.get("Distance_From_TSS")
                distance_val = (
                    pd.to_numeric(distance_from_tss, errors="coerce")
                    if distance_from_tss is not None
                    else None
                )
                edge_type = "nearby"
                if distance_val is not None and distance_val < 0:
                    edge_type = "direct"
                edge = EdgeDetails(
                    dmr_id=dmr_id,
                    gene_id=gene_id,
                    timepoint_id=timepoint_id,
                    edge_type=edge_type,
                    distance_from_tss=distance_val,
                    description=row.get("Gene_Description"),
                )
                key = (dmr_id, gene_id)
                if (
                    key not in aggregated_edges
                    or priority_map[edge_type]
                    > priority_map[aggregated_edges[key].edge_type]
                ):
                    aggregated_edges[key] = edge

    # Process enhancer interactions
    if "ENCODE_Enhancer_Interaction(BingRen_Lab)" in df.columns:
        for _, row in df.iterrows():
            dmr_id = row["DMR_No."]  # Do not adjust index
            enhancer_info = row["ENCODE_Enhancer_Interaction(BingRen_Lab)"]
            if (
                isinstance(enhancer_info, str)
                and enhancer_info.strip()
                and enhancer_info != "."
            ):
                processed_enhancer_genes = set()
                interactions = enhancer_info.split(";")
                for interaction in interactions:
                    interaction = interaction.strip()
                    if interaction and interaction != ".":
                        parts = interaction.split("/")
                        gene_symbol = parts[0].strip().lower()
                        if gene_symbol in processed_enhancer_genes:
                            continue
                        processed_enhancer_genes.add(gene_symbol)
                        distance_val = None
                        # if len(parts) > 1: # this is not the way to compute this distance
                        # distance_str = parts[1].strip()
                        # if distance_str.startswith("e"):
                        #    try:
                        #        distance_val = int(distance_str[1:])
                        #    except ValueError:
                        #        distance_val = None
                        # else:
                        #    try:
                        #        distance_val = int(distance_str)
                        #    except ValueError:
                        #        distance_val = None
                        # else:
                        # distance_val = None
                        if gene_symbol in gene_id_mapping:
                            edge = EdgeDetails(
                                dmr_id=dmr_id,
                                gene_id=gene_id_mapping[gene_symbol],
                                timepoint_id=timepoint_id,
                                edge_type="enhancer",
                                distance_from_tss=distance_val,
                                description=f"Enhancer interaction: {interaction}",
                            )
                            key = (dmr_id, gene_id_mapping[gene_symbol])
                            if (
                                key not in aggregated_edges
                                or priority_map["enhancer"]
                                > priority_map[aggregated_edges[key].edge_type]
                            ):
                                aggregated_edges[key] = edge
    else:
        print("ERROR : Can't found ENCODER column")

    if "ENCODE_Promoter_Interaction(BingRen_Lab)" in df.columns:
        for _, row in df.iterrows():
            dmr_id = row["DMR_No."]
            promoter_info = row["ENCODE_Promoter_Interaction(BingRen_Lab)"]
            if (
                isinstance(promoter_info, str)
                and promoter_info.strip()
                and promoter_info != "."
            ):
                processed_promoter_genes = set()
                interactions = promoter_info.split(";")
                for interaction in interactions:
                    interaction = interaction.strip()
                    if interaction and interaction != ".":
                        parts = interaction.split("/")
                        gene_symbol = parts[0].strip().lower()
                        if gene_symbol in processed_promoter_genes:
                            continue
                        processed_promoter_genes.add(gene_symbol)
                        distance_val = None
                        # if len(parts) > 1: # this is not the way to compute this distance
                        #    distance_str = parts[1].strip()
                        #    if distance_str.startswith("e"):
                        #        try:
                        #            distance_val = int(distance_str[1:])
                        #        except ValueError:
                        #            distance_val = None
                        #    else:
                        #        try:
                        #            distance_val = int(distance_str)
                        #        except ValueError:
                        #            distance_val = None
                        # else:
                        #    distance_val = None
                        if gene_symbol in gene_id_mapping:
                            edge = EdgeDetails(
                                dmr_id=dmr_id,
                                gene_id=gene_id_mapping[gene_symbol],
                                timepoint_id=timepoint_id,
                                edge_type="promoter",
                                distance_from_tss=distance_val,
                                description=f"Promoter interaction: {interaction}",
                            )
                            key = (dmr_id, gene_id_mapping[gene_symbol])
                            if (
                                key not in aggregated_edges
                                or priority_map["promoter"]
                                > priority_map[aggregated_edges[key].edge_type]
                            ):
                                aggregated_edges[key] = edge
    else:
        print("ERROR : Can't found ENCODE_Promoter_Interaction column")
    for edge in aggregated_edges.values():
        session.add(edge)

    try:
        session.commit()
        print("Edge details populated successfully")
    except Exception as e:
        session.rollback()
        print(f"Error populating edge details: {str(e)}")
        raise


def populate_relationships(session: Session, relationships: list):
    """Populate relationships table."""
    for rel in relationships:
        insert_relationship(session, **rel)
