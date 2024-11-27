# File : main_routes.py
# Author : Peter Shaw
# Created on : 27 Nov 2024

from flask import render_template
from . import main_bp
from process_data import process_data
from utils.json_utils import convert_for_json


@main_bp.route("/")
def index_route():
    """Handle main index page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Get overall data
        overall_data = results.get("overall", {})

        # Ensure complete statistics structure with defaults
        default_stats = {
            "components": {
                "original": {
                    "connected": {
                        "total": 0,
                        "single_node": 0,
                        "small": 0,
                        "interesting": 0,
                    },
                    "biconnected": {
                        "total": 0,
                        "single_node": 0,
                        "small": 0,
                        "interesting": 0,
                    },
                    "triconnected": {
                        "total": 0,
                        "single_node": 0,
                        "small": 0,
                        "interesting": 0,
                    },
                },
                "biclique": {
                    "connected": {
                        "total": 0,
                        "single_node": 0,
                        "small": 0,
                        "interesting": 0,
                    },
                    "biconnected": {
                        "total": 0,
                        "single_node": 0,
                        "small": 0,
                        "interesting": 0,
                    },
                    "triconnected": {
                        "total": 0,
                        "single_node": 0,
                        "small": 0,
                        "interesting": 0,
                    },
                },
            },
            "coverage": {
                "dmrs": {"covered": 0, "total": 0, "percentage": 0},
                "genes": {"covered": 0, "total": 0, "percentage": 0},
                "edges": {
                    "single_coverage": 0,
                    "multiple_coverage": 0,
                    "uncovered": 0,
                    "total": 0,
                    "single_percentage": 0,
                    "multiple_percentage": 0,
                    "uncovered_percentage": 0,
                },
            },
        }

        # Process timepoint data including overall
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict):
                # Get existing stats
                stats = data.get("stats", {})

                # Ensure triconnected data exists in components
                if "components" in stats:
                    for graph_type in ["original", "biclique"]:
                        if graph_type in stats["components"]:
                            if "triconnected" not in stats["components"][graph_type]:
                                stats["components"][graph_type]["triconnected"] = {
                                    "total": 0,
                                    "single_node": 0,
                                    "small": 0,
                                    "interesting": 0,
                                }

                # Merge with default structure
                merged_stats = default_stats.copy()
                if stats:
                    merged_stats["components"].update(stats.get("components", {}))
                    merged_stats["coverage"].update(stats.get("coverage", {}))

                timepoint_info[timepoint] = {
                    "status": "success" if "error" not in data else "error",
                    "message": data.get("error", ""),
                    "stats": merged_stats,
                    "coverage": data.get("coverage", {}),
                    "components": data.get("components", {}),
                }

        # Convert all data structures using JSON utils
        statistics = convert_for_json(overall_data.get("stats", default_stats))
        timepoint_info = convert_for_json(timepoint_info)
        overall_data = convert_for_json(overall_data)

        return render_template(
            "index.html",
            results=overall_data,
            statistics=statistics,
            timepoint_info=timepoint_info,
            dmr_metadata=overall_data.get("dmr_metadata", {}),
            gene_metadata=overall_data.get("gene_metadata", {}),
            bicliques_result=overall_data,
            coverage=overall_data.get("coverage", {}),
            node_labels=overall_data.get("node_labels", {}),
            dominating_set=overall_data.get("dominating_set", {}),
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))

