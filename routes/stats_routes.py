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

        # Process timepoint data
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                valid_timepoints += 1
                
                # Get graph info
                graph = data.get("bipartite_graph")
                if graph and isinstance(graph, dict):
                    node_attrs = graph.get("node_attributes", {})
                    dmrs = len([n for n, d in node_attrs.items() if d.get("bipartite") == 0])
                    genes = [n for n, d in node_attrs.items() if d.get("bipartite") == 1]
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
                    "components": convert_for_json(data.get("stats", {}).get("components", {})),
                    "dominating_set": convert_for_json(data.get("dominating_set", {})),
                    "bicliques_summary": convert_for_json(data.get("bicliques_summary", {})),
                    "interesting_components": convert_for_json(data.get("interesting_components", [])),
                    "complex_components": convert_for_json(data.get("complex_components", [])),
                    "message": ""
                }
            else:
                timepoint_info[timepoint] = {
                    "status": "error",
                    "message": data.get("message", "Unknown error"),
                    "stats": {}
                }

        overall_stats = {
            "graph_info": {
                "total_dmrs": total_dmrs,
                "total_genes": len(total_genes),
                "total_edges": total_edges,
                "timepoints": valid_timepoints
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
            statistics=initial_stats
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
            return jsonify({
                "status": "error", 
                "message": "Timepoint not found",
                "debug": {"available_timepoints": list(results.keys())}
            })

        data = results[timepoint]
        if isinstance(data, dict) and "error" not in data:
            # Get header stats directly from debug section
            header_stats = data.get("debug", {}).get("header_stats", {})
            
            # Get edge counts from coverage stats
            edge_stats = data.get("stats", {}).get("coverage", {}).get("edges", {})
            total_edges = (edge_stats.get("single_coverage", 0) + 
                         edge_stats.get("multiple_coverage", 0) + 
                         edge_stats.get("uncovered", 0))

            # Separate bicliques summary into its own section
            timepoint_data = {
                "status": "success",
                "data": {
                    "stats": {
                        "coverage": data.get("stats", {}).get("coverage", {}),
                        "edge_coverage": data.get("stats", {}).get("edge_coverage", {}),
                        "components": {
                            "original": data.get("stats", {}).get("components", {}).get("original", {}),
                            "biclique": data.get("stats", {}).get("components", {}).get("biclique", {})
                        }
                    },
                    "interesting_components": data.get("interesting_components", []),
                    "complex_components": data.get("complex_components", []),
                    "simple_components": data.get("simple_components", []),  # Add this
                    "non_simple_components": data.get("non_simple_components", []),  # Add this
                    "bicliques": data.get("bicliques", []),
                    "bicliques_summary": {
                        "graph_info": data.get("bicliques_summary", {}).get("graph_info", {}),
                        "header_stats": data.get("bicliques_summary", {}).get("header_stats", {})
                    }
                }
            }
            
            # Convert to JSON-safe format only when returning
            json_safe_data = convert_for_json(timepoint_data)
            
            print(f"\nTimepoint {timepoint} data being sent:")
            print(json.dumps(json_safe_data, indent=2))
            
            return jsonify(json_safe_data)

        return jsonify({
            "status": "error",
            "message": data.get("message", "Unknown error"),
            "debug": convert_for_json({
                "error_type": "DataError",
                "data_received": bool(data),
                "data_type": type(data).__name__,
                "data_keys": list(data.keys()) if isinstance(data, dict) else None
            })
        })

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error in timepoint_stats: {str(e)}\n{error_traceback}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "debug": convert_for_json({
                "traceback": error_traceback,
                "error_type": type(e).__name__,
                "error_details": {
                    "args": getattr(e, 'args', None),
                    "message": str(e),
                    "location": "timepoint_stats"
                }
            })
        })
