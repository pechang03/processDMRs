"""Database operations for biclique processing."""

from typing import Dict, List, Set, Tuple
import networkx as nx
import pandas as pd
from sqlalchemy.orm import Session
from backend.app.biclique_analysis.analyzer import analyze_bicliques
from backend.app.utils.id_mapping import create_dmr_id, convert_dmr_id
from .operations import insert_component
from .populate_tables import (
    populate_dmr_annotations,
    populate_gene_annotations,
    populate_bicliques,
)
from backend.app.biclique_analysis.reader import read_bicliques_file
from backend.app.utils.metadata import get_gene_details, get_dmr_details


def process_bicliques_db(
    session: Session,
    timepoint_id: int,
    timepoint_name: str,
    original_graph: nx.Graph,
    bicliques_file: str,
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    file_format: str = "gene_name",
) -> Dict:
    """Process bicliques with database integration."""

    # Read bicliques
    bicliques_result = read_bicliques_file(
        bicliques_file,
        original_graph,
        gene_id_mapping=gene_id_mapping,
        file_format=file_format,
    )

    if not bicliques_result or not bicliques_result.get("bicliques"):
        return bicliques_result

    # Create split graph and analyze
    split_graph = nx.Graph()
    analysis_results = analyze_bicliques(
        original_graph,
        bicliques_result["bicliques"],
        timepoint_id,  # pass the integer timepoint_id here
        split_graph=split_graph,
    )

    # Process original components
    for comp_info in analysis_results["original_components"]:
        comp_id = _process_original_component(
            session, timepoint_id, comp_info, original_graph, df
        )

    # Process split components
    for comp_info in analysis_results["split_components"]:
        comp_id = _process_split_component(
            session, timepoint_id, comp_info, split_graph, df, gene_id_mapping
        )

    return analysis_results


def _process_original_component(
    session: Session,
    timepoint_id: int,
    comp_info: Dict,
    original_graph: nx.Graph,
    df: pd.DataFrame,
) -> int:
    """Process a single component from the original graph."""
    comp_subgraph = original_graph.subgraph(comp_info["nodes"])

    # Insert component with classification
    comp_id = insert_component(
        session,
        timepoint_id=timepoint_id,
        graph_type="original",
        category=comp_info["category"],
        size=comp_info["size"],
        dmr_count=len(comp_info["dmr_nodes"]),
        gene_count=len(comp_info["gene_nodes"]),
        edge_count=comp_info["edge_count"],
        density=comp_info["density"],
    )

    # Populate annotations
    populate_dmr_annotations(
        session=session,
        timepoint_id=timepoint_id,
        component_id=comp_id,
        graph=comp_subgraph,
        df=df,
        is_original=True,
    )

    populate_gene_annotations(
        session=session,
        timepoint_id=timepoint_id,
        component_id=comp_id,
        graph=comp_subgraph,
        df=df,
        is_original=True,
    )

    return comp_id


def _process_split_component(
    session: Session,
    timepoint_id: int,
    comp_info: Dict,
    split_graph: nx.Graph,
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
) -> int:
    """Process a single component from the split graph."""
    comp_subgraph = split_graph.subgraph(comp_info["nodes"])

    # Insert component with classification
    comp_id = insert_component(
        session,
        timepoint_id=timepoint_id,
        graph_type="split",
        category=comp_info["category"],
        size=comp_info["size"],
        dmr_count=len(comp_info["dmr_nodes"]),
        gene_count=len(comp_info["gene_nodes"]),
        edge_count=comp_info["edge_count"],
        density=comp_info["density"],
    )

    # Pre-convert each biclique's DMR node set
    converted_bicliques = []
    for dmrs, genes in comp_info["bicliques"]:
        converted_dmrs = {convert_dmr_id(n, timepoint_id) for n in dmrs}
        converted_bicliques.append((converted_dmrs, genes))

    # Populate bicliques and annotations using pre-converted DMR IDs
    for biclique in converted_bicliques:
        biclique_id = populate_bicliques(
            session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            dmr_nodes=biclique[0],
            gene_nodes=biclique[1],
        )

        populate_dmr_annotations(
            session=session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            graph=comp_subgraph,
            df=df,
            is_original=False,
            bicliques=converted_bicliques,
        )

        populate_gene_annotations(
            session=session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            graph=comp_subgraph,
            df=df,
            is_original=False,
            bicliques=converted_bicliques,
        )

    return comp_id


def _add_biclique_details(
    bicliques: List, df: pd.DataFrame, gene_id_mapping: Dict
) -> Dict:
    """Add detailed information for each biclique."""
    detailed_info = {}
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        detailed_info[f"biclique_{idx+1}_details"] = {
            "dmrs": get_dmr_details(dmr_nodes, df),
            "genes": get_gene_details(gene_nodes, df, gene_id_mapping),
        }
    return detailed_info
