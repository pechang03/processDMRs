# File: statistics_route.PythonFinalizationError
# # Description: This file defines the routes to be used by the statistics app.

from flask import render_template
import json
from process_data import process_data
from visualization import (
    create_biclique_visualization,
    create_node_biclique_map,
    calculate_node_positions,
)


def component_detail_route(component_id):
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        bipartite_graph = results.get("bipartite_graph")
        if not bipartite_graph:
            return render_template(
                "error.html", message="Bipartite graph not found in results"
            )

        # Find the requested component
        component = None
        if "interesting_components" in results:
            for comp in results["interesting_components"]:
                if comp["id"] == component_id:
                    # Only create visualization if not already present
                    if "plotly_graph" not in comp:
                        try:
                            component_viz = create_biclique_visualization(
                                comp["raw_bicliques"],
                                results["node_labels"],
                                results["node_positions"],
                                create_node_biclique_map(comp["raw_bicliques"]),
                                original_graph=bipartite_graph,
                                dmr_metadata=results["dmr_metadata"],
                                gene_metadata=results["gene_metadata"],
                                gene_id_mapping=results["gene_id_mapping"],
                            )
                            comp["plotly_graph"] = json.loads(component_viz)
                        except Exception as e:
                            print(f"Error creating visualization: {str(e)}")

                    component = comp
                    break

        if component is None:
            return render_template(
                "error.html", message=f"Component {component_id} not found"
            )

        # Create visualization only for the requested component
        try:
            # Create node_biclique_map for this specific component
            node_biclique_map = create_node_biclique_map(component["raw_bicliques"])

            # Calculate positions for this component
            node_positions = calculate_node_positions(
                component["raw_bicliques"], node_biclique_map
            )

            component_viz = create_biclique_visualization(
                component["raw_bicliques"],
                results["node_labels"],
                node_positions,  # Use component-specific positions
                node_biclique_map,  # Use component-specific mapping
                original_graph=bipartite_graph,  # Add this line
                dmr_metadata=results["dmr_metadata"],
                gene_metadata=results["gene_metadata"],
                gene_id_mapping=results["gene_id_mapping"],
            )
            component["plotly_graph"] = json.loads(component_viz)
        except Exception as e:
            print(f"Error creating visualization: {str(e)}")
            import traceback

            traceback.print_exc()

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))
