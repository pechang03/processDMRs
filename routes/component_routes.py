from flask import render_template
from . import components_bp
from process_data import process_data
from utils.json_utils import convert_for_json
from visualization import create_biclique_visualization, create_node_biclique_map
from visualization.graph_layout import calculate_node_positions
from visualization.vis_components import create_component_visualization, create_component_details

@components_bp.route('/<int:component_id>')
def component_detail_route(component_id):
    """Handle component detail page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        results = convert_for_json(results)
        component = next(
            (c for c in results["interesting_components"] if c["id"] == component_id),
            None
        )

        if not component:
            return render_template("error.html", message=f"Component {component_id} not found")

        # Create visualization
        if "raw_bicliques" in component:
            node_biclique_map = create_node_biclique_map(component["raw_bicliques"])
            node_positions = calculate_node_positions(component["raw_bicliques"], node_biclique_map)
            
            component["visualization"] = create_component_visualization(
                component,
                node_positions,
                results["node_labels"],
                node_biclique_map,
                results.get("edge_classifications", {}),
                results.get("dmr_metadata", {}),
                results.get("gene_metadata", {})
            )

        # Create detailed component information
        component_details = create_component_details(
            component,
            results.get("dmr_metadata", {}),
            results.get("gene_metadata", {})
        )

        return render_template(
            "components.html",
            component=component,
            details=component_details,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            component_type="biconnected"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))

@components_bp.route('/graph')
def graph_components_route():
    """Handle graph components overview page."""
    results = process_data()
    overall_data = results.get("overall", {})
    component_stats = convert_for_json(overall_data.get("stats", {}).get("components", {}))
    return render_template("components/graph_components.html", statistics={"components": component_stats})
