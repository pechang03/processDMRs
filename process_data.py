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
import logging
from typing import Dict, List, Set, Tuple
import networkx as nx
from flask import current_app
from extensions import app
import pandas as pd

from utils.constants import (
    DSS1_FILE,
    DSS_PAIRWISE_FILE,
    BIPARTITE_GRAPH_TEMPLATE,
    BIPARTITE_GRAPH_OVERALL,
    START_GENE_ID,
)
from utils.id_mapping import create_gene_mapping
from utils import process_enhancer_info

from utils.json_utils import (
    convert_dict_keys_to_str, 
    convert_for_json, 
    convert_sets_to_lists
)

from biclique_analysis import (
    process_bicliques,
    create_node_metadata,
    process_components,
    reporting,
)
from biclique_analysis.edge_classification import classify_edges
from biclique_analysis.classifier import (
    BicliqueSizeCategory,
    classify_biclique,
    classify_component,
    classify_biclique_types,
)

# from biclique_analysis.embeddings import (
#    generate_triconnected_embeddings,
#    generate_biclique_embeddings,
# )

from biclique_analysis.processor import (
    create_biclique_metadata,
)

# Add missing imports and placeholder functions

from biclique_analysis.statistics import (
    analyze_components,
    calculate_edge_coverage,
    # calculate_biclique_statistics,
    calculate_coverage_statistics,
    calculate_component_statistics,
    analyze_biconnected_components,
)

from biclique_analysis.triconnected import analyze_triconnected_components
# from rb_domination import (
#    greedy_rb_domination,
#    calculate_dominating_sets,
#    print_domination_statistics,
#    copy_dominating_set,
# )


# from visualization import create_node_biclique_map, CircularBicliqueLayout

from data_loader import (
    # get_excel_sheets,
    read_excel_file,
    create_bipartite_graph,
    validate_bipartite_graph,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# _cached_data = None


# Removed: convert_dict_keys_to_str function (now imported from utils.json_utils)


def create_master_gene_mapping(df: pd.DataFrame) -> Dict[str, int]:
    """Create a master gene mapping from a DataFrame."""
    all_genes = set()

    # Add genes from gene column (case-insensitive)
    gene_col = next(
        (col for col in ["Gene_Symbol_Nearby", "Gene_Symbol", "Gene"] if col in df.columns),
        None
    )
    if gene_col:
        # Filter out empty values, ".", "N/A" etc.
        gene_names = df[gene_col].dropna().str.strip().str.lower()
        valid_genes = {g for g in gene_names if g and g != "." and g.lower() != "n/a"}
        all_genes.update(valid_genes)

    # Add genes from enhancer info
    df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
    
    for genes in df["Processed_Enhancer_Info"]:
        if genes:  # Only process non-empty gene lists
            # Filter out invalid entries
            valid_genes = {g.strip().lower() for g in genes if g.strip() and g.strip() != "." and g.strip().lower() != "n/a"}
            all_genes.update(valid_genes)

    # Remove any remaining invalid entries
    all_genes = {g for g in all_genes if g and g != "." and g.lower() != "n/a"}

    # Use utility function to create mapping
    max_dmr_id = df["DMR_No."].max() - 1  # Convert to 0-based index
    
    print("\nGene mapping creation debug:")
    print(f"Total valid genes found: {len(all_genes)}")
    print("First 5 valid genes:", sorted(list(all_genes))[:5])
    
    return create_gene_mapping(all_genes, max_dmr_id)


def process_DSStimeseries_timepoint(df: pd.DataFrame) -> Dict:
    """Process the overall DSS1 timepoint."""
    gene_id_mapping = create_master_gene_mapping(df)
    return process_timepoint(df, "DSS1", gene_id_mapping)


# Removed process_pairwise_timepoints function


def process_data():
    """Process all timepoints including DSStimeseries with configurable layouts"""
    try:
        # Define layout options for different timepoint types
        layout_options = {
            "DSStimeseries": {
                "triconnected": "spring",
                "bicliques": "circular",
                "default": "original",
            },
            "pairwise": {
                "triconnected": "spring",
                "bicliques": "circular",
                "default": "original",
            },
        }

        # Initialize timepoint data dictionary
        timepoint_data = {}

        # Process DSStimeseries timepoint first
        print("\nProcessing DSStimeseries timepoint...", flush=True)
        df_DSStimeseries = read_excel_file(app.config["DSS1_FILE"])

        # Create master gene mapping
        gene_id_mapping = create_master_gene_mapping(df_DSStimeseries)

        # Process DSStimeseries timepoint (no longer using "overall")
        timepoint_data["DSStimeseries"] = process_timepoint(
            df_DSStimeseries, 
            "DSStimeseries",  # Use consistent timepoint name
            gene_id_mapping, 
            layout_options["DSStimeseries"]
        )

        # Process pairwise timepoints
        pairwise_file = app.config["DSS_PAIRWISE_FILE"]
        xl = pd.ExcelFile(pairwise_file)

        for sheet_name in xl.sheet_names:
            print(f"\nProcessing pairwise timepoint: {sheet_name}", flush=True)
            try:
                # Read each sheet directly into a DataFrame
                df = pd.read_excel(pairwise_file, sheet_name=sheet_name)
                if not df.empty:
                    # Process the timepoint with the DataFrame
                    timepoint_data[sheet_name] = process_timepoint(
                        df, sheet_name, gene_id_mapping, layout_options["pairwise"]
                    )
                else:
                    print(f"Empty sheet: {sheet_name}", flush=True)
                    timepoint_data[sheet_name] = {
                        "status": "error",
                        "message": "Empty sheet",
                    }
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {str(e)}", flush=True)
                timepoint_data[sheet_name] = {"status": "error", "message": str(e)}

        # Convert entire timepoint_data to JSON-safe format
        return convert_for_json(timepoint_data)

    except Exception as e:
        print(f"Error in process_data: {str(e)}", flush=True)
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def process_timepoint(df, timepoint, gene_id_mapping, layout_options=None):
    """Process a single timepoint with configurable layout options."""
    try:
        print(f"\nProcessing timepoint {timepoint}")

        # Create bipartite graph
        print("Creating bipartite graph...")
        graph = create_bipartite_graph(df, gene_id_mapping, timepoint)
        print(
            f"Graph created with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges"
        )

        # Validate graph
        print(f"\nValidating graph for timepoint {timepoint}")
        filtered_graph = validate_bipartite_graph(graph)

        # Debug logging for JSON conversion
        def debug_json_conversion(data, name):
            print(f"\nDebug: Converting {name} to JSON-safe format")
            print(f"Before conversion - Type: {type(data)}")
            try:
                converted = convert_for_json(data)
                print(f"After conversion - Type: {type(converted)}")
                print(f"Conversion of {name} successful")
                return converted
            except Exception as e:
                print(f"Error converting {name}: {str(e)}")
                return data
        if filtered_graph is False:
            return {"error": "Graph validation failed"}
        graph = filtered_graph  # Use the filtered graph going forward
        print("Graph validation successful")

        # Look for biclique file using constants
        if timepoint == "DSStimeseries":
            biclique_file = BIPARTITE_GRAPH_OVERALL
        else:
            biclique_file = BIPARTITE_GRAPH_TEMPLATE.format(timepoint)

        print(f"\nLooking for biclique file: {biclique_file}")
        print(f"File exists: {os.path.exists(biclique_file)}")

        if os.path.exists(biclique_file):
            print(f"Processing bicliques from {biclique_file}")
            # Use processor.py to process bicliques
            bicliques_result = process_bicliques(
                graph,
                biclique_file,
                timepoint,
                gene_id_mapping=gene_id_mapping,
                file_format="gene-name",
            )

            if bicliques_result and "bicliques" in bicliques_result:
                # Process components using components.py
                (
                    complex_components,
                    interesting_components,
                    simple_components,  # Add this variable
                    non_simple_components,
                    component_stats,
                    statistics,
                ) = process_components(
                    graph,
                    bicliques_result,
                    dmr_metadata=create_dmr_metadata(df),
                    gene_metadata=create_gene_metadata(df),
                    gene_id_mapping=gene_id_mapping,
                )

                # For all timepoints, analyze original graph components
                print(f"\nAnalyzing graph components for {timepoint}")

                # Analyze connected components
                connected_comps = list(nx.connected_components(graph))
                print(f"Found {len(connected_comps)} connected components")
                original_stats = analyze_components(connected_comps, graph)
                print("Connected component statistics:")
                print(json.dumps(original_stats, indent=2))

                # Analyze biconnected components
                biconn_comps, biconn_stats = analyze_biconnected_components(graph)
                print("\nBiconnected component statistics:")
                print(json.dumps(biconn_stats, indent=2))

                # Analyze triconnected components
                triconn_comps, triconn_stats = analyze_triconnected_components(graph)
                print("\nTriconnected component statistics:")
                print(json.dumps(triconn_stats, indent=2))

                # Add to component_stats
                if "components" not in component_stats:
                    component_stats["components"] = {}
                if "original" not in component_stats["components"]:
                    component_stats["components"]["original"] = {}

                component_stats["components"]["original"] = {
                    "connected": {
                        "components": connected_comps,
                        "stats": original_stats,
                    },
                    "biconnected": {"components": biconn_comps, "stats": biconn_stats},
                    "triconnected": {
                        "components": triconn_comps,
                        "stats": triconn_stats,
                    },
                }

                print("\nFinal component statistics for original graph:")
                try:
                    print(
                        json.dumps(
                            convert_dict_keys_to_str(component_stats["components"]["original"]),
                            indent=2,
                        )
                    )
                except Exception as e:
                    print(f"Error converting stats to JSON: {e}")

                # Calculate coverage statistics
                coverage_stats = calculate_coverage_statistics(
                    bicliques_result["bicliques"], graph
                )
                edge_coverage = calculate_edge_coverage(
                    bicliques_result["bicliques"], graph
                )

                # Get bicliques summary
                from biclique_analysis.reporting import get_bicliques_summary
                from utils.json_utils import convert_for_json
        
                bicliques_summary = get_bicliques_summary(bicliques_result, graph)
                # Convert to JSON-safe format before using
                bicliques_summary = convert_for_json(bicliques_summary)
        
                # Now safe to print
                print("\nDebug: Generated Bicliques Summary:")
                print(json.dumps(bicliques_summary, indent=2))

                # Use debug conversion function
                return {
                    "status": "success",
                    "stats": {
                        "components": debug_json_conversion(component_stats, "component_stats"),
                        "coverage": debug_json_conversion(coverage_stats, "coverage_stats"),
                        "edge_coverage": debug_json_conversion(edge_coverage, "edge_coverage"),
                        "biclique_types": debug_json_conversion(
                            classify_biclique_types(bicliques_result["bicliques"]), 
                            "biclique_types"
                        ),
                        "bicliques_summary": debug_json_conversion(bicliques_summary, "bicliques_summary"),
                        # Move these inside stats
                        "interesting_components": debug_json_conversion(interesting_components, "interesting_components"),
                        "complex_components": debug_json_conversion(complex_components, "complex_components"),
                        "non_simple_components": debug_json_conversion(non_simple_components, "non_simple_components")
                    },
                    "layout_used": debug_json_conversion(layout_options, "layout_options"),
                    "bipartite_graph": graph
                }

        # Return basic statistics if no bicliques found
        return {
            "status": "success",
            "stats": {
                "components": calculate_component_statistics([], graph),
                "coverage": {
                    "dmrs": {"covered": 0, "total": 0, "percentage": 0},
                    "genes": {"covered": 0, "total": 0, "percentage": 0},
                    "edges": {
                        "single_coverage": 0,
                        "multiple_coverage": 0,
                        "uncovered": 0,
                        "total": 0,
                        "single_percentage": 0,
                        "multiple_percentage": 0,
                        "uncovered_percentage": 0,
                    },
                },
                "biclique_types": {
                    "empty": 0,
                    "simple": 0,
                    "interesting": 0,
                    "complex": 0,
                },
            },
            "complex_components": [],
            "interesting_components": [],
            "non_simple_components": [],
            "layout_used": layout_options,
            "bipartite_graph": graph,
        }

    except Exception as e:
        print(f"Error processing timepoint {timepoint}: {str(e)}", flush=True)
        import traceback

        traceback.print_exc()
        return {"status": "error", "message": str(e)}


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
