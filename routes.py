from flask import render_template, request
import json
from process_data import process_data
from visualization import (
    create_biclique_visualization,
    create_node_biclique_map,
    calculate_node_positions,
)
from biclique_analysis.statistics import calculate_biclique_statistics

def index_route():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Limit to first two components
        if "interesting_components" in results:
            results["interesting_components"] = results["interesting_components"][:2]

        detailed_stats = calculate_biclique_statistics(
            results.get("bicliques", []), 
            results.get("bipartite_graph")
        )

        return render_template(
            "index.html",
            results=results,
            statistics=detailed_stats,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            bicliques_result=results,
            coverage=results.get("coverage", {}),
            node_labels=results.get("node_labels", {})
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))

def statistics_route():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        selected_component_id = request.args.get("component_id", type=int)
        detailed_stats = calculate_biclique_statistics(
            results.get("bicliques", []), 
            results.get("bipartite_graph")
        )

        return render_template(
            "statistics.html",
            statistics=detailed_stats,
            bicliques_result=results,
            selected_component_id=selected_component_id,
            total_bicliques=len(results.get("bicliques", []))
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))

def component_detail_route(component_id):
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        bipartite_graph = results.get("bipartite_graph")
        if not bipartite_graph:
            return render_template("error.html", message="Bipartite graph not found in results")

        # Find the requested component
        component = None
        if "interesting_components" in results:
            for comp in results["interesting_components"]:
                if comp["id"] == component_id:
                    component = comp
                    # Create visualization if not already present
                    if "plotly_graph" not in comp:
                        try:
                            node_biclique_map = create_node_biclique_map(comp["raw_bicliques"])
                            node_positions = calculate_node_positions(
                                comp["raw_bicliques"], 
                                node_biclique_map
                            )
                            component_viz = create_biclique_visualization(
                                comp["raw_bicliques"],
                                results["node_labels"],
                                node_positions,
                                node_biclique_map,
                                original_graph=bipartite_graph,
                                dmr_metadata=results["dmr_metadata"],
                                gene_metadata=results["gene_metadata"],
                                gene_id_mapping=results["gene_id_mapping"],
                            )
                            comp["plotly_graph"] = json.loads(component_viz)
                        except Exception as e:
                            print(f"Error creating visualization: {str(e)}")
                    break

        if component is None:
            return render_template("error.html", message=f"Component {component_id} not found")

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {})
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))
