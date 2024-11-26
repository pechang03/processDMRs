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
from utils.id_mapping import create_gene_mapping

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
from biclique_analysis.statistics import (
    analyze_components,
    calculate_biclique_statistics,
    calculate_coverage_statistics,
    calculate_component_statistics,
)
from biclique_analysis.triconnected import analyze_triconnected_components
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


def process_single_timepoint(
    df: pd.DataFrame, timepoint: str, gene_id_mapping: Dict[str, int] = None
) -> Dict:
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
            "gene_id_mapping": gene_id_mapping,  # Add this to return the mapping
        }
    except Exception as e:
        return {"error": str(e)}


def create_master_gene_mapping(df: pd.DataFrame) -> Dict[str, int]:
    """Create a master gene mapping from a DataFrame."""
    all_genes = set()

    # Add genes from gene column (case-insensitive)
    gene_col = next(
        (col for col in ["Gene_Symbol_Nearby", "Gene_Symbol", "Gene"] if col in df.columns),
        None
    )
    if gene_col:
        gene_names = df[gene_col].dropna().str.strip().str.lower()
        all_genes.update(gene_names)

    # Add genes from enhancer info
    df["Processed_Enhancer_Info"] = df[
        "ENCODE_Enhancer_Interaction(BingRen_Lab)"
    ].apply(process_enhancer_info)

    for genes in df["Processed_Enhancer_Info"]:
        if genes:
            all_genes.update(g.strip().lower() for g in genes)

    # Use utility function to create mapping
    max_dmr_id = df["DMR_No."].max() - 1  # Convert to 0-based index
    return create_gene_mapping(all_genes, max_dmr_id)


def process_overall_timepoint(df: pd.DataFrame) -> Dict:
    """Process the overall DSS1 timepoint."""
    gene_id_mapping = create_master_gene_mapping(df)
    return process_timepoint(df, "DSS1", gene_id_mapping)


# Removed process_pairwise_timepoints function


def process_data():
    """Process all timepoints including overall/DSS1 with configurable layouts"""
    try:
        # Define layout options for different timepoint types
        layout_options = {
            "overall": {
                "triconnected": "spring",
                "bicliques": "circular",
                "default": "original"
            },
            "pairwise": {
                "triconnected": "spring",
                "bicliques": "circular",
                "default": "original"
            }
        }

        # Process overall/DSS1 timepoint first
        print("\nProcessing overall timepoint (DSS1)...", flush=True)
        df_overall = read_excel_file(current_app.config["DSS1_FILE"])

        # Create master gene mapping
        gene_id_mapping = create_master_gene_mapping(df_overall)

        # Initialize timepoint data dictionary
        timepoint_data = {}

        # Process DSS1 timepoint
        timepoint_data["overall"] = process_timepoint(
            df_overall, 
            "DSS1", 
            gene_id_mapping, 
            layout_options["overall"]
        )

        # Process pairwise timepoints
        pairwise_file = current_app.config["DSS_PAIRWISE_FILE"]
        xl = pd.ExcelFile(pairwise_file)
        
        for sheet_name in xl.sheet_names:
            print(f"\nProcessing pairwise timepoint: {sheet_name}", flush=True)
            try:
                # Read each sheet directly into a DataFrame
                df = pd.read_excel(pairwise_file, sheet_name=sheet_name)
                if not df.empty:
                    # Process the timepoint with the DataFrame
                    timepoint_data[sheet_name] = process_timepoint(
                        df,
                        sheet_name,
                        gene_id_mapping,
                        layout_options["pairwise"]
                    )
                else:
                    print(f"Empty sheet: {sheet_name}", flush=True)
                    timepoint_data[sheet_name] = {
                        "status": "error",
                        "message": "Empty sheet"
                    }
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {str(e)}", flush=True)
                timepoint_data[sheet_name] = {
                    "status": "error",
                    "message": str(e)
                }

        return timepoint_data

    except Exception as e:
        print(f"Error in process_data: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def process_timepoint(
    df, 
    timepoint, 
    gene_id_mapping, 
    layout_options=None
):
    """Process a single timepoint with configurable layout options."""
    try:
        # Verify we have a DataFrame
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"Expected DataFrame for {timepoint}, got {type(df)}")
            
        # Create bipartite graph
        graph = create_bipartite_graph(df, gene_id_mapping, timepoint)
        
        # Get connected components
        connected_components = list(nx.connected_components(graph))
        biconnected_components = list(nx.biconnected_components(graph))
        
        # Call without layout parameter
        triconnected_components, triconnected_stats = analyze_triconnected_components(graph)

        # Calculate component statistics
        component_stats = {
            "original": {
                "connected": analyze_components(connected_components, graph),
                "biconnected": analyze_components(biconnected_components, graph),
                "triconnected": triconnected_stats
            },
            "biclique": {
                "connected": {},
                "biconnected": {},
                "triconnected": {}
            }
        }

        # Calculate coverage statistics
        coverage_stats = calculate_coverage_statistics([], graph)  # Empty bicliques for now

        # Structure the return data to match template expectations
        return {
            "status": "success",
            "stats": {
                "components": component_stats,
                "coverage": coverage_stats,
                "edge_coverage": calculate_edge_coverage([], graph),
                "biclique_types": {
                    "empty": 0,
                    "simple": 0,
                    "interesting": 0,
                    "complex": 0
                },
                "size_distribution": {},
                "dominating_set": {
                    "size": 0,
                    "percentage": 0,
                    "genes_dominated": 0,
                    "components_with_ds": 0,
                    "avg_size_per_component": 0
                }
            },
            "coverage": coverage_stats,
            "components": component_stats,  # Direct access path
            "layout_used": layout_options
        }

    except Exception as e:
        print(f"Error processing timepoint {timepoint}: {str(e)}", flush=True)
        return {
            "status": "error",
            "message": str(e)
        }
        biclique_file = f"bipartite_graph_output_{timepoint}.txt"
        if os.path.exists(biclique_file):
            print(f"Processing bicliques from {biclique_file}", flush=True)
            bicliques_result = process_bicliques(
                graph, 
                biclique_file,
                timepoint, 
                gene_id_mapping=gene_id_mapping,
                layout=layout_options.get("bicliques", "circular")
            )
            
            # Process biclique graph components if bicliques found
            if bicliques_result and "bicliques" in bicliques_result:
                print(f"Creating biclique graph for {timepoint}...", flush=True)
                biclique_graph = nx.Graph()
                for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
                    biclique_graph.add_nodes_from(dmr_nodes, bipartite=0)
                    biclique_graph.add_nodes_from(gene_nodes, bipartite=1)
                    biclique_graph.add_edges_from((d, g) for d in dmr_nodes for g in gene_nodes)

                # Calculate statistics for biclique graph
                biclique_connected = list(nx.connected_components(biclique_graph))
                biclique_biconnected = list(nx.biconnected_components(biclique_graph))
                biclique_triconnected, biclique_tri_stats = analyze_triconnected_components(
                    biclique_graph, 
                    layout=layout_options.get("triconnected", "spring")
                )

                component_stats["components"]["biclique"] = {
                    "connected": analyze_components(
                        biclique_connected, 
                        biclique_graph, 
                        layout=layout_options.get("default", "original")
                    ),
                    "biconnected": analyze_components(
                        biclique_biconnected, 
                        biclique_graph, 
                        layout=layout_options.get("default", "original")
                    ),
                    "triconnected": biclique_tri_stats,
                }
                
                statistics = calculate_biclique_statistics(bicliques_result["bicliques"], graph)
            else:
                print(f"No bicliques found for {timepoint}", flush=True)
                bicliques_result = {"bicliques": []}
                statistics = {}
        else:
            print(f"Biclique file not found for {timepoint}", flush=True)
            bicliques_result = {"bicliques": []}
            statistics = {}

        # Structure the return data to match template expectations
        return {
            "status": "success",
            "stats": component_stats,
            "coverage": calculate_coverage_statistics(bicliques_result.get("bicliques", []), graph),
            "biclique_types": statistics.get("biclique_types", {
                "empty": 0,
                "simple": 0,
                "interesting": 0,
                "complex": 0
            }),
            "components": component_stats["components"],
            "layout_used": layout_options,  # Add layout information
        }

    except Exception as e:
        print(f"Error processing timepoint {timepoint}: {str(e)}", flush=True)
        return {
            "status": "error",
            "message": str(e)
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
