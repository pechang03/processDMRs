"""Metadata creation utilities."""

from typing import Dict, List, Tuple, Set
import pandas as pd
from backend.app.utils.node_info import NodeInfo
import networkx as nx


def create_node_labels_and_metadata(
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    node_biclique_map: Dict[int, List[int]],
    graph: nx.Graph = None,
) -> Tuple[Dict, Dict, Dict]:
    """Create node labels and metadata for visualization."""
    # Create node info if graph is provided
    node_info = None
    if graph:
        node_info = NodeInfo(
            all_nodes=set(graph.nodes()),
            dmr_nodes={n for n, d in graph.nodes(data=True) if d["bipartite"] == 0},
            regular_genes={n for n, d in graph.nodes(data=True) if d["bipartite"] == 1},
            split_genes=set(),
            node_degrees={n: graph.degree(n) for n in graph.nodes()},
            min_gene_id=min(gene_id_mapping.values(), default=0),
        )

    # Create DMR metadata
    dmr_metadata = {}
    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
        dmr_metadata[f"DMR_{row['DMR_No.']}"] = {
            "area": str(row["Area_Stat"]) if "Area_Stat" in df.columns else "N/A",
            "description": str(row["Gene_Description"])
            if "Gene_Description" in df.columns
            else "N/A",
            "name": f"DMR_{row['DMR_No.']}",
            "bicliques": node_biclique_map.get(dmr_id, []),
            "node_type": node_info.get_node_type(dmr_id) if node_info else "DMR",
            "degree": node_info.get_node_degree(dmr_id) if node_info else 0,
        }

    # Create gene metadata
    gene_metadata = {}
    for gene_name, gene_id in gene_id_mapping.items():
        gene_matches = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        description = "N/A"
        if not gene_matches.empty and "Gene_Description" in gene_matches.columns:
            description = str(gene_matches.iloc[0]["Gene_Description"])

        gene_metadata[gene_name] = {
            "description": description,
            "id": gene_id,
            "bicliques": node_biclique_map.get(gene_id, []),
            "name": gene_name,
            "node_type": node_info.get_node_type(gene_id) if node_info else "gene",
            "degree": node_info.get_node_degree(gene_id) if node_info else 0,
        }

    # Create node labels
    node_labels = {}
    for dmr_id in dmr_metadata:
        node_labels[dmr_id] = dmr_metadata[dmr_id]["name"]
    for gene_name in gene_metadata:
        node_labels[gene_metadata[gene_name]["id"]] = gene_name

    return node_labels, dmr_metadata, gene_metadata


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
