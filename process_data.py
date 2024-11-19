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
from visualization import (
    create_node_biclique_map,
    calculate_node_positions,
)
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
            '_'.join(map(str, k)) if isinstance(k, tuple) else str(k): convert_dict_keys_to_str(v)
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
        node_positions = calculate_node_positions(
            bicliques_result["bicliques"], node_biclique_map
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
        # Copy dominating set to biclique graph
        biclique_dominating_set = copy_dominating_set(
            bipartite_graph, biclique_graph, dominating_set
        )

        # Process components first
        print("Processing components...")
        interesting_components, simple_connections, component_stats = (
            process_components(
                bipartite_graph,
                bicliques_result,
                dmr_metadata=dmr_metadata,
                gene_metadata=gene_metadata,
                gene_id_mapping=gene_id_mapping,
            )
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

        # Ensure proper structure for component stats
        def convert_dict_keys_to_str(d):
            if isinstance(d, dict):
                return {
                    str(k) if isinstance(k, tuple) else k: convert_dict_keys_to_str(v)
                    for k, v in d.items()
                }
            return d

        formatted_component_stats = {
            "components": {
                "original": {
                    "connected": {
                        "total": len(list(nx.connected_components(bipartite_graph))),
                        "single_node": sum(1 for comp in nx.connected_components(bipartite_graph) if len(comp) == 1),
                        "small": sum(1 for comp in nx.connected_components(bipartite_graph) 
                                   if 1 < len(comp) <= 3),  # Adjust small threshold as needed
                        "interesting": len([comp for comp in nx.connected_components(bipartite_graph) 
                                         if len(comp) > 3])  # Adjust interesting threshold as needed
                    },
                    "biconnected": {
                        "total": len(list(nx.biconnected_components(bipartite_graph))),
                        "single_node": 0,  # Biconnected components can't have single nodes
                        "small": sum(1 for comp in nx.biconnected_components(bipartite_graph) 
                                   if len(comp) <= 3),
                        "interesting": len([comp for comp in nx.biconnected_components(bipartite_graph) 
                                         if len(comp) > 3])
                    }
                },
                "biclique": {
                    "connected": {
                        "total": len(interesting_components),
                        "single_node": sum(1 for comp in interesting_components 
                                         if len(comp.get("dmr_nodes", [])) + len(comp.get("gene_nodes", [])) == 1),
                        "small": sum(1 for comp in interesting_components 
                                   if 1 < len(comp.get("dmr_nodes", [])) + len(comp.get("gene_nodes", [])) <= 3),
                        "interesting": sum(1 for comp in interesting_components 
                                        if len(comp.get("dmr_nodes", [])) + len(comp.get("gene_nodes", [])) > 3)
                    },
                    "biconnected": {
                        "total": len(list(nx.biconnected_components(bipartite_graph))),
                        "single_node": 0,
                        "small": sum(1 for comp in nx.biconnected_components(bipartite_graph) 
                                   if len(comp) <= 3),
                        "interesting": len([comp for comp in nx.biconnected_components(bipartite_graph) 
                                         if len(comp) > 3])
                    }
                }
            },
            "with_split_genes": sum(1 for comp in interesting_components if comp.get("split_genes")),
            "total_split_genes": sum(len(comp.get("split_genes", [])) for comp in interesting_components),
            "total_bicliques": sum(len(comp.get("raw_bicliques", [])) for comp in interesting_components)
        }
        formatted_component_stats = convert_dict_keys_to_str(formatted_component_stats)

        # Create cached data with all information
        _cached_data = {
            "stats": stats,
            "interesting_components": interesting_components,
            "simple_connections": simple_connections, 
            "coverage": bicliques_result.get("coverage", {}),
            "dmr_metadata": dmr_metadata,
            "gene_metadata": gene_metadata,
            "gene_id_mapping": gene_id_mapping,
            "node_positions": node_positions,
            "node_labels": node_labels,
            "bipartite_graph": bipartite_graph,
            "component_stats": {
                "components": formatted_component_stats["components"],
                "dominating_set": {
                    "size": len(dominating_set),
                    "percentage": len(dominating_set) / len(df) if len(df) > 0 else 0,
                    "genes_dominated": len(set().union(*[set(bipartite_graph.neighbors(dmr)) for dmr in dominating_set])),
                    "components_with_ds": len([c for c in interesting_components 
                                            if any(n in dominating_set for n in c.get("dmr_nodes", []))]),
                    "avg_size_per_component": len(dominating_set) / len(interesting_components) 
                                            if interesting_components else 0,
                    "genes_dominated_percentage": len(set().union(*[set(bipartite_graph.neighbors(dmr)) 
                                                for dmr in dominating_set])) / len(gene_id_mapping) * 100
                }
            },
            "dominating_set": dominating_set
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
