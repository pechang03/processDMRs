from flask import render_template, request
import json
from extensions import app
from process_data import process_data
from visualization import (
    create_biclique_visualization,
    create_node_biclique_map,
    OriginalGraphLayout,
    CircularBicliqueLayout,
    SpringLogicalLayout,
)
from biclique_analysis.statistics import calculate_biclique_statistics
from biclique_analysis.classifier import classify_biclique

@app.template_filter('get_biclique_classification')
def get_biclique_classification(dmr_nodes, gene_nodes):
    """Template filter to get biclique classification."""
    return classify_biclique(set(dmr_nodes), set(gene_nodes))


def index_route():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Limit to first two components
        if "interesting_components" in results:
            results["interesting_components"] = results["interesting_components"][:2]

        bicliques = []
        if "interesting_components" in results:
            for component in results["interesting_components"]:
                if "raw_bicliques" in component:
                    bicliques.extend(component["raw_bicliques"])

        # Create properly structured statistics dictionary
        detailed_stats = {
            "coverage": results.get("coverage", {
                "dmrs": {"covered": 0, "total": 0, "percentage": 0},
                "genes": {"covered": 0, "total": 0, "percentage": 0},
                "edges": {
                    "single_coverage": 0,
                    "multiple_coverage": 0,
                    "uncovered": 0,
                    "total": 0,
                    "single_percentage": 0,
                    "multiple_percentage": 0,
                    "uncovered_percentage": 0
                }
            }),
            "components": results.get("component_stats", {}).get("components", {
                "original": {
                    "connected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0},
                    "biconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0}
                },
                "biclique": {
                    "connected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0},
                    "biconnected": {"total": 0, "single_node": 0, "small": 0, "interesting": 0}
                }
            }),
            "dominating_set": results.get("dominating_set", {
                "size": 0,
                "percentage": 0,
                "genes_dominated": 0,
                "components_with_ds": 0,
                "avg_size_per_component": 0
            }),
            "size_distribution": results.get("size_distribution", {}),
            "node_participation": results.get("node_participation", {}),
            "edge_coverage": results.get("edge_coverage", {
                "single": 0,
                "multiple": 0,
                "uncovered": 0
            })
        }

        return render_template(
            "index.html",
            results=results,
            statistics=detailed_stats,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            bicliques_result=results,
            coverage=results.get("coverage", {}),
            node_labels=results.get("node_labels", {}),
            dominating_set=results.get("dominating_set", {}),
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))


def statistics_route():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        bicliques = []
        if "interesting_components" in results:
            # Add debug logging
            print(
                f"Number of interesting components: {len(results['interesting_components'])}"
            )
            for component in results["interesting_components"]:
                if "raw_bicliques" in component:
                    bicliques.extend(component["raw_bicliques"])

        # Initialize detailed stats with proper structure
        detailed_stats = {
            "components": results.get("component_stats", {}).get("components", {}),
            "dominating_set": results.get(
                "dominating_set",
                {
                    "size": 0,
                    "percentage": 0,
                    "genes_dominated": 0,
                    "components_with_ds": 0,
                    "avg_size_per_component": 0,
                },
            ),
            "coverage": results.get("coverage", {}),
            "size_distribution": results.get("size_distribution", {}),
            "node_participation": results.get("node_participation", {}),
            "edge_coverage": results.get("edge_coverage", {}),
        }

        # Debug logging
        print("\nDetailed stats structure:")
        print("Components key exists:", "components" in detailed_stats)
        if "components" in detailed_stats:
            print("Biclique key exists:", "biclique" in detailed_stats["components"])
            if "biclique" in detailed_stats["components"]:
                print(
                    "Connected key exists:",
                    "connected" in detailed_stats["components"]["biclique"],
                )
                if "connected" in detailed_stats["components"]["biclique"]:
                    print(
                        "Interesting key exists:",
                        "interesting"
                        in detailed_stats["components"]["biclique"]["connected"],
                    )

        # Merge component stats more carefully
        if "component_stats" in results:
            if "components" not in detailed_stats:
                detailed_stats["components"] = {}
            # Update instead of replace
            detailed_stats["components"].update(
                results["component_stats"]["components"]
            )

        # Additional debug logging after merge
        print("\nFinal stats structure:")
        print("Keys in detailed_stats:", detailed_stats.keys())
        if "components" in detailed_stats:
            print("Keys in components:", detailed_stats["components"].keys())
            if "biclique" in detailed_stats["components"]:
                print(
                    "Keys in biclique:", detailed_stats["components"]["biclique"].keys()
                )

        # Add debug logging
        print(
            f"Statistics show {detailed_stats['components']['original']['connected']['interesting']} interesting components"
        )
        print(
            f"Results contain {len(results.get('interesting_components', []))} components"
        )

        # Debug output
        print(f"\nComponent Statistics:")
        print(
            f"Original graph components: {detailed_stats['components']['original']['connected']['interesting']}"
        )
        print(
            f"Biclique graph components: {detailed_stats['components']['biclique']['connected']['interesting']}"
        )
        print("Debug - Dominating Set Stats:", detailed_stats.get("dominating_set", {}))
        print(
            "\nFull detailed_stats structure:",
            json.dumps(detailed_stats, indent=2, default=str),
        )
        print("\nDEBUG - All components being passed to template:")
        if "interesting_components" in results:
            for comp in results["interesting_components"]:
                print(
                    f"Component {comp.get('id')}: {comp.get('dmrs', '?')} DMRs, {comp.get('total_genes', '?')} genes"
                )
        else:
            print("No interesting_components in results")
        return render_template(
            "statistics.html",
            statistics=detailed_stats,
            bicliques_result=results,  # Pass the full results
            selected_component_id=request.args.get("component_id", type=int),
            total_bicliques=len(bicliques),
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))

def component_detail_route(component_id):
    """Handle component detail page requests."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Find the requested component
        component = next(
            (c for c in results["interesting_components"] if c["id"] == component_id),
            None
        )
        
        if not component:
            return render_template("error.html", message=f"Component {component_id} not found")

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            gene_id_mapping=results.get("gene_id_mapping", {})
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))


from biclique_analysis.classifier import classify_biclique

@app.template_filter('get_biclique_classification')
def get_biclique_classification(dmr_nodes, gene_nodes):
    """Template filter to get biclique classification."""
    return classify_biclique(set(dmr_nodes), set(gene_nodes))
