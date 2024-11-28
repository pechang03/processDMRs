from flask import render_template
from . import stats_bp
from process_data import process_data
from utils.json_utils import convert_for_json

@stats_bp.route('/')
def statistics_route():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        DSStimeseries_data = results.get("DSStimeseries", {})
        
        # Create timepoint info with proper structure
        timepoint_info = {}
        for timepoint, data in results.items():
            if isinstance(data, dict) and "error" not in data:
                timepoint_info[timepoint] = {
                    "status": "success",
                    "data": {  # Wrap data in a data key
                        "stats": data.get("stats", {
                            "coverage": {
                                "dmrs": {"covered": 0, "total": 0},
                                "genes": {"covered": 0, "total": 0}
                            }
                        }),
                        "coverage": data.get("coverage", {}),
                        "components": data.get("components", {})
                    }
                }

        # Convert all data structures
        template_data = convert_for_json({
            "statistics": {
                "total_dmrs": DSStimeseries_data.get("stats", {}).get("total_dmrs", 0),
                "total_genes": DSStimeseries_data.get("stats", {}).get("total_genes", 0),
                "total_edges": DSStimeseries_data.get("stats", {}).get("total_edges", 0),
                "components": DSStimeseries_data.get("stats", {}).get("components", {}),
                "coverage": DSStimeseries_data.get("stats", {}).get("coverage", {}),
                "edge_coverage": DSStimeseries_data.get("stats", {}).get("edge_coverage", {}),
                "bicliques_summary": DSStimeseries_data.get("stats", {}).get("bicliques_summary", {})
            },
            "timepoint_info": timepoint_info
        })

        return render_template(
            "statistics.html",
            statistics=template_data["statistics"],
            timepoint_info=template_data["timepoint_info"],
            DSStimeseries_data=convert_for_json(DSStimeseries_data)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))

@stats_bp.route('/coverage')
def coverage_stats_route():
    """Handle coverage statistics page."""
    results = process_data()
    DSStimeseries_data = results.get("DSStimeseries", {})
    coverage_stats = convert_for_json(DSStimeseries_data.get("stats", {}).get("coverage", {}))
    return render_template("components/stats/coverage.html", statistics={"coverage": coverage_stats})

@stats_bp.route('/edge-coverage')
def edge_coverage_stats_route():
    """Handle edge coverage statistics page."""
    results = process_data()
    DSStimeseries_data = results.get("DSStimeseries", {})
    edge_stats = convert_for_json(DSStimeseries_data.get("stats", {}).get("edge_coverage", {}))
    return render_template("components/stats/edge_coverage.html", statistics={"edge_coverage": edge_stats})

@stats_bp.route('/dominating-set')
def dominating_set_stats_route():
    """Handle dominating set statistics page."""
    results = process_data()
    DSStimeseries_data = results.get("DSStimeseries", {})
    dominating_stats = convert_for_json(DSStimeseries_data.get("stats", {}).get("dominating_set", {}))
    return render_template("components/stats/dominating_set.html", statistics={"dominating_set": dominating_stats})
