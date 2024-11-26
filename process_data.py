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
from rb_domination import (
    greedy_rb_domination,
    calculate_dominating_sets,
    print_domination_statistics,
    copy_dominating_set,
)

app = Flask(__name__)

from data_loader import (
    DSS1_FILE,
    DSS_PAIRWISE_FILE,
    BIPARTITE_GRAPH_TEMPLATE,
    BIPARTITE_GRAPH_OVERALL,
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


def process_data(timepoint=None):
    """Process the DMR data and return results"""
    global _cached_data
    
    try:
        print("Starting data processing...")
        
        # Get file paths from Flask config
        dss1_file = current_app.config["DSS1_FILE"]
        pairwise_file = current_app.config["DSS_PAIRWISE_FILE"]
        
        # Initialize storage for multiple graphs
        graphs = {}
        timepoint_results = {}

        # Process overall DSS1 data first
        print("\nProcessing DSS1 overall data...")
        # First get available sheets
        available_sheets = get_excel_sheets(dss1_file)
        if not available_sheets:
            raise ValueError(f"No sheets found in {dss1_file}")
            
        # Try to find the right sheet
        sheet_name = None
        for sheet in available_sheets:
            if sheet.lower() == "dss1" or "overall" in sheet.lower():
                sheet_name = sheet
                break
        
        if not sheet_name:
            sheet_name = available_sheets[0]  # Use first sheet as fallback
            print(f"Warning: No DSS1 sheet found, using first available sheet: {sheet_name}")
            
        df_overall = read_excel_file(dss1_file, sheet_name=sheet_name)
        df_overall["Processed_Enhancer_Info"] = df_overall[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

        # Create gene mapping from overall data
        all_genes = set()
        gene_names = df_overall["Gene_Symbol_Nearby"].dropna().str.strip().str.lower()
        all_genes.update(gene_names)
        for genes in df_overall["Processed_Enhancer_Info"]:
            if genes:
                all_genes.update(g.strip().lower() for g in genes)

        # Create consistent gene ID mapping to use across all graphs
        max_dmr = df_overall["DMR_No."].max()
        gene_id_mapping = {
            gene: idx + max_dmr + 1 for idx, gene in enumerate(sorted(all_genes))
        }

        # Create overall graph
        overall_graph = create_bipartite_graph(df_overall, gene_id_mapping)
        graphs["overall"] = overall_graph

        # Create gene ID mapping
        all_genes = set()
        # First pass: Collect and normalize all gene names
        all_genes = set()

        # Use the overall dataframe for processing
        df = df_overall

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
        if timepoint:
            bicliques_file = BIPARTITE_GRAPH_TEMPLATE.format(timepoint)
        else:
            bicliques_file = BIPARTITE_GRAPH_OVERALL
        bicliques_result = process_bicliques(
            bipartite_graph,
            bicliques_file,  # Use template here
            max(df["DMR_No."]),
            timepoint if timepoint else "total",  # Pass timepoint info
            gene_id_mapping=gene_id_mapping,
            file_format=app.config.get("BICLIQUE_FORMAT", "gene-name"),
        )

        # Debug print for bicliques result
        print("\nBicliques result contents:")
        print("Number of bicliques:", len(bicliques_result.get("bicliques", [])))
        print("Keys in bicliques_result:", list(bicliques_result.keys()))

        # Detailed biclique logging (commented out)
        """
        print("\nDetailed biclique contents:")
        for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques_result.get("bicliques", [])):
            print(f"\nBiclique {idx + 1}:")
            print("DMR nodes:", sorted(list(dmr_nodes)))
            print("Gene nodes:", sorted(list(gene_nodes)))
        """

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
                        complex_components.append(
                            {
                                "component": component,
                                "bicliques": component_bicliques,
                                "split_genes": split_genes,
                            }
                        )

            print(
                f"\nFound {len(complex_components)} complex components with split genes"
            )
            print(
                f"Total split genes across components: {sum(len(c['split_genes']) for c in complex_components)}"
            )

            # Update biclique type statistics to include complex components
            total_components = len(bicliques_result["bicliques"])
            complex_count = len(
                [c for c in complex_components if len(c["bicliques"]) > 2]
            )
            interesting_count = len(
                [c for c in complex_components if len(c["bicliques"]) == 2]
            )
            simple_count = total_components - (complex_count + interesting_count)

            biclique_stats["biclique_types"] = {
                "empty": 0,
                "simple": simple_count,
                "interesting": interesting_count,
                "complex": complex_count,
            }

            # Add more detailed component statistics
            biclique_stats["component_details"] = {
                "total_components": total_components,
                "split_genes": {
                    "total": sum(len(c["split_genes"]) for c in complex_components),
                    "per_component": {
                        f"component_{i}": len(c["split_genes"])
                        for i, c in enumerate(complex_components)
                    },
                },
                "bicliques_per_component": {
                    f"component_{i}": len(c["bicliques"])
                    for i, c in enumerate(complex_components)
                },
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
        timepoint_results = {}
        if not timepoint:
            # Process each timepoint when doing total analysis
            xl = pd.ExcelFile(DSS_PAIRWISE_FILE)
            for sheet in xl.sheet_names:
                print(f"\nProcessing timepoint: {sheet}")
                try:
                    timepoint_data = process_data(sheet)
                    if "error" not in timepoint_data:
                        timepoint_results[sheet] = timepoint_data
                    else:
                        print(
                            f"Skipping timepoint {sheet} due to error: {timepoint_data['error']}"
                        )
                except Exception as e:
                    print(f"Error processing timepoint {sheet}: {e}")
                    continue  # Skip failed timepoints instead of failing completely

        # Initialize these variables with default values
        edge_coverage = {}
        biclique_stats = {
            "biclique_types": {},
            "coverage": {},
            "node_participation": {},
            "edge_coverage": {},
            "components": {},
        }

        # Calculate biclique statistics if we have bicliques
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

        # Now create _cached_data with the guaranteed-defined variables
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
            "edge_coverage": edge_coverage,  # Now guaranteed to be defined
            "biclique_stats": biclique_stats,  # Now guaranteed to be defined
            "biclique_types": biclique_stats.get("biclique_types", {}),
            "timepoint_stats": timepoint_results if not timepoint else None,
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


def process_single_timepoint(graph, df, gene_id_mapping, timepoint_name):
    """Process a single timepoint's graph and return its results"""
    try:
        # Validate graph
        print(f"\nValidating graph for timepoint {timepoint_name}")
        from data_loader import validate_bipartite_graph

        graph_valid = validate_bipartite_graph(graph)

        # Process bicliques for this timepoint
        bicliques_result = process_bicliques(
            graph,
            f"bipartite_graph_output_{timepoint_name}.txt",
            max(df["DMR_No."]),
            timepoint_name,
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
        }
    except Exception as e:
        return {"error": str(e)}
