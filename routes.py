from flask import render_template, request
import json
from process_data import process_data
from visualization import (
    create_biclique_visualization,
    create_node_biclique_map,
    calculate_node_positions,
)


def index_route():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Limit to first two components
        if "interesting_components" in results:
            results["interesting_components"] = results["interesting_components"][:2]

        return render_template(
            "index.html",
            results=results,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            bicliques_result=results,
            coverage=results.get("coverage", {}),
            node_labels=results.get("node_labels", {}),
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

        detailed_stats = {
            "size_distribution": {},
            "coverage": results.get(
                "coverage",
                {
                    "dmrs": {"covered": 0, "total": 0, "percentage": 0},
                    "genes": {"covered": 0, "total": 0, "percentage": 0},
                },
            ),
            "node_participation": {"dmrs": {}, "genes": {}},
            "edge_coverage": {
                "single": 0,
                "multiple": 0,
                "uncovered": 0,
                "total": 0,
                "single_percentage": 0,
                "multiple_percentage": 0,
                "uncovered_percentage": 0,
            },
        }

        # Filter components based on selection
        components_to_process = []
        if selected_component_id and "interesting_components" in results:
            components_to_process = [
                comp
                for comp in results["interesting_components"]
                if comp["id"] == selected_component_id
            ]
        elif "interesting_components" in results:
            components_to_process = results["interesting_components"]

        # Calculate statistics for selected component(s)
        size_dist = {}
        dmr_participation = {}
        gene_participation = {}

        for component in components_to_process:
            for biclique in component.get("raw_bicliques", []):
                dmr_nodes, gene_nodes = biclique
                size_key = (len(dmr_nodes), len(gene_nodes))
                size_dist[size_key] = size_dist.get(size_key, 0) + 1

                for dmr in dmr_nodes:
                    dmr_participation[dmr] = dmr_participation.get(dmr, 0) + 1
                for gene in gene_nodes:
                    gene_participation[gene] = gene_participation.get(gene, 0) + 1

        detailed_stats["size_distribution"] = size_dist

        # Calculate participation distributions
        for count in set(dmr_participation.values()):
            detailed_stats["node_participation"]["dmrs"][count] = len(
                [n for n, c in dmr_participation.items() if c == count]
            )
        for count in set(gene_participation.values()):
            detailed_stats["node_participation"]["genes"][count] = len(
                [n for n, c in gene_participation.items() if c == count]
            )

        return render_template(
            "statistics.html",
            statistics=detailed_stats,
            bicliques_result=results,
            selected_component_id=selected_component_id,
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
