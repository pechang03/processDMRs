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

        # Process timepoint data
        timepoint_info = {}
        
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                # Extract stats directly from the timepoint data
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
                
                # Debug print for DSStimeseries
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

        return render_template(
            "statistics.html",
            timepoint_info=safe_timepoint_info
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
