from flask import render_template, request
import json
from extensions import app
from process_data import process_data, convert_dict_keys_to_str
from visualization.core import create_biclique_visualization  # Direct import
from visualization import (
    create_node_biclique_map,
    OriginalGraphLayout,
    CircularBicliqueLayout,
    SpringLogicalLayout,
)
from visualization.graph_layout import calculate_node_positions
from utils.node_info import NodeInfo
from visualization.base_layout import BaseLogicalLayout
from visualization.biconnected_visualization import BiconnectedVisualization
from visualization.triconnected_visualization import TriconnectedVisualization
from biclique_analysis.statistics import (
    calculate_biclique_statistics,
    analyze_components,
)
from biclique_analysis.triconnected import analyze_triconnected_components
from biclique_analysis.classifier import (
    BicliqueSizeCategory,
    classify_biclique,
    classify_component,
)

# Use functions from biclique_analysis
from biclique_analysis.statistics import (
    analyze_components,
    calculate_component_statistics,
    calculate_coverage_statistics,
    calculate_edge_coverage,
)
from biclique_analysis.triconnected import analyze_triconnected_components

from biclique_analysis.classifier import classify_biclique
from utils.json_utils import convert_dict_keys_to_str


@app.template_filter("get_biclique_classification")
def get_biclique_classification(dmr_nodes, gene_nodes):
    """Template filter to get biclique classification."""
    category = classify_biclique(set(dmr_nodes), set(gene_nodes))
    return category.name.lower()  # Return string name of enum


def index_route():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Process each timepoint's data
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict):
                if "error" in data:
                    timepoint_info[timepoint] = {
                        "status": "error",
                        "message": data["error"]
                    }
                else:
                    # Extract statistics and component info for this timepoint
                    timepoint_info[timepoint] = {
                        "status": "success",
                        "stats": data.get("stats", {}),
                        "coverage": data.get("stats", {}).get("coverage", {}),
                        "components": data.get("stats", {}).get("components", {}),
                        "interesting_components": data.get("interesting_components", []),
                        "complex_components": data.get("complex_components", []),
                        "biclique_types": data.get("stats", {}).get("biclique_types", {})
                    }

        # Get overall data if available
        overall_data = results.get("overall", {})
        
        return render_template(
            "index.html",
            results=overall_data,
            statistics=overall_data.get("stats", {}),
            timepoint_info=timepoint_info,
            dmr_metadata=overall_data.get("dmr_metadata", {}),
            gene_metadata=overall_data.get("gene_metadata", {}),
            bicliques_result=overall_data,
            coverage=overall_data.get("coverage", {}),
            node_labels=overall_data.get("node_labels", {}),
            dominating_set=overall_data.get("dominating_set", {})
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))


def statistics_route():
    """Handle statistics page requests with enhanced error handling and debugging."""
    import sys

    try:
        print("\n=== Starting Statistics Route ===", flush=True)
        results = process_data()

        print("\nResults from process_data():", flush=True)
        print(f"Type: {type(results)}", flush=True)
        print(
            f"Keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}",
            flush=True,
        )

        if "error" in results:
            print(f"Error found in results: {results['error']}", flush=True)
            return render_template("error.html", message=results["error"])

        # Get overall graph from results
        overall_data = results.get("overall", {})
        if "bipartite_graph" in overall_data:
            graph = overall_data["bipartite_graph"]

            # Calculate all statistics
            bicliques = overall_data.get("bicliques", [])

            # Calculate component statistics
            component_stats = calculate_component_statistics(bicliques, graph)

            # Calculate coverage statistics
            coverage_stats = calculate_coverage_statistics(bicliques, graph)

            # Calculate edge coverage
            edge_coverage = calculate_edge_coverage(bicliques, graph)

            # Create detailed statistics with proper structure
            detailed_stats = {
                "components": component_stats,
                "coverage": {
                    "dmrs": coverage_stats.get(
                        "dmrs", {"covered": 0, "total": 0, "percentage": 0}
                    ),
                    "genes": coverage_stats.get(
                        "genes", {"covered": 0, "total": 0, "percentage": 0}
                    ),
                    "edges": edge_coverage,
                },
                "edge_coverage": edge_coverage,
                "biclique_types": overall_data.get(
                    "biclique_types",
                    {"empty": 0, "simple": 0, "interesting": 0, "complex": 0},
                ),
                "size_distribution": overall_data.get("size_distribution", {}),
                "dominating_set": {
                    "size": 0,
                    "percentage": 0,
                    "genes_dominated": 0,
                    "components_with_ds": 0,
                    "avg_size_per_component": 0,
                },
            }
        else:
            # Provide default empty statistics structure if no graph
            detailed_stats = {
                "components": {
                    "original": {
                        "connected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                        "biconnected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                        "triconnected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                    },
                    "biclique": {
                        "connected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                        "biconnected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                        "triconnected": {
                            "total": 0,
                            "single_node": 0,
                            "small": 0,
                            "interesting": 0,
                        },
                    },
                },
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
                "edge_coverage": {},
                "biclique_types": {
                    "empty": 0,
                    "simple": 0,
                    "interesting": 0,
                    "complex": 0,
                },
                "size_distribution": {},
                "dominating_set": {
                    "size": 0,
                    "percentage": 0,
                    "genes_dominated": 0,
                    "components_with_ds": 0,
                    "avg_size_per_component": 0,
                },
            }

        # Process timepoint data
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict):
                if "error" in data:
                    timepoint_info[timepoint] = {
                        "status": "error",
                        "message": data["error"],
                    }
                else:
                    timepoint_info[timepoint] = {
                        "status": "success",
                        "stats": detailed_stats
                        if timepoint == "overall"
                        else data.get("stats", {}),
                    }

        print("\nRendering template with data:", flush=True)
        print(f"Number of timepoints: {len(timepoint_info)}", flush=True)
        print(f"Detailed stats keys: {list(detailed_stats.keys())}", flush=True)

        # Create template data with correct structure
        template_data = {
            "statistics": detailed_stats,
            "timepoint_info": timepoint_info,
            "data": {"stats": detailed_stats},
        }

        # Debug the structure
        print("\nTemplate data structure:")
        print("data.stats keys:", list(template_data["data"]["stats"].keys()))
        if "components" in template_data["data"]["stats"]:
            print(
                "data.stats.components keys:",
                list(template_data["data"]["stats"]["components"].keys()),
            )
            if "original" in template_data["data"]["stats"]["components"]:
                print(
                    "data.stats.components.original keys:",
                    list(
                        template_data["data"]["stats"]["components"]["original"].keys()
                    ),
                )

        return render_template("statistics.html", **template_data)

    except Exception as e:
        import traceback

        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        return render_template("error.html", message=str(e))


def component_detail_route(component_id, type="biconnected"):
    """Handle component detail page requests."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        results = convert_dict_keys_to_str(results)

        print(f"\nProcessing component {component_id} of type {type}")

        if type == "triconnected":
            # ... [triconnected handling stays the same] ...
            pass
        else:
            component = next(
                (
                    c
                    for c in results["interesting_components"]
                    if c["id"] == component_id
                ),
                None,
            )

            if component and "raw_bicliques" in component:
                print("\nComponent found:")
                print(f"Component ID: {component['id']}")
                print(f"Number of raw bicliques: {len(component['raw_bicliques'])}")

                # Create node biclique map first
                node_biclique_map = create_node_biclique_map(component["raw_bicliques"])
                print(f"Node-biclique map size: {len(node_biclique_map)}")

                # Calculate positions using graph_layout.py
                node_positions = calculate_node_positions(
                    component["raw_bicliques"], node_biclique_map
                )

                print("\nPosition calculation complete:")
                print(f"Number of positions: {len(node_positions)}")

                # Get subgraph for this component
                all_nodes = set()
                for dmrs, genes in component["raw_bicliques"]:
                    all_nodes.update(dmrs)
                    all_nodes.update(genes)
                subgraph = results["bipartite_graph"].subgraph(all_nodes)

                # Create visualization
                component["visualization"] = create_biclique_visualization(
                    component["raw_bicliques"],
                    results["node_labels"],
                    node_positions,
                    node_biclique_map,
                    results.get("edge_classifications", {}),
                    results["bipartite_graph"],
                    subgraph,
                    dmr_metadata=results.get("dmr_metadata", {}),
                    gene_metadata=results.get("gene_metadata", {}),
                    gene_id_mapping=results.get("gene_id_mapping", {}),
                )

        if not component:
            return render_template(
                "error.html", message=f"Component {component_id} not found"
            )

        print("\nFinal component data:")
        print(f"DMRs: {component.get('dmrs')}")
        print(f"Genes: {component.get('genes')}")
        print(f"Total edges: {component.get('total_edges')}")
        print(f"Has visualization: {'visualization' in component}")

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            gene_id_mapping=results.get("gene_id_mapping", {}),
            component_type=type,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))


@app.template_filter("get_biclique_classification")
def get_biclique_classification(dmr_nodes, gene_nodes):
    """Template filter to get biclique classification."""
    category = classify_biclique(set(dmr_nodes), set(gene_nodes))
    return category.name.lower()
