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

@main_bp.route("/statistics/")
@main_bp.route("/statistics")
def statistics_route():
    """Handle statistics page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Calculate overall statistics
        total_dmrs = 0
        total_genes = 0
        total_edges = 0
        timepoint_info = {}

        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                # Ensure proper data structure
                stats = data.get("stats", {})
                if not isinstance(stats, dict):
                    stats = {}
                
                timepoint_info[timepoint] = {
                    "status": "success",
                    "stats": {
                        "components": {
                            "original": {
                                "connected": stats.get("components", {}).get("original", {}).get("connected", {}),
                                "biconnected": stats.get("components", {}).get("original", {}).get("biconnected", {}),
                                "triconnected": stats.get("components", {}).get("original", {}).get("triconnected", {})
                            },
                            "biclique": {
                                "connected": stats.get("components", {}).get("biclique", {}).get("connected", {}),
                                "biconnected": stats.get("components", {}).get("biclique", {}).get("biconnected", {}),
                                "triconnected": stats.get("components", {}).get("biclique", {}).get("triconnected", {})
                            }
                        },
                        "coverage": stats.get("coverage", {}),
                        "edge_coverage": stats.get("edge_coverage", {})
                    }
                }

                # Update totals
                graph_info = data.get("graph_info", {})
                total_dmrs += graph_info.get("total_dmrs", 0)
                total_genes += len(set(graph_info.get("gene_nodes", [])))
                total_edges += graph_info.get("total_edges", 0)

        # Structure the template data
        statistics = {
            "total_dmrs": total_dmrs,
            "total_genes": total_genes,
            "total_edges": total_edges,
            "timepoint_count": len([k for k in results.keys() if k != "overall"])
        }

        return render_template(
            "statistics.html",
            statistics=statistics,
            timepoint_info=timepoint_info
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))

@main_bp.route("/component/<int:component_id>")
def component_detail_route(component_id):
    """Handle component detail page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Find the requested component
        component = next(
            (c for c in results.get("interesting_components", []) 
             if c["id"] == component_id),
            None
        )

        if not component:
            return render_template(
                "error.html", 
                message=f"Component {component_id} not found"
            )

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

