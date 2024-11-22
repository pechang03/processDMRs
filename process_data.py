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
# import pandas as pd
# import numpy as np

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
    classify_biclique_types,
)
from visualization import create_node_biclique_map, CircularBicliqueLayout, NodeInfo
from utils.node_info import NodeInfo
from utils.json_utils import convert_dict_keys_to_str

from data_loader import read_excel_file, create_bipartite_graph
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


def process_data():
    """Process the DMR data and return results"""
    global _cached_data

    # Return cached data if available
    if _cached_data is not None:
        print("\nCached data keys:")
        print(list(_cached_data.keys()))
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
                "BICLIQUE_FORMAT", "gene-name"
            ),  # Get format from app config
        )

        # Debug print for bicliques result
        print("\nBicliques result contents:")
        print("Number of bicliques:", len(bicliques_result.get("bicliques", [])))
        print("Keys in bicliques_result:", list(bicliques_result.keys()))

        # Biclique type statistics
        biclique_type_stats = classify_biclique_types(
            bicliques_result.get("bicliques", [])
        )
        print("\nBiclique type statistics:")
        print(json.dumps(biclique_type_stats, indent=2))

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
            dominating_set=dominating_set,  # Add this parameter
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
            "components_with_ds": component_stats["components"]["original"][
                "connected"
            ]["interesting"],
            # Use the interesting component count from stats
            "avg_size_per_component": (
                len(dominating_set)
                / component_stats["components"]["original"]["connected"]["interesting"]
                if component_stats["components"]["original"]["connected"]["interesting"]
                > 0
                else 0
            ),
        }

        print(f"\nCalculated dominating set statistics:")
        print(json.dumps(dominating_set_stats, indent=2))

        # First get the biclique classifications
        biclique_type_counts = classify_biclique_types(bicliques_result["bicliques"])

        # Get component classifications
        components = list(nx.connected_components(bipartite_graph))
        component_classifications = {
            cat.name.lower(): 0 for cat in BicliqueSizeCategory
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
            component_classifications[category.name.lower()] += 1

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
        genes_dominated = set().union(
            *(set(bipartite_graph.neighbors(dmr)) for dmr in dominating_set)
        )
        num_genes_dominated = len(genes_dominated)
        dominating_set_stats = {
            "size": len(dominating_set),
            # "percentage": len(dominating_set) / len(dmr_nodes) if dmr_nodes else 0,
            "percentage": num_genes_dominated / len(gene_nodes) if dmr_nodes else 0,
            "genes_dominated": num_genes_dominated,
            "components_with_ds": sum(
                1
                for comp in interesting_components
                if any(node in dominating_set for node in comp.get("component", []))
            ),
            "avg_size_per_component": len(dominating_set) / len(interesting_components)
            if interesting_components
            else 0,
        }

        # Calculate biclique statistics
        if bicliques_result and "bicliques" in bicliques_result:
            print("\nCalculating biclique statistics...")
            from biclique_analysis.statistics import (
                calculate_biclique_statistics,
                calculate_edge_coverage,
            )

            # Calculate edge coverage
            edge_coverage = calculate_edge_coverage(
                bicliques_result["bicliques"], bipartite_graph
            )
            print("Edge coverage calculated:", edge_coverage)

            # Calculate full biclique statistics
            biclique_stats = calculate_biclique_statistics(
                bicliques_result["bicliques"], bipartite_graph, dominating_set
            )
            print(
                "Biclique statistics calculated:",
                json.dumps(convert_dict_keys_to_str(biclique_stats), indent=2),
            )

            # Analyze connected components
            print("\nAnalyzing connected components...")
            connected_components = list(nx.connected_components(biclique_graph))
            print(f"Found {len(connected_components)} connected components")

            # Track complex components (those with multiple bicliques)
            complex_components = []
            for component in connected_components:
                # Get all bicliques that have nodes in this component
                component_bicliques = [
                    (dmr_nodes, gene_nodes) 
                    for dmr_nodes, gene_nodes in bicliques_result["bicliques"]
                    if not (dmr_nodes | gene_nodes).isdisjoint(component)
                ]
            
                if len(component_bicliques) > 1:
                    # This is a complex component with multiple bicliques
                    split_genes = {
                        gene 
                        for _, genes in component_bicliques 
                        for gene in genes
                        if sum(1 for _, g in component_bicliques if gene in g) > 1
                    }
                
                    if split_genes:  # Only count if there are actual split genes
                        complex_components.append({
                            "component": component,
                            "bicliques": component_bicliques,
                            "split_genes": split_genes
                        })

            print(f"\nFound {len(complex_components)} complex components with split genes")
            print(f"Total split genes across components: {sum(len(c['split_genes']) for c in complex_components)}")

            # Update biclique type statistics to include complex components
            total_components = len(bicliques_result["bicliques"])
            complex_count = len([c for c in complex_components if len(c["bicliques"]) > 2])
            interesting_count = len([c for c in complex_components if len(c["bicliques"]) == 2])
            simple_count = total_components - (complex_count + interesting_count)

            biclique_stats["biclique_types"] = {
                "empty": 0,
                "simple": simple_count,
                "interesting": interesting_count,
                "complex": complex_count
            }

            # Add more detailed component statistics
            biclique_stats["component_details"] = {
                "total_components": total_components,
                "split_genes": {
                    "total": sum(len(c["split_genes"]) for c in complex_components),
                    "per_component": {
                        f"component_{i}": len(c["split_genes"]) 
                        for i, c in enumerate(complex_components)
                    }
                },
                "bicliques_per_component": {
                    f"component_{i}": len(c["bicliques"]) 
                    for i, c in enumerate(complex_components)
                }
            }

            # Also add the header statistics from the biclique file
            if "statistics" in bicliques_result:
                biclique_stats["header_statistics"] = bicliques_result["statistics"]

            # Process components to identify interesting ones
            interesting_components = []
            for idx, (dmr_nodes, gene_nodes) in enumerate(
                bicliques_result["bicliques"]
            ):
                # Create subgraph for this component
                component_nodes = dmr_nodes | gene_nodes
                subgraph = bipartite_graph.subgraph(component_nodes)

                # Get bicliques for this component
                component_bicliques = [(dmr_nodes, gene_nodes)]

                # Classify the component
                category = classify_component(
                    dmr_nodes, gene_nodes, component_bicliques
                )

                if category in [
                    BicliqueSizeCategory.INTERESTING,
                    BicliqueSizeCategory.COMPLEX,
                ]:
                    # Find split genes (genes appearing in multiple bicliques)
                    split_genes = {
                        gene
                        for gene in gene_nodes
                        if len(
                            [b for b in bicliques_result["bicliques"] if gene in b[1]]
                        )
                        > 1
                    }

                    component_info = {
                        "id": idx + 1,
                        "dmrs": len(dmr_nodes),
                        "genes": len(gene_nodes - split_genes),
                        "total_genes": len(gene_nodes),
                        "split_genes": list(split_genes),
                        "raw_bicliques": component_bicliques,
                        "category": category.name.lower(),
                        "component": component_nodes,
                        "total_edges": len(list(subgraph.edges())),
                    }
                    interesting_components.append(component_info)

            print(f"\nFound {len(interesting_components)} interesting components")

        # Create cached data with all information
        _cached_data = {
            "stats": stats,
            "interesting_components": interesting_components,
            "simple_connections": [],
            "coverage": bicliques_result.get("coverage", {}),
            "dmr_metadata": dmr_metadata,
            "gene_metadata": gene_metadata,
            "gene_id_mapping": gene_id_mapping,
            "node_positions": node_positions,
            "node_labels": node_labels,
            "bipartite_graph": bipartite_graph,
            "biclique_graph": biclique_graph,
            "component_stats": component_stats,
            "dominating_set": dominating_set_stats,
            "size_distribution": bicliques_result.get("size_distribution", {}),
            "node_participation": bicliques_result.get("node_participation", {}),
            "edge_coverage": edge_coverage,
            "biclique_stats": biclique_stats,
            "biclique_types": biclique_stats.get("biclique_types", {}),
        }

        # Debug print for cached data
        print("\nCached data keys:")
        print(list(_cached_data.keys()))

        # Debug print for biclique types
        print("\nBiclique types from results:")
        print(json.dumps(_cached_data.get("biclique_types", {}), indent=2))

        return _cached_data
    except Exception as e:
        print(f"Error in process_data: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}
