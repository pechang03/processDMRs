from flask import render_template
from . import stats_bp
from process_data import process_data
from utils.json_utils import convert_for_json

@stats_bp.route('/')
def statistics_route():
    """Handle main statistics page."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        overall_data = results.get("overall", {})
        
        # Create complete statistics dictionary
        template_data = {
            "statistics": {
                # Basic stats
                "total_dmrs": overall_data.get("stats", {}).get("total_dmrs", 0),
                "total_genes": overall_data.get("stats", {}).get("total_genes", 0),
                "total_edges": overall_data.get("stats", {}).get("total_edges", 0),
                
                # Component stats
                "stats": {
                    "components": {
                        "original": {
                            "triconnected": overall_data.get("stats", {})
                                .get("components", {})
                                .get("original", {})
                                .get("triconnected", {})
                        }
                    }
                },
                
                # Interesting and complex components
                "interesting_components": overall_data.get("interesting_components", []),
                "complex_components": overall_data.get("complex_components", []),
                
                # Coverage and other stats
                "coverage": overall_data.get("stats", {}).get("coverage", {}),
                "edge_coverage": overall_data.get("stats", {}).get("edge_coverage", {})
            },
            
            # Timepoint specific data
            "timepoint_info": {
                timepoint: {
                    "status": "success",
                    "stats": convert_for_json(data.get("stats", {})),
                    "coverage": data.get("stats", {}).get("coverage", {}),
                    "components": data.get("stats", {}).get("components", {})
                }
                for timepoint, data in results.items()
                if isinstance(data, dict) and "error" not in data
            }
        }

        # Debug print to verify data
        print("\nDebug: Statistics Data Structure")
        print("Triconnected components:", 
              len(template_data["statistics"]["stats"]["components"]["original"]["triconnected"].get("components", [])))
        print("Interesting components:", 
              len(template_data["statistics"]["interesting_components"]))
        print("Complex components:", 
              len(template_data["statistics"]["complex_components"]))
        
        return render_template("statistics.html", **template_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))

@stats_bp.route('/coverage')
def coverage_stats_route():
    """Handle coverage statistics page."""
    results = process_data()
    overall_data = results.get("overall", {})
    coverage_stats = convert_for_json(overall_data.get("stats", {}).get("coverage", {}))
    return render_template("components/stats/coverage.html", statistics={"coverage": coverage_stats})

@stats_bp.route('/edge-coverage')
def edge_coverage_stats_route():
    """Handle edge coverage statistics page."""
    results = process_data()
    overall_data = results.get("overall", {})
    edge_stats = convert_for_json(overall_data.get("stats", {}).get("edge_coverage", {}))
    return render_template("components/stats/edge_coverage.html", statistics={"edge_coverage": edge_stats})

@stats_bp.route('/dominating-set')
def dominating_set_stats_route():
    """Handle dominating set statistics page."""
    results = process_data()
    overall_data = results.get("overall", {})
    dominating_stats = convert_for_json(overall_data.get("stats", {}).get("dominating_set", {}))
    return render_template("components/stats/dominating_set.html", statistics={"dominating_set": dominating_stats})

@stats_bp.route('/coverage')
def coverage_stats_route():
    """Handle coverage statistics page."""
    results = process_data()
    overall_data = results.get("overall", {})
    coverage_stats = convert_for_json(overall_data.get("stats", {}).get("coverage", {}))
    return render_template("components/stats/coverage.html", statistics={"coverage": coverage_stats})

@stats_bp.route('/edge-coverage')
def edge_coverage_stats_route():
    """Handle edge coverage statistics page."""
    results = process_data()
    overall_data = results.get("overall", {})
    edge_stats = convert_for_json(overall_data.get("stats", {}).get("edge_coverage", {}))
    return render_template("components/stats/edge_coverage.html", statistics={"edge_coverage": edge_stats})

@stats_bp.route('/dominating-set')
def dominating_set_stats_route():
    """Handle dominating set statistics page."""
    results = process_data()
    overall_data = results.get("overall", {})
    dominating_stats = convert_for_json(overall_data.get("stats", {}).get("dominating_set", {}))
    return render_template("components/stats/dominating_set.html", statistics={"dominating_set": dominating_stats})
