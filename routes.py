from flask import render_template
from process_data import process_data
from biclique_analysis.statistics import calculate_biclique_statistics


def index():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Limit to first two components
        if "interesting_components" in results:
            results["interesting_components"] = results["interesting_components"][:2]

        # Create properly structured statistics dictionary
        detailed_stats = {
            "size_distribution": {},  # Initialize empty if not available
            "coverage": results.get("coverage", {
                "dmrs": {"covered": 0, "total": 0, "percentage": 0},
                "genes": {"covered": 0, "total": 0, "percentage": 0}
            }),
            "node_participation": {
                "dmrs": {},
                "genes": {}
            },
            "edge_coverage": {
                "single": 0,
                "multiple": 0,
                "uncovered": 0,
                "total": 0,
                "single_percentage": 0,
                "multiple_percentage": 0,
                "uncovered_percentage": 0
            }
        }

        return render_template(
            "index.html",
            results=results,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            statistics=detailed_stats,  # Pass the properly structured statistics
            bicliques_result=results,  # Add this line to pass component data
            coverage=results.get("coverage", {}),
            node_labels=results.get("node_labels", {})
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))

from flask import render_template, request  # Add this at the top
from process_data import process_data
from biclique_analysis.statistics import calculate_biclique_statistics

def statistics():
    """Handle the statistics route"""
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Get selected component ID from query parameters
        selected_component_id = request.args.get('component_id', type=int)
        
        # Create a properly structured statistics dictionary
        detailed_stats = {
            "size_distribution": {},
            "coverage": {
                "dmrs": {
                    "covered": results.get("coverage", {}).get("dmrs", {}).get("covered", 0),
                    "total": results.get("coverage", {}).get("dmrs", {}).get("total", 0),
                    "percentage": results.get("coverage", {}).get("dmrs", {}).get("percentage", 0)
                },
                "genes": {
                    "covered": results.get("coverage", {}).get("genes", {}).get("covered", 0),
                    "total": results.get("coverage", {}).get("genes", {}).get("total", 0),
                    "percentage": results.get("coverage", {}).get("genes", {}).get("percentage", 0)
                }
            },
            "node_participation": {
                "dmrs": {},
                "genes": {}
            },
            "edge_coverage": {
                "single": 0,
                "multiple": 0,
                "uncovered": 0,
                "total": 0,
                "single_percentage": 0,
                "multiple_percentage": 0,
                "uncovered_percentage": 0
            }
        }

        # Filter components based on selection
        components_to_process = []
        if selected_component_id and "interesting_components" in results:
            components_to_process = [
                comp for comp in results["interesting_components"] 
                if comp["id"] == selected_component_id
            ]
        elif "interesting_components" in results:
            components_to_process = results["interesting_components"]

        # Calculate statistics for selected component(s)
        size_dist = {}
        dmr_participation = {}
        gene_participation = {}
        
        for component in components_to_process:
            for biclique in component.get("raw_bicliques", []):
                dmr_nodes, gene_nodes = biclique
                size_key = (len(dmr_nodes), len(gene_nodes))
                size_dist[size_key] = size_dist.get(size_key, 0) + 1
                
                for dmr in dmr_nodes:
                    dmr_participation[dmr] = dmr_participation.get(dmr, 0) + 1
                for gene in gene_nodes:
                    gene_participation[gene] = gene_participation.get(gene, 0) + 1

        detailed_stats["size_distribution"] = size_dist

        # Calculate participation distributions
        for count in set(dmr_participation.values()):
            detailed_stats["node_participation"]["dmrs"][count] = len(
                [n for n, c in dmr_participation.items() if c == count]
            )
        for count in set(gene_participation.values()):
            detailed_stats["node_participation"]["genes"][count] = len(
                [n for n, c in gene_participation.items() if c == count]
            )

        return render_template(
            "statistics.html", 
            statistics=detailed_stats,
            bicliques_result=results,
            selected_component_id=selected_component_id
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))
