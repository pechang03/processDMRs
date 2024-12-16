# File: Processor.py
# Author: Peter Shaw
#
from typing import Dict, List, Set, Tuple
import networkx as nx
import pandas as pd
from collections import defaultdict

# Removed data_loader import
from utils.json_utils import convert_for_json
from utils.node_info import NodeInfo
from utils import process_enhancer_info
from .classifier import BicliqueSizeCategory
from .classifier import classify_biclique


def process_dataset(
    df: pd.DataFrame, bipartite_graph: nx.Graph, gene_id_mapping: Dict[str, int]
):
    """Process a dataset with pre-loaded graph and dataframe.

    Args:
        df: Loaded dataframe
        bipartite_graph: Pre-created bipartite graph
        gene_id_mapping: Gene name to ID mapping

    Returns:
        Tuple of (bipartite_graph, dataframe, gene_id_mapping)
    """
    # Process enhancer information if not already processed
    if "Processed_Enhancer_Info" not in df.columns:
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

    return bipartite_graph, df, gene_id_mapping


# Add other helper functions...
def create_node_metadata(
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    node_biclique_map: Dict[int, List[int]],
    graph: nx.Graph = None,
) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """
    Create metadata dictionaries for DMRs and genes.

    Args:
        df: DataFrame containing DMR and gene information
        gene_id_mapping: Mapping of gene names to IDs
        node_biclique_map: Mapping of nodes to their bicliques
        graph: Optional NetworkX graph for additional node information

    Returns:
        Tuple of (dmr_metadata, gene_metadata)
    """
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

    return dmr_metadata, gene_metadata


def create_biclique_metadata(
    bicliques: List[Tuple[Set[int], Set[int]]], node_info: NodeInfo = None
) -> List[Dict]:
    """
    Create detailed metadata for each biclique.

    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        node_info: Optional NodeInfo object for additional node details

    Returns:
        List of dictionaries containing metadata for each biclique
    """

    metadata = []

    # Track nodes across all bicliques for overlap calculations
    all_dmrs = set()
    all_genes = set()
    node_to_bicliques = defaultdict(set)

    # First pass - collect basic info and track nodes
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        all_dmrs.update(dmr_nodes)
        all_genes.update(gene_nodes)

        # Track which bicliques each node belongs to
        for node in dmr_nodes | gene_nodes:
            node_to_bicliques[node].add(idx)

    # Second pass - create detailed metadata
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        # Calculate basic metrics
        size = len(dmr_nodes) + len(gene_nodes)
        density = len(dmr_nodes) * len(gene_nodes) / (size * size) if size > 0 else 0

        # Calculate overlap with other bicliques
        overlapping_bicliques = set()
        for node in dmr_nodes | gene_nodes:
            overlapping_bicliques.update(node_to_bicliques[node])
        overlapping_bicliques.discard(idx)  # Remove self

        # Calculate shared nodes with overlapping bicliques
        shared_nodes = {
            str(other_idx): len(
                (dmr_nodes | gene_nodes)
                & (bicliques[other_idx][0] | bicliques[other_idx][1])
            )
            for other_idx in overlapping_bicliques
        }

        # Get biclique classification
        category = classify_biclique(dmr_nodes, gene_nodes)

        # Create metadata dictionary
        biclique_metadata = {
            "id": idx,
            "size": {"total": size, "dmrs": len(dmr_nodes), "genes": len(gene_nodes)},
            "nodes": {
                "dmrs": sorted(str(n) for n in dmr_nodes),
                "genes": sorted(str(n) for n in gene_nodes),
            },
            "metrics": {
                "density": density,
                "dmr_ratio": len(dmr_nodes) / len(all_dmrs) if all_dmrs else 0,
                "gene_ratio": len(gene_nodes) / len(all_genes) if all_genes else 0,
                "edge_count": len(dmr_nodes) * len(gene_nodes),
            },
            "classification": {
                "category": category.name.lower(),
                "is_interesting": classify_biclique(dmr_nodes, gene_nodes)
                == BicliqueSizeCategory.INTERESTING,
            },
            "relationships": {
                "overlapping_bicliques": len(overlapping_bicliques),
                "shared_nodes": shared_nodes,
                "max_overlap": max(shared_nodes.values()) if shared_nodes else 0,
            },
            "node_details": {
                "dmrs": {
                    "types": [
                        node_info.get_node_type(n) if node_info else "DMR"
                        for n in dmr_nodes
                    ],
                    "degrees": [
                        node_info.get_node_degree(n) if node_info else 0
                        for n in dmr_nodes
                    ],
                },
                "genes": {
                    "types": [
                        node_info.get_node_type(n) if node_info else "gene"
                        for n in gene_nodes
                    ],
                    "degrees": [
                        node_info.get_node_degree(n) if node_info else 0
                        for n in gene_nodes
                    ],
                },
            },
        }

        metadata.append(biclique_metadata)

        # Convert to JSON-safe format
        return convert_for_json(metadata)
