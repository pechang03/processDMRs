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
from flask import Flask, render_template
import pandas as pd

# from processDMR import read_excel_file,
from biclique_analysis import (
    process_bicliques,
    process_enhancer_info,
    create_node_metadata,
    process_components,
    reporting,  # Add this import
)
from biclique_analysis.edge_classification import classify_edges
from biclique_analysis.classifier import (
    BicliqueSizeCategory,
    classify_biclique,
    classify_component,
    classify_biclique_types
)
from visualization import create_node_biclique_map, CircularBicliqueLayout, NodeInfo
from visualization.node_info import NodeInfo
from graph_utils import read_excel_file, create_bipartite_graph
from rb_domination import (
    greedy_rb_domination,
    calculate_dominating_sets,
    print_domination_statistics,
    copy_dominating_set,
)

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DSS1_FILE = os.path.join(DATA_DIR, "DSS1.xlsx")
HOME1_FILE = os.path.join(DATA_DIR, "HOME1.xlsx")
BICLIQUES_FILE = os.path.join(DATA_DIR, "bipartite_graph_output.txt.biclusters")


_cached_data = None


def convert_dict_keys_to_str(d):
    """Convert dictionary tuple keys to strings recursively."""
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
        return list(d)  # Convert sets to lists for JSON serialization
    return d


def convert_dict_keys_to_str(d):
    """Convert dictionary tuple keys to strings recursively."""
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
        return list(d)  # Convert sets to lists for JSON serialization
    return d


def process_data():
    """Process the DMR data and return results"""
    global _cached_data

    # Return cached data if available
    if _cached_data is not None:
        return _cached_data

    try:
        print("Starting initial data processing...")
        print(f"Using data directory: {DATA_DIR}")

        # Process DSS1 dataset
        df = read_excel_file(DSS1_FILE)
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Create gene ID mapping
        all_genes = set()
        # First pass: Collect and normalize all gene names
        all_genes = set()

        # Add genes from gene column (case-insensitive)
        gene_names = df["Gene_Symbol_Nearby"].dropna().str.strip().str.lower()
        all_genes.update(gene_names)

        # Add genes from enhancer info (case-insensitive)
        for genes in df["Processed_Enhancer_Info"]:
            if genes:  # Check if not None/empty
                all_genes.update(g.strip().lower() for g in genes)

        # Sort genes alphabetically for deterministic assignment
        sorted_genes = sorted(all_genes)

        # Create gene mapping starting after max DMR number
        max_dmr = df["DMR_No."].max()
        gene_id_mapping = {
            gene: idx + max_dmr + 1 for idx, gene in enumerate(sorted_genes)
        }

        print("\nGene ID Mapping Statistics:")
        print(f"Total unique genes (case-insensitive): {len(all_genes)}")
        print(f"ID range: {max_dmr + 1} to {max(gene_id_mapping.values())}")
        print("\nFirst 5 gene mappings:")
        for gene in sorted_genes[:5]:
            print(f"{gene}: {gene_id_mapping[gene]}")

        # Create gene mapping starting after max DMR number
        max_dmr = df["DMR_No."].max()
        gene_id_mapping = {
            gene: idx + max_dmr + 1
            for idx, gene in enumerate(
                sorted(all_genes)
            )  # Sort for deterministic assignment
        }

        print("\nGene ID Mapping Statistics:")
        print(f"Total unique genes: {len(all_genes)}")
        print(f"ID range: {max_dmr + 1} to {max(gene_id_mapping.values())}")
        print("\nFirst 5 gene mappings:")
        for gene in sorted(list(all_genes))[:5]:
            print(f"{gene}: {gene_id_mapping[gene]}")

        bipartite_graph = create_bipartite_graph(df, gene_id_mapping)

        # Process bicliques
        print("Processing bicliques...")
        bicliques_result = process_bicliques(
            bipartite_graph,
            BICLIQUES_FILE,
            max(df["DMR_No."]),
            "DSS1",
            gene_id_mapping=gene_id_mapping,
            file_format=app.config.get(
                "BICLIQUE_FORMAT", "gene_name"
            ),  # Get format from app config
        )

        # Get header statistics from bicliques file
        header_stats = bicliques_result.get("statistics", {})

        # Validate against header statistics
        if header_stats:
            print("\nValidating against header statistics:")
            dmr_stats = header_stats["coverage"]["dmrs"]
            gene_stats = header_stats["coverage"]["genes"]
            print(
                f"DMR Coverage - Header: {dmr_stats['covered']}/{dmr_stats['total']} ({dmr_stats['percentage']:.1%})"
            )
            print(
                f"Gene Coverage - Header: {gene_stats['covered']}/{gene_stats['total']} ({gene_stats['percentage']:.1%})"
            )

            # Compare size distribution
            print("\nBiclique size distribution from header:")
            for (dmrs, genes), count in header_stats["size_distribution"].items():
                print(f"{dmrs} DMRs, {genes} genes: {count} bicliques")

        # Create node_biclique_map
        node_biclique_map = create_node_biclique_map(bicliques_result["bicliques"])

        # Create metadata
        print("Creating metadata...")
        dmr_metadata, gene_metadata = create_node_metadata(
            df, gene_id_mapping, node_biclique_map
        )

        # Calculate positions
        # Use circular layout for biclique visualization
        biclique_layout = CircularBicliqueLayout()
        node_positions = biclique_layout.calculate_positions(
            bipartite_graph,
            NodeInfo(
                all_nodes=set(bipartite_graph.nodes()),
                dmr_nodes={
                    n
                    for n, d in bipartite_graph.nodes(data=True)
                    if d["bipartite"] == 0
                },
                regular_genes={
                    n
                    for n, d in bipartite_graph.nodes(data=True)
                    if d["bipartite"] == 1
                },
                split_genes=set(),
                node_degrees={
                    n: len(list(bipartite_graph.neighbors(n)))
                    for n in bipartite_graph.nodes()
                },
                min_gene_id=min(gene_id_mapping.values(), default=0),
            ),
        )

        # Create node labels and metadata
        node_labels, dmr_metadata, gene_metadata = (
            reporting.create_node_labels_and_metadata(
                df, bicliques_result, gene_id_mapping, node_biclique_map
            )
        )
        # Calculate dominating set for original graph
        print("\nCalculating dominating set...")
        dominating_set = calculate_dominating_sets(bipartite_graph, df)
        print(f"Found dominating set of size {len(dominating_set)}")

        # Build biclique_graph from bicliques
        biclique_graph = nx.Graph()
        for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
            biclique_graph.add_nodes_from(dmr_nodes, bipartite=0)
            biclique_graph.add_nodes_from(gene_nodes, bipartite=1)
            biclique_graph.add_edges_from(
                (dmr, gene) for dmr in dmr_nodes for gene in gene_nodes
            )

        # Process components first
        print("Processing components...")
        (
            complex_components,
            interesting_components,
            simple_connections,
            non_simple_components,
            component_stats,
            statistics,
        ) = process_components(
            bipartite_graph,
            bicliques_result,
            dmr_metadata=dmr_metadata,
            gene_metadata=gene_metadata,
            gene_id_mapping=gene_id_mapping,
        )

        # Create summary statistics
        stats = {
            "total_components": len(interesting_components),
            "components_with_bicliques": len(
                [comp for comp in interesting_components if comp.get("bicliques")]
            ),
            "total_bicliques": len(bicliques_result["bicliques"]),
            "non_trivial_bicliques": sum(
                1
                for comp in interesting_components
                if comp.get("bicliques")
                for bic in comp["bicliques"]
            ),
        }

        # Add debug logging
        print(
            f"Original graph has {component_stats['components']['original']['connected']['interesting']} interesting components"
        )
        print(
            f"Biclique graph has {component_stats['components']['biclique']['connected']['interesting']} interesting components"
        )

        # Debug print the component_stats structure
        print("\nComponent Statistics received:")
        print(json.dumps(convert_dict_keys_to_str(component_stats), indent=2))

        # Calculate dominating set statistics first
        dmr_nodes = {
            n for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 0
        }
        dominating_set_stats = {
            "size": len(dominating_set),
            "percentage": len(dominating_set) / len(dmr_nodes) if dmr_nodes else 0,
            "genes_dominated": len(
                set().union(
                    *(set(bipartite_graph.neighbors(dmr)) for dmr in dominating_set)
                )
            ),
            # Use the count from component_stats instead of recalculating
            "components_with_ds": component_stats["components"]["original"]["connected"]["interesting"],
            # Use the interesting component count from stats
            "avg_size_per_component": (
                len(dominating_set) / component_stats["components"]["original"]["connected"]["interesting"]
                if component_stats["components"]["original"]["connected"]["interesting"] > 0
                else 0
            )
        }

        print(f"\nCalculated dominating set statistics:")
        print(json.dumps(dominating_set_stats, indent=2))

        # First get the biclique classifications
        biclique_type_counts = get_biclique_type_counts(bicliques_result["bicliques"])

        # Get component classifications
        components = list(nx.connected_components(bipartite_graph))
        component_classifications = {
            BicliqueSizeCategory.EMPTY: 0,
            BicliqueSizeCategory.SIMPLE: 0,
            BicliqueSizeCategory.INTERESTING: 0,
            BicliqueSizeCategory.COMPLEX: 0
        }

        for component in components:
            subgraph = bipartite_graph.subgraph(component)
            dmr_nodes = {
                n for n in component if bipartite_graph.nodes[n]["bipartite"] == 0
            }
            gene_nodes = {
                n for n in component if bipartite_graph.nodes[n]["bipartite"] == 1
            }

            # Get bicliques for this component
            component_bicliques = [
                (dmr_nodes_bic, gene_nodes_bic)
                for dmr_nodes_bic, gene_nodes_bic in bicliques_result["bicliques"]
                if (dmr_nodes_bic | gene_nodes_bic) & set(component)
            ]

            category = classify_component(dmr_nodes, gene_nodes, component_bicliques)
            component_classifications[category] += 1

        formatted_component_stats = {
            "components": component_stats[
                "components"
            ],  # Use the stats directly from process_components()
            "dominating_set": dominating_set_stats,
            "with_split_genes": sum(
                1 for comp in interesting_components if comp.get("split_genes")
            ),
            "total_split_genes": sum(
                len(comp.get("split_genes", [])) for comp in interesting_components
            ),
            "size_distribution": bicliques_result.get("size_distribution", {}),
        }

        print("\nFormatted component stats structure:")
        print(json.dumps(convert_dict_keys_to_str(formatted_component_stats), indent=2))

        # Calculate dominating set statistics
        dmr_nodes = {
            n for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 0
        }
        dominating_set_stats = {
            "size": len(dominating_set),
            "percentage": len(dominating_set) / len(dmr_nodes) if dmr_nodes else 0,
            "genes_dominated": len(
                set().union(
                    *(set(bipartite_graph.neighbors(dmr)) for dmr in dominating_set)
                )
            ),
            "components_with_ds": sum(
                1
                for comp in interesting_components
                if any(node in dominating_set for node in comp.get("component", []))
            ),
            "avg_size_per_component": len(dominating_set) / len(interesting_components)
            if interesting_components
            else 0,
        }

        # Create cached data with all information
        _cached_data = {
            "stats": stats,
            "interesting_components": interesting_components,
            "simple_connections": [],  # Initialize as empty list
            "coverage": bicliques_result.get("coverage", {}),
            "dmr_metadata": dmr_metadata,
            "gene_metadata": gene_metadata,
            "gene_id_mapping": gene_id_mapping,
            "node_positions": node_positions,
            "node_labels": node_labels,
            "bipartite_graph": bipartite_graph,
            "biclique_graph": biclique_graph,  # Add this line
            "component_stats": component_stats,  # Use the full component_stats
            "dominating_set": dominating_set_stats,
            "size_distribution": bicliques_result.get("size_distribution", {}),
            "node_participation": bicliques_result.get("node_participation", {}),
            "edge_coverage": bicliques_result.get("edge_coverage", {}),
        }

        return _cached_data
    except Exception as e:
        print(f"Error in process_data: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def extract_biclique_sets(bicliques_data) -> List[Tuple[Set[int], Set[int]]]:
    """Extract DMR and gene sets from processed biclique data."""
    result = []
    for biclique in bicliques_data:
        try:
            if isinstance(biclique, dict) and "details" in biclique:
                # Handle processed biclique format
                dmrs = {
                    int(d["id"].split("_")[1]) - 1
                    if isinstance(d["id"], str)
                    else d["id"]
                    for d in biclique["details"]["dmrs"]
                }
                genes = {g["name"] for g in biclique["details"]["genes"]}
                result.append((dmrs, genes))
            elif isinstance(biclique, tuple) and len(biclique) == 2:
                # Handle raw biclique format
                dmrs = {int(d) if isinstance(d, str) else d for d in biclique[0]}
                genes = {int(g) if isinstance(g, str) else g for g in biclique[1]}
                result.append((dmrs, genes))
            else:
                print(f"Warning: Unexpected biclique format: {type(biclique)}")
                continue

        except Exception as e:
            print(f"Error processing biclique: {str(e)}")
            continue

    print(f"Processed {len(result)} bicliques")
    if result:
        print("Sample biclique sizes:")
        for i, (dmrs, genes) in enumerate(result[:3]):
            print(f"Biclique {i}: {len(dmrs)} DMRs, {len(genes)} genes")

    return result
