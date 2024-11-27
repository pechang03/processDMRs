from flask import render_template
from . import main_bp
from process_data import process_data
from utils.json_utils import convert_for_json

@main_bp.route('/')
def index_route():
    """Handle main index page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Get overall data
        overall_data = results.get("overall", {})
        statistics = convert_for_json(overall_data.get("stats", {}))
        
        return render_template(
            "index.html",
            results=overall_data,
            statistics=statistics,
            timepoint_info=results,
            dmr_metadata=overall_data.get("dmr_metadata", {}),
            gene_metadata=overall_data.get("gene_metadata", {}),
            bicliques_result=overall_data,
            coverage=overall_data.get("coverage", {}),
            node_labels=overall_data.get("node_labels", {}),
            dominating_set=overall_data.get("dominating_set", {})
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))
