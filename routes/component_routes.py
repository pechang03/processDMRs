from flask import render_template
from . import components_bp
from process_data import process_data
from utils.json_utils import convert_for_json
from visualization import create_biclique_visualization, create_node_biclique_map
from visualization.graph_layout import calculate_node_positions
from visualization.vis_components import create_component_visualization, create_component_details
from visualization.triconnected_visualization import TriconnectedVisualization
from visualization.graph_layout_original import OriginalGraphLayout
from visualization.graph_layout_biclique import CircularBicliqueLayout

@components_bp.route('/<int:component_id>')
@components_bp.route('/<int:component_id>/<type>')
def component_detail_route(component_id, type="biclique"):
    """Handle component detail page with optional type."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        results = convert_for_json(results)

        # Find the component in any timepoint's data
        component = None
        timepoint_data = None

        for timepoint, data in results.items():
            if not isinstance(data, dict) or "error" in data:
                continue

            if type == "triconnected":
                # Look for triconnected components in this timepoint
                components = (data.get("stats", {})
                            .get("components", {})
                            .get("original", {})
                            .get("triconnected", {})
                            .get("components", []))
                
                component = next((c for c in components if c.get("id") == component_id), None)
                if component:
                    timepoint_data = data
                    break
            else:  # Biclique component
                # Check interesting components
                components = data.get("interesting_components", [])
                component = next((c for c in components if c.get("id") == component_id), None)
                if component:
                    timepoint_data = data
                    break

        if not component or not timepoint_data:
            return render_template("error.html", 
                                message=f"Component {component_id} not found in any timepoint")

        # Determine layout based on type
        layout = "spring" if type == "triconnected" else "circular"

        # Create visualization
        if type == "triconnected":
            # Create triconnected visualization using spring layout
            visualizer = TriconnectedVisualization()
            layout = OriginalGraphLayout()

            # Get subgraph for this component
            subgraph = timepoint_data["bipartite_graph"].subgraph(component["component"])

            # Calculate positions using spring layout
            node_positions = layout.calculate_positions(
                subgraph,
                node_info=None,
                layout_type="spring",
            )

            # Create visualization
            component["visualization"] = visualizer.create_visualization(
                subgraph,
                timepoint_data["node_labels"],
                node_positions,
                timepoint_data.get("dmr_metadata", {}),
                timepoint_data.get("edge_classifications", {}),
            )

        else:  # Biclique component
            if "raw_bicliques" in component:
                # Create node biclique map
                node_biclique_map = create_node_biclique_map(component["raw_bicliques"])

                # Use circular layout for bicliques
                layout = CircularBicliqueLayout()

                # Get subgraph for this component
                all_nodes = set()
                for dmrs, genes in component["raw_bicliques"]:
                    all_nodes.update(dmrs)
                    all_nodes.update(genes)
                subgraph = timepoint_data["bipartite_graph"].subgraph(all_nodes)

                # Calculate positions
                node_positions = layout.calculate_positions(
                    subgraph,
                    node_info=None,
                )

                # Create visualization
                component["visualization"] = create_biclique_visualization(
                    component["raw_bicliques"],
                    timepoint_data["node_labels"],
                    node_positions,
                    node_biclique_map,
                    timepoint_data.get("edge_classifications", {}),
                    timepoint_data["bipartite_graph"],
                    subgraph,
                    dmr_metadata=timepoint_data.get("dmr_metadata", {}),
                    gene_metadata=timepoint_data.get("gene_metadata", {}),
                )

        return render_template(
            "components.html",
            component=component,
            component_type=type,
            layout=layout,
            dmr_metadata=timepoint_data.get("dmr_metadata", {}),
            gene_metadata=timepoint_data.get("gene_metadata", {}),
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))

@components_bp.route('/graph')
def graph_components_route():
    """Handle graph components overview page."""
    results = process_data()
    
    # Initialize empty component stats structure
    default_component_stats = {
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
    }

    # Aggregate component stats from all timepoints
    aggregated_stats = default_component_stats.copy()
    for timepoint, data in results.items():
        if isinstance(data, dict) and "error" not in data:
            timepoint_stats = data.get("stats", {}).get("components", {})
            for graph_type in ["original", "biclique"]:
                for comp_type in ["connected", "biconnected", "triconnected"]:
                    for metric in ["total", "single_node", "small", "interesting"]:
                        aggregated_stats[graph_type][comp_type][metric] += (
                            timepoint_stats.get(graph_type, {})
                            .get(comp_type, {})
                            .get(metric, 0)
                        )

    return render_template(
        "components/graph_components.html", 
        statistics={"components": convert_for_json(aggregated_stats)}
    )
