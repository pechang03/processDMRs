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

        # Aggregate statistics across all timepoints
        total_stats = {
            "total_dmrs": 0,
            "total_genes": 0,
            "total_edges": 0,
            "timepoint_count": len(results)
        }

        # Process each timepoint's data
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                # Get graph info for totals
                if "bipartite_graph" in data:
                    graph = data["bipartite_graph"]
                    total_stats["total_dmrs"] += sum(1 for n, d in graph.nodes(data=True) if d["bipartite"] == 0)
                    total_stats["total_genes"] += sum(1 for n, d in graph.nodes(data=True) if d["bipartite"] == 1)
                    total_stats["total_edges"] += graph.number_of_edges()

                # Structure timepoint data
                timepoint_info[timepoint] = {
                    "status": "success",
                    "stats": data.get("stats", {}),
                    "message": ""
                }
            else:
                timepoint_info[timepoint] = {
                    "status": "error",
                    "stats": {},
                    "message": str(data.get("message", "Unknown error"))
                }

        # Convert all data to JSON-safe format
        template_data = convert_for_json({
            "statistics": total_stats,
            "timepoint_info": timepoint_info
        })

        return render_template(
            "index.html",
            results=template_data,
            statistics=template_data["statistics"],
            timepoint_info=template_data["timepoint_info"],
            dmr_metadata=timepoint_info.get(next(iter(timepoint_info), {}), {}).get("dmr_metadata", {}),
            gene_metadata=timepoint_info.get(next(iter(timepoint_info), {}), {}).get("gene_metadata", {}),
            bicliques_result=timepoint_info.get(next(iter(timepoint_info), {}), {}),
            coverage=template_data["statistics"].get("coverage", {}),
            node_labels=timepoint_info.get(next(iter(timepoint_info), {}), {}).get("node_labels", {}),
            dominating_set=timepoint_info.get(next(iter(timepoint_info), {}), {}).get("dominating_set", {})
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

        # Initialize aggregated statistics
        total_stats = {
            "total_dmrs": 0,
            "total_genes": 0,
            "total_edges": 0,
            "timepoint_count": len(results)
        }

        # Process each timepoint's data
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                # Update totals from graph info
                if "bipartite_graph" in data:
                    graph = data["bipartite_graph"]
                    total_stats["total_dmrs"] += sum(1 for n, d in graph.nodes(data=True) if d["bipartite"] == 0)
                    total_stats["total_genes"] += sum(1 for n, d in graph.nodes(data=True) if d["bipartite"] == 1)
                    total_stats["total_edges"] += graph.number_of_edges()

                # Store all timepoint data directly
                timepoint_info[timepoint] = data

            else:
                timepoint_info[timepoint] = {
                    "status": "error",
                    "message": data.get("message", "Unknown error")
                }

        # Convert data for template
        template_data = convert_for_json({
            "statistics": total_stats,  # Just the overall totals
            "timepoint_info": timepoint_info  # All timepoint data
        })

        return render_template(
            "statistics.html",
            statistics=template_data["statistics"],
            timepoint_info=template_data["timepoint_info"]
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
