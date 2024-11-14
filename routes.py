from flask import render_template
from process_data import process_data
from biclique_analysis.statistics import calculate_biclique_statistics


def index():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Print results for debugging
        print("Results structure:", results.keys())
        print(
            "Number of interesting components:",
            len(results.get("interesting_components", [])),
        )
        print(
            "Number of simple connections:", len(results.get("simple_connections", []))
        )

        # Ensure we have all required data
        for component in results.get("interesting_components", []):
            if "plotly_graph" not in component:
                print(f"Warning: Component {component.get('id')} missing plotly_graph")

        return render_template(
            "index.html",
            results=results,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            statistics=results.get("stats", {}),
            coverage=results.get("coverage", {}),
            node_labels=results.get(
                "node_labels", {}
            ),  # Pass node_labels to the template
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))

def statistics():
    """Handle the statistics route"""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Calculate statistics using the bicliques result
        bipartite_graph = results.get("bipartite_graph")
        bicliques = results.get("bicliques", [])
        
        if bipartite_graph and bicliques:
            detailed_stats = calculate_biclique_statistics(bicliques, bipartite_graph)
        else:
            detailed_stats = {
                "size_distribution": {},
                "coverage": results.get("coverage", {}),
                "node_participation": {"dmrs": {}, "genes": {}},
                "edge_coverage": {"single": 0, "multiple": 0, "uncovered": 0, "total": 0,
                                "single_percentage": 0, "multiple_percentage": 0, "uncovered_percentage": 0}
            }

        return render_template(
            "statistics.html", 
            statistics=detailed_stats,
            bicliques_result=results
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))
