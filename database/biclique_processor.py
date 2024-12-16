"""Database operations for biclique processing."""

from typing import Dict, List, Set, Tuple
import networkx as nx
import pandas as pd
from sqlalchemy.orm import Session
from biclique_analysis.analyzer import analyze_bicliques
from .operations import insert_component
from .populate_tables import (
    populate_dmr_annotations,
    populate_gene_annotations,
    populate_bicliques,
)


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
    from biclique_analysis.reader import read_bicliques_file

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
        original_graph, bicliques_result["bicliques"], split_graph
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

    # Populate bicliques and annotations
    for biclique in comp_info["bicliques"]:
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
            bicliques=comp_info["bicliques"],
        )

        populate_gene_annotations(
            session=session,
            timepoint_id=timepoint_id,
            component_id=comp_id,
            graph=comp_subgraph,
            df=df,
            is_original=False,
            bicliques=comp_info["bicliques"],
        )

    return comp_id


def get_dmr_details(dmr_nodes: Set[int], df: pd.DataFrame) -> List[Dict]:
    """Get detailed information for DMR nodes."""
    dmr_details = []
    for dmr_id in dmr_nodes:
        dmr_row = df[df["DMR_No."] == dmr_id + 1].iloc[0]
        dmr_details.append(
            {
                "id": dmr_id,
                "area": dmr_row["Area_Stat"] if "Area_Stat" in df.columns else "N/A",
                "description": dmr_row["DMR_Description"]
                if "DMR_Description" in df.columns
                else "N/A",
            }
        )
    return dmr_details


def get_gene_details(
    gene_nodes: Set[int], df: pd.DataFrame, gene_id_mapping: Dict
) -> List[Dict]:
    """Get detailed information for gene nodes."""
    gene_details = []
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    for gene_id in gene_nodes:
        gene_name = reverse_gene_mapping.get(gene_id, f"Unknown_{gene_id}")
        matching_rows = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        if not matching_rows.empty:
            gene_desc = matching_rows.iloc[0]["Gene_Description"]
            gene_details.append(
                {
                    "name": gene_name,
                    "description": gene_desc
                    if pd.notna(gene_desc) and gene_desc != "N/A"
                    else "N/A",
                }
            )
        else:
            gene_details.append({"name": gene_name, "description": "N/A"})
    return gene_details


def _get_gene_details(
    gene_nodes: Set[int], df: pd.DataFrame, gene_id_mapping: Dict
) -> List[Dict]:
    """Get detailed information for gene nodes."""
    gene_details = []
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    for gene_id in gene_nodes:
        gene_name = reverse_gene_mapping.get(gene_id, f"Unknown_{gene_id}")
        matching_rows = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        if not matching_rows.empty:
            gene_desc = matching_rows.iloc[0]["Gene_Description"]
            gene_details.append(
                {
                    "name": gene_name,
                    "description": gene_desc
                    if pd.notna(gene_desc) and gene_desc != "N/A"
                    else "N/A",
                }
            )
        else:
            gene_details.append({"name": gene_name, "description": "N/A"})
    return gene_details


def _get_dmr_details(dmr_nodes: Set[int], df: pd.DataFrame) -> List[Dict]:
    """Get detailed information for DMR nodes."""
    dmr_details = []
    for dmr_id in dmr_nodes:
        dmr_row = df[df["DMR_No."] == dmr_id + 1].iloc[0]
        dmr_details.append(
            {
                "id": dmr_id,
                "area": dmr_row["Area_Stat"] if "Area_Stat" in df.columns else "N/A",
                "description": dmr_row["DMR_Description"]
                if "DMR_Description" in df.columns
                else "N/A",
            }
        )
    return dmr_details


def _add_biclique_details(
    bicliques: List, df: pd.DataFrame, gene_id_mapping: Dict
) -> Dict:
    """Add detailed information for each biclique."""
    detailed_info = {}
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        detailed_info[f"biclique_{idx+1}_details"] = {
            "dmrs": _get_dmr_details(dmr_nodes, df),
            "genes": _get_gene_details(gene_nodes, df, gene_id_mapping),
        }
    return detailed_info
