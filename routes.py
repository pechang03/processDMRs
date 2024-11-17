from flask import render_template, request
from process_data import process_data

def index_route():
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Limit to first two components
        if "interesting_components" in results:
            results["interesting_components"] = results["interesting_components"][:2]

        return render_template(
            "index.html",
            results=results,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            bicliques_result=results,
            coverage=results.get("coverage", {}),
            node_labels=results.get("node_labels", {})
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

        selected_component_id = request.args.get('component_id', type=int)
        
        detailed_stats = {
            "size_distribution": {},
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

def component_detail_route(component_id):
    import json  # Make sure this is at the top
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Find the requested component
        component = None
        if "interesting_components" in results:
            for comp in results["interesting_components"]:
                if comp["id"] == component_id:
                    # Create a serializable version of the component
                    formatted_comp = {
                        "id": comp["id"],
                        "dmrs": comp.get("dmrs", 0),
                        "genes": comp.get("genes", 0),
                        "total_edges": comp.get("total_edges", 0),
                        "split_genes": [{"gene_name": g.get("gene_name", ""), 
                                       "description": g.get("description", ""),
                                       "bicliques": g.get("bicliques", [])} 
                                      for g in comp.get("split_genes", [])],
                        "bicliques": [{
                            "id": idx,
                            "details": {
                                "dmrs": [{"id": d, "area": results.get("dmr_metadata", {}).get(str(d), {}).get("area", "N/A")} 
                                        for d in b[0]] if isinstance(b, tuple) else [],
                                "genes": [{"name": str(g), 
                                          "description": results.get("gene_metadata", {}).get(str(g), {}).get("description", "N/A")}
                                        for g in b[1]] if isinstance(b, tuple) else []
                            }
                        } for idx, b in enumerate(comp.get("bicliques", []))],
                    }
                    
                    # Handle plotly_graph data separately
                    if "plotly_graph" in comp:
                        try:
                            # Ensure plotly_graph is proper JSON
                            if isinstance(comp["plotly_graph"], str):
                                formatted_comp["plotly_graph"] = json.loads(comp["plotly_graph"])
                            else:
                                formatted_comp["plotly_graph"] = comp["plotly_graph"]
                        except json.JSONDecodeError as je:
                            print(f"Error parsing plotly_graph JSON: {str(je)}")
                            formatted_comp["plotly_graph"] = None
                    
                    component = formatted_comp
                    break

        if component is None:
            return render_template("error.html", message=f"Component {component_id} not found")

        # Debug print
        print("Component data structure:")
        print(json.dumps(component, indent=2, default=str))

        # Add these debug prints
        print("\nComponent structure:")
        print(json.dumps({
            "id": component["id"],
            "dmrs": component.get("dmrs"),
            "genes": component.get("genes"),
            "total_edges": component.get("total_edges"),
            "has_plotly_graph": "plotly_graph" in component,
            "num_bicliques": len(component.get("bicliques", [])),
            "num_split_genes": len(component.get("split_genes", [])),
        }, indent=2))

        if "plotly_graph" in component:
            print("\nPlotly graph structure:")
            graph_data = component["plotly_graph"]
            print(f"Type: {type(graph_data)}")
            if isinstance(graph_data, str):
                try:
                    parsed = json.loads(graph_data)
                    print("Data keys:", list(parsed.keys()))
                    print("Number of traces:", len(parsed.get("data", [])))
                except json.JSONDecodeError as e:
                    print("Error parsing plotly_graph JSON:", str(e))
            elif isinstance(graph_data, dict):
                print("Data keys:", list(graph_data.keys()))
                print("Number of traces:", len(graph_data.get("data", [])))

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
            node_labels=results.get("node_labels", {})
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template("error.html", message=str(e))
