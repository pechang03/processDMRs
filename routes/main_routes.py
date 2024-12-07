# File : main_routes.py
# Author : Peter Shaw
# Created on : 27 Nov 2024

from flask import render_template, jsonify, request
import json
from . import main_bp
from process_data import process_data
from utils.json_utils import convert_for_json, convert_dict_keys_to_str
from visualization.triconnected_visualization import TriconnectedVisualization
from visualization.graph_layout_original import OriginalGraphLayout
from visualization.core import create_biclique_visualization
from visualization.graph_layout_biclique import CircularBicliqueLayout
from visualization import create_node_biclique_map
import networkx as nx


@main_bp.route("/")
def index_route():
    """Handle main index page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Process timepoint data
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                timepoint_info[timepoint] = {
                    "status": "success",
                    "stats": data.get("stats", {}),
                    "data": data  # Include full data
                }
            else:
                timepoint_info[timepoint] = {
                    "status": "error",
                    "message": str(data) if data else "Unknown error",
                    "stats": {},
                    "data": {}
                }

        # Convert to JSON-safe format
        template_data = convert_for_json({
            "statistics": results,
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


        data = results[timepoint]
        if isinstance(data, dict) and "error" not in data:
            # Create a copy and remove the full graph
            timepoint_data = data.copy()
            graph = timepoint_data.pop('bipartite_graph', None)

            # If there are specific components selected, process only those
            selected_components = request.args.get('components', '').split(',')
            if selected_components and selected_components[0]:
                # Extract only the requested component subgraphs
                component_graphs = {}
                for comp_id in selected_components:
                    # Find the component in interesting or complex components
                    comp = next((c for c in timepoint_data.get('interesting_components', []) + 
                                 timepoint_data.get('complex_components', []) 
                                 if c.get('id') == int(comp_id)), None)
                    
                    if comp and graph:
                        # Get nodes for this component
                        all_nodes = set()
                        for dmrs, genes in comp.get('raw_bicliques', []):
                            all_nodes.update(dmrs)
                            all_nodes.update(genes)
                        
                        # Create subgraph
                        subgraph = graph.subgraph(all_nodes)
                        
                        # Create visualization
                        component_graphs[comp_id] = create_biclique_visualization(
                            comp['raw_bicliques'],
                            timepoint_data.get('node_labels', {}),
                            None,  # Let visualization handle positions
                            None,  # Node biclique map
                            timepoint_data.get('edge_classifications', {}),
                            graph,
                            subgraph,
                            dmr_metadata=timepoint_data.get('dmr_metadata', {}),
                            gene_metadata=timepoint_data.get('gene_metadata', {})
                        )

                timepoint_data['component_graphs'] = component_graphs

            return jsonify({
                "status": "success",
                "data": convert_for_json(timepoint_data)
            })

        return jsonify({
            "status": "error",
            "message": data.get("message", "Unknown error")
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })


# Remove this entire method, as it's now handled by stats_routes
    """Handle statistics page."""
    print("DEBUG: Hit statistics route")  # Debug print
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Process timepoint data
        timepoint_info = {}
        
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                # Extract stats directly from the timepoint data
                timepoint_info[timepoint] = {
                    "status": "success",
                    "stats": {
                        "coverage": data.get("stats", {}).get("coverage", {}),
                        "edge_coverage": data.get("stats", {}).get("edge_coverage", {}),
                        "components": data.get("stats", {}).get("components", {}),
                        "bicliques_summary": data.get("stats", {}).get("bicliques_summary", {})
                    },
                    "message": ""
                }
                
                # Debug print for DSStimeseries
                if timepoint == "DSStimeseries":
                    print("\nDEBUG: DSStimeseries Stats:")
                    print(json.dumps(timepoint_info[timepoint]["stats"], indent=2))
            else:
                timepoint_info[timepoint] = {
                    "status": "error",
                    "message": data.get("message", "Unknown error"),
                    "stats": {}
                }

        # Convert to JSON-safe format before sending to template
        safe_timepoint_info = convert_for_json(timepoint_info)

        return render_template(
            "statistics.html",
            timepoint_info=safe_timepoint_info
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
