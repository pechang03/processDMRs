from flask import render_template

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
