from flask import render_template, jsonify
from . import stats_bp
from process_data import process_data
from utils.json_utils import convert_for_json
import json

@stats_bp.route("/")
def statistics_index():
    """Handle statistics overview page."""
    print("DEBUG: Hit statistics index route")  # Debug print
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Calculate overall statistics
        overall_stats = {
            "total_dmrs": 0,
            "total_genes": 0,
            "total_edges": 0,
            "timepoint_count": len(results)
        }

        # Process timepoint data and accumulate overall stats
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                # Add to overall stats if bipartite graph is present
                if "bipartite_graph" in data:
                    graph = data["bipartite_graph"]
                    overall_stats["total_dmrs"] += sum(1 for n, d in graph.nodes(data=True) if d["bipartite"] == 0)
                    overall_stats["total_genes"] += sum(1 for n, d in graph.nodes(data=True) if d["bipartite"] == 1)
                    overall_stats["total_edges"] += graph.number_of_edges()

                # Extract stats for this timepoint
                timepoint_info[timepoint] = {
                    "status": "success",
                    "stats": {
                        "coverage": data.get("stats", {}).get("coverage", {}),
                        "edge_coverage": data.get("stats", {}).get("edge_coverage", {}),
                        "components": data.get("stats", {}).get("components", {}),
                        "bicliques_summary": data.get("stats", {}).get("bicliques_summary", {})
                    },
                    "message": ""
                }
                
                if timepoint == "DSStimeseries":
                    print("\nDEBUG: DSStimeseries Stats:")
                    print(json.dumps(timepoint_info[timepoint]["stats"], indent=2))
            else:
                timepoint_info[timepoint] = {
                    "status": "error",
                    "message": data.get("message", "Unknown error"),
                    "stats": {}
                }

        # Convert to JSON-safe format before sending to template
        safe_timepoint_info = convert_for_json(timepoint_info)
        safe_overall_stats = convert_for_json(overall_stats)

        # Debug print for statistics
        for timepoint, data in safe_timepoint_info.items():
            print(f"\nDEBUG: Statistics for {timepoint}:")
            print("Components:")
            if 'stats' in data and 'components' in data['stats']:
                print(json.dumps(data['stats']['components'], indent=2))
        
            print("\nInteresting Components:")
            if 'interesting_components' in data:
                print(json.dumps(data['interesting_components'], indent=2))
        
            print("\nComplex Components:")
            if 'complex_components' in data:
                print(json.dumps(data['complex_components'], indent=2))

        return render_template(
            "statistics.html",
            timepoint_info=safe_timepoint_info,
            statistics=safe_overall_stats  # Add overall stats to template context
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
            timepoint_data = {
                "status": "success",
                "stats": {
                    "coverage": data.get("stats", {}).get("coverage", {}),
                    "edge_coverage": data.get("stats", {}).get("edge_coverage", {}),
                    "components": data.get("stats", {}).get("components", {}),
                    "bicliques_summary": data.get("stats", {}).get("bicliques_summary", {})
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
