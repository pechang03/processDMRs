from flask import render_template, jsonify
from . import stats_bp
from process_data import process_data
from utils.json_utils import convert_for_json
import json

@stats_bp.route("/")
def statistics_index():
    """Handle statistics overview page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Calculate overall statistics by aggregating across all timepoints
        total_dmrs = 0
        total_genes = set()  # Use set to avoid counting duplicate genes
        total_edges = 0
        valid_timepoints = 0

        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                valid_timepoints += 1
                
                # Get graph from data
                graph = data.get("bipartite_graph")
                if graph and isinstance(graph, dict):  # Check if it's the converted dict format
                    # Count DMRs and genes from converted graph format
                    node_attrs = graph.get("node_attributes", {})
                    dmrs = len([n for n, d in node_attrs.items() if d.get("bipartite") == 0])
                    genes = [n for n, d in node_attrs.items() if d.get("bipartite") == 1]
                    edges = len(graph.get("edges", []))
                    
                    total_dmrs += dmrs
                    total_genes.update(genes)  # Add to set to avoid duplicates
                    total_edges += edges

        overall_stats = {
            "graph_info": {
                "total_dmrs": total_dmrs,
                "total_genes": len(total_genes),  # Get unique count
                "total_edges": total_edges,
                "timepoints": valid_timepoints
            }
        }

        # Process timepoint data
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                # Extract complete stats for this timepoint
                timepoint_info[timepoint] = {
                    "status": "success",
                    "stats": data.get("stats", {}),  # Include all stats
                    "coverage": data.get("coverage", {}),
                    "edge_coverage": data.get("edge_coverage", {}),
                    "components": data.get("stats", {}).get("components", {}),
                    "dominating_set": data.get("dominating_set", {}),
                    "bicliques_summary": data.get("bicliques_summary", {}),
                    "message": ""
                }
            else:
                timepoint_info[timepoint] = {
                    "status": "error",
                    "message": data.get("message", "Unknown error"),
                    "stats": {}
                }

        # Convert to JSON-safe format
        safe_timepoint_info = convert_for_json(timepoint_info)
        safe_overall_stats = convert_for_json(overall_stats)

        return render_template(
            "statistics.html",
            timepoint_info=safe_timepoint_info,
            overall_stats=safe_overall_stats,
            statistics=safe_timepoint_info.get(next(iter(safe_timepoint_info), ""), {})
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
        if "error" in results or timepoint not in results:
            return jsonify({"status": "error", "message": "Timepoint not found"})

        data = results[timepoint]
        if isinstance(data, dict) and "error" not in data:
            # Ensure we have the expected structure
            timepoint_data = {
                "status": "success",
                "data": {  # Wrap everything in a data field
                    "stats": {
                        "coverage": data.get("stats", {}).get("coverage", {}),
                        "edge_coverage": data.get("stats", {}).get("edge_coverage", {}),
                        "components": data.get("stats", {}).get("components", {}),
                        "bicliques_summary": data.get("stats", {}).get("bicliques_summary", {})
                    },
                    "interesting_components": data.get("interesting_components", []),
                    "complex_components": data.get("complex_components", [])
                }
            }
            return jsonify(convert_for_json(timepoint_data))

        return jsonify({
            "status": "error",
            "message": data.get("message", "Unknown error")
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })
