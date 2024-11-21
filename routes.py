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
from biclique_analysis.classifier import (
    BicliqueSizeCategory,
    classify_biclique,
    classify_component
)


@app.template_filter("get_biclique_classification")
def get_biclique_classification(dmr_nodes, gene_nodes):
    """Template filter to get biclique classification."""
    category = classify_biclique(set(dmr_nodes), set(gene_nodes))
    return category.name.lower()  # Return string name of enum


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
            "coverage": results.get(
                "coverage",
                {
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
            ),
            "components": results.get("component_stats", {}).get(
                "components",
                {
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
                    },
                },
            ),
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
            "size_distribution": results.get("size_distribution", {}),
            "node_participation": results.get("node_participation", {}),
            "edge_coverage": {  # Restructure edge coverage to match template expectations
                "single_coverage": results.get("edge_coverage", {}).get("single", 0),
                "multiple_coverage": results.get("edge_coverage", {}).get(
                    "multiple", 0
                ),
                "uncovered": results.get("edge_coverage", {}).get("uncovered", 0),
                "total": sum(results.get("edge_coverage", {}).values()),
                "single_percentage": 0,
                "multiple_percentage": 0,
                "uncovered_percentage": 0,
            },
        }

        # Calculate percentages if we have a total
        total_edges = detailed_stats["edge_coverage"]["total"]
        if total_edges > 0:
            detailed_stats["edge_coverage"]["single_percentage"] = (
                detailed_stats["edge_coverage"]["single_coverage"] / total_edges
            )
            detailed_stats["edge_coverage"]["multiple_percentage"] = (
                detailed_stats["edge_coverage"]["multiple_coverage"] / total_edges
            )
            detailed_stats["edge_coverage"]["uncovered_percentage"] = (
                detailed_stats["edge_coverage"]["uncovered"] / total_edges
            )

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

        # Create properly structured statistics dictionary
        detailed_stats = {
            "components": results.get("component_stats", {}).get("components", {}),
            "dominating_set": results.get("dominating_set", {}),
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
            "edge_coverage": results.get("edge_coverage", {}),
            "biclique_types": results.get("biclique_types", {
                "empty": 0,
                "simple": 0,
                "interesting": 0,
                "complex": 0
            }),
            "size_distribution": results.get("size_distribution", {})
        }

        # Update edge coverage from biclique statistics if available
        if "biclique_stats" in results:
            detailed_stats["edge_coverage"] = results["biclique_stats"].get("edge_coverage", {})
            detailed_stats["coverage"]["edges"] = results["biclique_stats"].get("edge_coverage", {})

        print("\nDetailed stats being sent to template:")
        print(json.dumps(detailed_stats, indent=2))

        return render_template(
            "statistics.html",
            statistics=detailed_stats,
            bicliques_result=results
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))


def component_detail_route(component_id, type='biclique'):
    """Handle component detail page requests."""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        if type == 'triconnected':
            # Get triconnected component
            component = next(
                (c for c in results.get("statistics", {}).get("components", {}).get("original", {}).get("triconnected", {}).get("components", []) 
                 if c["id"] == component_id),
                None
            )
            if component:
                # Create spring layout visualization
                from visualization import SpringLogicalLayout
                layout = SpringLogicalLayout()
                subgraph = results["bipartite_graph"].subgraph(component["nodes"])
                positions = layout.calculate_positions(subgraph)
                
                # Create visualization using spring layout
                from visualization import create_biclique_visualization
                viz_data = create_biclique_visualization(
                    [],  # No bicliques for triconnected view
                    results["node_labels"],
                    positions,
                    {},  # No biclique map needed
                    {},  # No edge classifications needed
                    subgraph,  # Use the component subgraph
                    subgraph,  # Same graph for both parameters
                    original_node_positions=positions
                )
                component["visualization"] = viz_data
        else:
            # Original biclique component logic
            component = next(
                (c for c in results.get("interesting_components", []) if c["id"] == component_id),
                None
            )

        if not component:
            return render_template(
                "error.html", message=f"Component {component_id} not found"
            )

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            gene_id_mapping=results.get("gene_id_mapping", {}),
            component_type=type
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))


from biclique_analysis.classifier import classify_biclique


@app.template_filter("get_biclique_classification")
def get_biclique_classification(dmr_nodes, gene_nodes):
    """Template filter to get biclique classification."""
    category = classify_biclique(set(dmr_nodes), set(gene_nodes))
    return category.name.lower()
