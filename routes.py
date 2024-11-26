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
    try:
        print("\n=== Starting Statistics Route ===", flush=True)
        results = process_data()

        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Get overall data from results
        overall_data = results.get("overall", {})
        
        # Structure the template data correctly
        template_data = {
            "data": {  # Add this wrapper level
                "stats": overall_data.get("stats", {}),
                "coverage": overall_data.get("stats", {}).get("coverage", {
                    "dmrs": {"covered": 0, "total": 0, "percentage": 0},
                    "genes": {"covered": 0, "total": 0, "percentage": 0},
                    "edges": {
                        "single_coverage": 0,
                        "multiple_coverage": 0,
                        "uncovered": 0,
                        "total": 0,
                        "single_percentage": 0,
                        "multiple_percentage": 0,
                        "uncovered_percentage": 0
                    }
                }),
                "components": overall_data.get("stats", {}).get("components", {
                    "original": {
                        "connected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0},
                        "biconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0},
                        "triconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0}
                    },
                    "biclique": {
                        "connected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0},
                        "biconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0},
                        "triconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0}
                    }
                })
            },
            "statistics": overall_data.get("stats", {}),
            "timepoint_info": {
                timepoint: {
                    "status": data.get("status", "error"),
                    "stats": data.get("stats", {})
                }
                for timepoint, data in results.items()
                if timepoint != "overall"
            }
        }

        return render_template("statistics.html", **template_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
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
