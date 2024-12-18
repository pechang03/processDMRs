from extensions import app
from flask import render_template, jsonify, current_app
import json
from . import stats_bp
from process_data import process_data
from utils.json_utils import convert_for_json


@stats_bp.route("/")
def statistics_index():
    """Handle statistics overview page."""
    try:
        # Get paths from app config
        gene_mapping_file = app.config.get(
            "GENE_MAPPING_FILE", "./data/master_gene_ids.csv"
        )
        dss1_path = app.config.get("DSS1_FILE", "./data/DSS1.xlsx")
        pairwise_path = app.config.get("DSS_PAIRWISE_FILE", "./data/DSS_PAIRWISE.xlsx")
        if gene_mapping_file is None:
            print("No gene mapping file found")
        if dss1_path is None:
            print("No DSS1 file found")
        if pairwise_path is None:
            print("No pairwise file found")

        # Call process_data with configuration
        results = process_data(
            gene_mapping_file=gene_mapping_file,
            dss1_path=dss1_path,
            pairwise_path=pairwise_path,
        )
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Calculate overall statistics by aggregating across all timepoints
        total_dmrs = 0
        total_genes = set()  # Use set to avoid counting duplicate genes
        total_edges = 0
        valid_timepoints = 0

        # Process timepoint data
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                valid_timepoints += 1

                # Get graph info
                graph = data.get("bipartite_graph")
                if graph and isinstance(graph, dict):
                    node_attrs = graph.get("node_attributes", {})
                    dmrs = len(
                        [n for n, d in node_attrs.items() if d.get("bipartite") == 0]
                    )
                    genes = [
                        n for n, d in node_attrs.items() if d.get("bipartite") == 1
                    ]
                    edges = len(graph.get("edges", []))

                    total_dmrs += dmrs
                    total_genes.update(genes)
                    total_edges += edges

                # Process timepoint data with complete stats
                timepoint_info[timepoint] = {
                    "status": "success",
                    "stats": convert_for_json(data.get("stats", {})),
                    "coverage": convert_for_json(data.get("coverage", {})),
                    "edge_coverage": convert_for_json(data.get("edge_coverage", {})),
                    "components": convert_for_json(
                        data.get("stats", {}).get("components", {})
                    ),
                    "dominating_set": convert_for_json(data.get("dominating_set", {})),
                    "bicliques_summary": convert_for_json(
                        data.get("bicliques_summary", {})
                    ),
                    "interesting_components": convert_for_json(
                        data.get("interesting_components", [])
                    ),
                    "complex_components": convert_for_json(
                        data.get("complex_components", [])
                    ),
                    "message": "",
                }
            else:
                timepoint_info[timepoint] = {
                    "status": "error",
                    "message": data.get("message", "Unknown error"),
                    "stats": {},
                }

        overall_stats = {
            "graph_info": {
                "total_dmrs": total_dmrs,
                "total_genes": len(total_genes),
                "total_edges": total_edges,
                "timepoints": valid_timepoints,
            }
        }

        # Convert everything to JSON-safe format
        safe_timepoint_info = convert_for_json(timepoint_info)
        safe_overall_stats = convert_for_json(overall_stats)

        # Get first timepoint's statistics for initial display
        first_timepoint = next(iter(safe_timepoint_info), "")
        initial_stats = safe_timepoint_info.get(first_timepoint, {})

        return render_template(
            "statistics.html",
            timepoint_info=safe_timepoint_info,
            overall_stats=safe_overall_stats,
            statistics=initial_stats,
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))


@stats_bp.route("/timepoint/<timepoint>")
def timepoint_stats(timepoint):
    """Get statistics for a specific timepoint."""
    try:
        results = process_data()

        # Special handling for DSStimeseries
        if timepoint == "DSStimeseries":
            # Ensure data is ready
            if not results or "DSStimeseries" not in results:
                return jsonify(
                    {
                        "status": "error",
                        "message": "Data still processing",
                        "retry": True,
                    }
                ), 404

        if "error" in results or timepoint not in results:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Timepoint {timepoint} not found",
                    "debug": {
                        "available_timepoints": list(results.keys()),
                        "error": results.get("error"),
                    },
                }
            ), 404

        data = results[timepoint]
        if isinstance(data, dict) and "error" not in data:
            return jsonify({"status": "success", "data": convert_for_json(data)})

        return jsonify(
            {
                "status": "error",
                "message": data.get("message", "Unknown error"),
                "debug": data,
            }
        ), 400

    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        return jsonify(
            {
                "status": "error",
                "message": str(e),
                "debug": {"traceback": error_traceback, "error_type": type(e).__name__},
            }
        ), 500
