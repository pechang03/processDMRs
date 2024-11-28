# File : main_routes.py
# Author : Peter Shaw
# Created on : 27 Nov 2024

from flask import render_template
from . import main_bp
from process_data import process_data
from utils.json_utils import convert_for_json, convert_dict_keys_to_str
from visualization.triconnected_visualization import TriconnectedVisualization
from visualization.graph_layout_original import OriginalGraphLayout
from visualization.core import create_biclique_visualization
from visualization.graph_layout_biclique import CircularBicliqueLayout
from visualization import create_node_biclique_map


@main_bp.route("/")
def index_route():
    """Handle main index page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Get overall data
        DSStimeseries_data = results.get("DSStimeseries", {})

        # Ensure complete statistics structure with defaults
        default_stats = {
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
        }

        # Process timepoint data including overall
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict):
                # Get existing stats
                stats = data.get("stats", {})

                # Ensure triconnected data exists in components
                if "components" in stats:
                    for graph_type in ["original", "biclique"]:
                        if graph_type in stats["components"]:
                            if "triconnected" not in stats["components"][graph_type]:
                                stats["components"][graph_type]["triconnected"] = {
                                    "total": 0,
                                    "single_node": 0,
                                    "small": 0,
                                    "interesting": 0,
                                }

                # Merge with default structure
                merged_stats = default_stats.copy()
                if stats:
                    merged_stats["components"].update(stats.get("components", {}))
                    merged_stats["coverage"].update(stats.get("coverage", {}))

                timepoint_info[timepoint] = {
                    "status": "success" if "error" not in data else "error",
                    "message": data.get("error", ""),
                    "stats": merged_stats,
                    "coverage": data.get("coverage", {}),
                    "components": data.get("components", {}),
                }

        # Convert all data structures using JSON utils
        statistics = convert_for_json(DSStimeseries_data.get("stats", default_stats))
        timepoint_info = convert_for_json(timepoint_info)
        DSStimeseries_data = convert_for_json(DSStimeseries_data)

        return render_template(
            "index.html",
            results=DSStimeseries_data,
            statistics=statistics,
            timepoint_info=timepoint_info,
            dmr_metadata=DSStimeseries_data.get("dmr_metadata", {}),
            gene_metadata=DSStimeseries_data.get("gene_metadata", {}),
            bicliques_result=DSStimeseries_data,
            coverage=DSStimeseries_data.get("coverage", {}),
            node_labels=DSStimeseries_data.get("node_labels", {}),
            dominating_set=DSStimeseries_data.get("dominating_set", {}),
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))


@main_bp.route("/statistics/")
@main_bp.route("/statistics")
def statistics_route():
    """Handle statistics page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Calculate overall statistics
        total_dmrs = 0
        total_genes = 0
        total_edges = 0
        timepoint_info = {}

        # Process each timepoint's data
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                # Get graph info for totals
                if "bipartite_graph" in data:
                    graph = data["bipartite_graph"]
                    dmr_nodes = {
                        n for n, d in graph.nodes(data=True) if d["bipartite"] == 0
                    }
                    gene_nodes = {
                        n for n, d in graph.nodes(data=True) if d["bipartite"] == 1
                    }
                    total_dmrs += len(dmr_nodes)
                    total_genes += len(gene_nodes)
                    total_edges += graph.number_of_edges()

                # Ensure proper data structure for timepoint
                timepoint_info[timepoint] = {
                    "status": "success",
                    "stats": data.get("stats", {}),
                    "complex_components": data.get("complex_components", []),
                    "interesting_components": data.get("interesting_components", []),
                    "non_simple_components": data.get("non_simple_components", []),
                    "components": data.get("stats", {}).get("components", {}),
                }

        # Get overall data
        DSStimeseries_data = results.get("DSStimeseries", {})

        # Structure the template data
        statistics = {
            "total_dmrs": total_dmrs,
            "total_genes": total_genes,
            "total_edges": total_edges,
            "timepoint_count": len([k for k in results.keys() if k != "DSStimeseries"]),
            "components": DSStimeseries_data.get("stats", {}).get("components", {}),
            "interesting_components": DSStimeseries_data.get(
                "interesting_components", []
            ),  # Make sure this is included
            "complex_components": DSStimeseries_data.get("complex_components", []),
            "stats": DSStimeseries_data.get("stats", {}),
            "edge_coverage": DSStimeseries_data.get("stats", {}).get("edge_coverage", {}),
            "coverage": DSStimeseries_data.get("stats", {}).get("coverage", {}),
            # Add these additional fields that might be needed by the template
            "edge_classifications": DSStimeseries_data.get("edge_classifications", {}),
            "node_labels": DSStimeseries_data.get("node_labels", {}),
            "dmr_metadata": DSStimeseries_data.get("dmr_metadata", {}),
            "gene_metadata": DSStimeseries_data.get("gene_metadata", {}),
        }

        # Debug print to check the data
        print("Interesting components:", len(statistics["interesting_components"]))

        return render_template(
            "statistics.html",
            statistics=statistics,
            timepoint_info=timepoint_info,
            DSStimeseries_data=DSStimeseries_data,
            edge_classifications=statistics[
                "edge_classifications"
            ],  # Make sure this is passed
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))


@main_bp.route("/component/<int:component_id>")
@main_bp.route("/component/<int:component_id>/<type>")
def component_detail_route(component_id, type="biclique"):
    """Handle component detail page with optional type."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Determine which components to search based on type
        if type == "triconnected":
            # Use triconnected components from original graph
            components = (
                results.get("DSStimeseries", {})
                .get("stats", {})
                .get("components", {})
                .get("original", {})
                .get("triconnected", {})
                .get("components", [])
            )

            # Find the requested component
            component = next((c for c in components if c["id"] == component_id), None)

            if component:
                # Create triconnected visualization using spring layout
                # Create visualizer with spring layout
                visualizer = TriconnectedVisualization()
                layout = OriginalGraphLayout()

                # Get subgraph for this component
                subgraph = results["bipartite_graph"].subgraph(component["component"])

                # Calculate positions using spring layout
                node_positions = layout.calculate_positions(
                    subgraph,
                    node_info=None,  # Will be created inside visualizer
                    layout_type="spring",
                )

                # Create visualization
                component["visualization"] = visualizer.create_visualization(
                    subgraph,
                    results["node_labels"],
                    node_positions,
                    results.get("dmr_metadata", {}),
                    results.get("edge_classifications", {}),
                )

        else:  # Biclique component
            # Use interesting components from biclique analysis
            components = results.get("interesting_components", [])
            component = next((c for c in components if c["id"] == component_id), None)

            if component and "raw_bicliques" in component:
                # Create node biclique map
                node_biclique_map = create_node_biclique_map(component["raw_bicliques"])

                # Use circular layout for bicliques
                layout = CircularBicliqueLayout()

                # Get subgraph for this component
                all_nodes = set()
                for dmrs, genes in component["raw_bicliques"]:
                    all_nodes.update(dmrs)
                    all_nodes.update(genes)
                subgraph = results["bipartite_graph"].subgraph(all_nodes)

                # Calculate positions
                node_positions = layout.calculate_positions(
                    subgraph,
                    node_info=None,  # Will be created inside visualizer
                )

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
                )

        if not component:
            return render_template(
                "error.html", message=f"Component {component_id} not found"
            )

        return render_template(
            "components.html",
            component=component,
            component_type=type,
            layout=layout,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))
