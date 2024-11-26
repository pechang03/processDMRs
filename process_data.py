# File : process_data.py
# Author: Peter Shaw

# Author: Peter Shaw
#
# This file handles all data processing logic separate from web presentation.
# It serves as the main orchestrator for data analysis and visualization preparation.
#
# Responsibilities:
# - Read and process Excel data files
# - Create and analyze bipartite graphs
# - Process bicliques and their components
# - Generate visualization data
# - Create metadata for nodes
# - Calculate statistics
#
# Note: This separation allows the data processing logic to be used independently
# of the web interface, making it more maintainable and testable.

import os
import json
from typing import Dict, List, Set, Tuple
import networkx as nx
from flask import Flask, render_template, current_app
import pandas as pd
# import numpy as np

from utils.constants import START_GENE_ID

# from processDMR import read_excel_file,
from biclique_analysis import (
    process_bicliques,
    create_node_metadata,
    process_components,
    reporting,
)
from utils import process_enhancer_info
from biclique_analysis.edge_classification import classify_edges
from biclique_analysis.classifier import (
    BicliqueSizeCategory,
    classify_biclique,
    classify_component,
    classify_biclique_types,
)
from visualization import create_node_biclique_map, CircularBicliqueLayout, NodeInfo
from utils.node_info import NodeInfo
from utils.json_utils import convert_dict_keys_to_str

from data_loader import read_excel_file, create_bipartite_graph
from data_loader import validate_bipartite_graph
from rb_domination import (
    greedy_rb_domination,
    calculate_dominating_sets,
    print_domination_statistics,
    copy_dominating_set,
)

# Add missing imports and placeholder functions
from biclique_analysis.statistics import calculate_edge_coverage

app = Flask(__name__)

from data_loader import (
    DSS1_FILE,
    DSS_PAIRWISE_FILE,
    BIPARTITE_GRAPH_TEMPLATE,
    BIPARTITE_GRAPH_OVERALL,
    get_excel_sheets,
)


_cached_data = None


def convert_dict_keys_to_str(d):
    """Convert dictionary tuple keys to strings recursively and handle numpy types."""
    import numpy as np

    if isinstance(d, dict):
        return {
            "_".join(map(str, k))
            if isinstance(k, tuple)
            else str(k): convert_dict_keys_to_str(v)
            for k, v in d.items()
        }
    elif isinstance(d, list):
        return [convert_dict_keys_to_str(i) for i in d]
    elif isinstance(d, set):
        return sorted(list(d))
    elif isinstance(d, tuple):
        return list(d)
    elif isinstance(
        d,
        (
            np.int_,
            np.intc,
            np.intp,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
        ),
    ):
        return int(d)
    elif isinstance(d, (np.float_, np.float16, np.float32, np.float64)):
        return float(d)
    elif isinstance(d, np.ndarray):
        return d.tolist()
    elif isinstance(d, np.bool_):
        return bool(d)
    return d


def process_single_timepoint(df: pd.DataFrame, timepoint: str, gene_id_mapping: Dict[str, int] = None) -> Dict:
    """Process a single timepoint and return its results"""
    try:
        # Create bipartite graph
        graph = create_bipartite_graph(df, gene_id_mapping, timepoint)
        
        # Validate graph
        print(f"\nValidating graph for timepoint {timepoint}")
        filtered_graph = validate_bipartite_graph(graph)
        if filtered_graph is False:
            return {"error": "Graph validation failed"}
        graph = filtered_graph  # Use the filtered graph going forward
        graph_valid = True

        # Process bicliques for this timepoint
        bicliques_result = process_bicliques(
            graph,
            f"bipartite_graph_output_{timepoint}.txt",
            timepoint,
            gene_id_mapping=gene_id_mapping,
        )

        # Calculate statistics for this timepoint
        biclique_type_stats = classify_biclique_types(
            bicliques_result.get("bicliques", [])
        )

        return {
            "bicliques": bicliques_result,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "graph_valid": graph_valid,
            "biclique_type_stats": biclique_type_stats,
            "coverage": bicliques_result.get("coverage", {}),
            "size_distribution": bicliques_result.get("size_distribution", {}),
            "gene_id_mapping": gene_id_mapping  # Add this to return the mapping
        }
    except Exception as e:
        return {"error": str(e)}


def process_data():
    """Process all timepoints including overall/DSS1"""
    try:
        timepoint_data = {}

        # Process overall/DSS1 timepoint first
        print("\nProcessing overall timepoint (DSS1)...")
        df_overall = read_excel_file(current_app.config["DSS1_FILE"])
        overall_results = process_single_timepoint(
            df=df_overall,
            timepoint="overall",
            gene_id_mapping=None,  # Will create master mapping
        )
        timepoint_data["overall"] = overall_results

        # Use the master gene mapping for all other timepoints
        gene_id_mapping = overall_results["gene_id_mapping"]

        # Process each pairwise timepoint
        xl = pd.ExcelFile(current_app.config["DSS_PAIRWISE_FILE"])
        for sheet in xl.sheet_names:
            print(f"\nProcessing timepoint: {sheet}")
            df = read_excel_file(
                current_app.config["DSS_PAIRWISE_FILE"], sheet_name=sheet
            )
            timepoint_results = process_single_timepoint(
                df=df, timepoint=sheet, gene_id_mapping=gene_id_mapping
            )
            timepoint_data[sheet] = timepoint_results

        return timepoint_data
    except Exception as e:
        print(f"Error in process_data: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def process_single_timepoint(
    df: pd.DataFrame, timepoint: str, gene_id_mapping: Dict[str, int] = None
) -> Dict:
    """Process a single timepoint and return its complete analysis"""

    # Create bipartite graph
    if gene_id_mapping is None:
        # Create master mapping for overall timepoint
        gene_id_mapping = create_master_gene_mapping(df)

    graph = create_bipartite_graph(df, gene_id_mapping, timepoint)

    # Remove degree-0 gene nodes before analysis
    filtered_graph = remove_isolated_genes(graph)
    print(f"\nTimepoint {timepoint}:")
    print(f"Original graph: {len(graph.nodes())} nodes, {len(graph.edges())} edges")
    print(
        f"Filtered graph: {len(filtered_graph.nodes())} nodes, {len(filtered_graph.edges())} edges"
    )

    # Process bicliques on filtered graph
    bicliques_result = process_bicliques(
        filtered_graph,
        f"bipartite_graph_output_{timepoint}.txt",
        timepoint,
        gene_id_mapping=gene_id_mapping,
    )

    # Process components - unpack the tuple returned by process_components
    (complex_components, interesting_components, simple_components, 
     non_simple_components, component_stats, statistics) = process_components(
        graph, bicliques_result
    )

    # Generate embeddings for both types of components
    triconnected_embeddings = generate_triconnected_embeddings(graph)
    biclique_embeddings = generate_biclique_embeddings(bicliques_result["bicliques"])

    return {
        "summary": {
            "coverage": bicliques_result["coverage"],
            "edge_coverage": calculate_edge_coverage(
                bicliques_result["bicliques"], graph
            ),
            "component_stats": component_stats,  # Use the unpacked value
            "biclique_types": classify_biclique_types(bicliques_result["bicliques"]),
            "size_distribution": bicliques_result["size_distribution"],
        },
        "graphs": {
            "original": graph,
            "biclique": create_biclique_graph(bicliques_result["bicliques"]),
        },
        "interesting_components": interesting_components,  # Use the unpacked value
        "component_tables": {
            "triconnected": {
                "embeddings": triconnected_embeddings,
                "metadata": create_triconnected_metadata(graph),
            },
            "biclique": {
                "embeddings": biclique_embeddings,
                "metadata": create_biclique_metadata(bicliques_result["bicliques"]),
            },
        },
        "gene_id_mapping": gene_id_mapping,
        "node_metadata": {
            "dmr": create_dmr_metadata(df),
            "gene": create_gene_metadata(df),
        },
    }


# Add placeholder functions for missing metadata creation
def create_dmr_metadata(df: pd.DataFrame) -> Dict:
    """Create metadata for DMRs"""
    return {
        str(row["DMR_No."]): {
            "area": row.get("Area_Stat", "N/A"),
            "description": row.get("Gene_Description", "N/A"),
        }
        for _, row in df.iterrows()
    }


def create_gene_metadata(df: pd.DataFrame) -> Dict:
    """Create metadata for genes"""
    gene_metadata = {}

    # Check for gene symbol column
    gene_col = next(
        (col for col in ["Gene_Symbol_Nearby", "Gene_Symbol"] if col in df.columns),
        None,
    )

    if gene_col:
        for _, row in df.iterrows():
            gene_name = row.get(gene_col)
            if gene_name:
                gene_metadata[gene_name] = {
                    "description": row.get("Gene_Description", "N/A")
                }

    return gene_metadata


def create_master_gene_mapping(df: pd.DataFrame) -> Dict[str, int]:
    """Create a master gene mapping from a DataFrame"""
    all_genes = set()

    # Add genes from gene column (case-insensitive)
    gene_names = df["Gene_Symbol_Nearby"].dropna().str.strip().str.lower()
    all_genes.update(gene_names)

    # Add genes from enhancer info (case-insensitive)
    df["Processed_Enhancer_Info"] = df[
        "ENCODE_Enhancer_Interaction(BingRen_Lab)"
    ].apply(process_enhancer_info)

    for genes in df["Processed_Enhancer_Info"]:
        if genes:
            all_genes.update(g.strip().lower() for g in genes)

    # Sort genes alphabetically for deterministic assignment
    sorted_genes = sorted(all_genes)
    max_dmr = df["DMR_No."].max()

    # Create gene mapping starting after max DMR number

    gene_id_mapping = {
        gene: START_GENE_ID + idx for idx, gene in enumerate(sorted_genes)
    }

    return gene_id_mapping


def create_biclique_graph(bicliques: List[Tuple[Set[int], Set[int]]]) -> nx.Graph:
    """Create a biclique graph from bicliques"""
    biclique_graph = nx.Graph()
    for dmr_nodes, gene_nodes in bicliques:
        biclique_graph.add_nodes_from(dmr_nodes, bipartite=0)
        biclique_graph.add_nodes_from(gene_nodes, bipartite=1)
        biclique_graph.add_edges_from(
            (dmr, gene) for dmr in dmr_nodes for gene in gene_nodes
        )
    return biclique_graph


def remove_isolated_genes(graph: nx.Graph) -> nx.Graph:
    """Remove gene nodes with degree 0 from the graph."""
    filtered_graph = graph.copy()

    # Find gene nodes with degree 0
    isolated_genes = [
        node
        for node, degree in filtered_graph.degree()
        if degree == 0 and filtered_graph.nodes[node]["bipartite"] == 1
    ]

    # Remove isolated genes
    filtered_graph.remove_nodes_from(isolated_genes)

    return filtered_graph


def get_isolated_genes(
    graph: nx.Graph, gene_id_mapping: Dict[str, int]
) -> Dict[str, List[str]]:
    """Get information about isolated genes for reporting."""
    reverse_mapping = {v: k for k, v in gene_id_mapping.items()}

    isolated_genes = [
        reverse_mapping[node]
        for node, degree in graph.degree()
        if degree == 0 and graph.nodes[node]["bipartite"] == 1
    ]

    return {"count": len(isolated_genes), "genes": sorted(isolated_genes)}


def generate_triconnected_embeddings(graph: nx.Graph) -> List[Dict]:
    """Generate embeddings for triconnected components"""
    # Placeholder implementation
    return []


def generate_biclique_embeddings(
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> List[Dict]:
    """Generate embeddings for biclique components"""
    # Placeholder implementation
    return []


def create_triconnected_metadata(graph: nx.Graph) -> List[Dict]:
    """Create metadata for triconnected components"""
    # Placeholder implementation
    return []


def create_biclique_metadata(bicliques: List[Tuple[Set[int], Set[int]]]) -> List[Dict]:
    """Create metadata for biclique components"""
    # Placeholder implementation
    return []


# Removed duplicate function definition
