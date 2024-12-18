# File : index_route.py
# Description : This file is for the root route of the application

from flask import render_template
from process_data import process_data


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
