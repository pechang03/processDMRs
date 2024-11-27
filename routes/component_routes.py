from flask import render_template
from . import components_bp
from process_data import process_data
from utils.json_utils import convert_for_json
from visualization import create_biclique_visualization, create_node_biclique_map

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

        # Add visualization if needed
        if "raw_bicliques" in component:
            node_biclique_map = create_node_biclique_map(component["raw_bicliques"])
            component["visualization"] = create_biclique_visualization(
                component["raw_bicliques"],
                results["node_labels"],
                results.get("node_positions", {}),
                node_biclique_map,
                results.get("edge_classifications", {}),
                results["bipartite_graph"],
                results["bipartite_graph"].subgraph(component["component"]),
                dmr_metadata=results.get("dmr_metadata", {}),
                gene_metadata=results.get("gene_metadata", {}),
                gene_id_mapping=results.get("gene_id_mapping", {})
            )

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            gene_id_mapping=results.get("gene_id_mapping", {}),
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
