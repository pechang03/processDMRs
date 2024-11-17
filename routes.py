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
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        # Find the requested component
        component = None
        if "interesting_components" in results:
            for comp in results["interesting_components"]:
                if comp["id"] == component_id:
                    # Format the bicliques data structure
                    formatted_comp = comp.copy()
                    
                    # Create visualization if it doesn't exist
                    if "raw_bicliques" in formatted_comp and not formatted_comp.get("plotly_graph"):
                        try:
                            from visualization import (
                                create_biclique_visualization,
                                create_node_biclique_map,
                                calculate_node_positions
                            )
        
                            print(f"\nProcessing visualization for component {component_id}:")
                            print(f"Number of bicliques: {len(formatted_comp['raw_bicliques'])}")
        
                            # Create node_biclique_map for this component
                            node_biclique_map = create_node_biclique_map(formatted_comp["raw_bicliques"])
        
                            # Calculate positions
                            node_positions = calculate_node_positions(
                                formatted_comp["raw_bicliques"],
                                node_biclique_map
                            )
        
                            # Create visualization
                            viz_data = create_biclique_visualization(
                                formatted_comp["raw_bicliques"],
                                results.get("node_labels", {}),
                                node_positions,
                                node_biclique_map,
                                dmr_metadata=results.get("dmr_metadata", {}),
                                gene_metadata=results.get("gene_metadata", {}),
                                gene_id_mapping=results.get("gene_id_mapping", {})
                            )
        
                            # Store visualization data - ensure it's properly parsed JSON
                            try:
                                formatted_comp["plotly_graph"] = json.loads(viz_data)
                                print(f"Successfully created visualization for component {component_id}")
            
                                # Debug - check the structure
                                if isinstance(formatted_comp["plotly_graph"], dict):
                                    print("Visualization data is properly formatted as dictionary")
                                    if "data" in formatted_comp["plotly_graph"]:
                                        print(f"Number of traces: {len(formatted_comp['plotly_graph']['data'])}")
                            except json.JSONDecodeError as je:
                                print(f"Error parsing visualization JSON: {str(je)}")
                                formatted_comp["plotly_graph"] = None
                        except Exception as viz_error:
                            print(f"Error creating visualization: {str(viz_error)}")
                            import traceback
                            traceback.print_exc()
                    
                    # Format bicliques for display
                    if "raw_bicliques" in formatted_comp:
                        formatted_bicliques = []
                        for idx, biclique in enumerate(formatted_comp["raw_bicliques"]):
                            dmr_nodes, gene_nodes = biclique
                            
                            # Format DMR details
                            dmr_details = []
                            for dmr in dmr_nodes:
                                dmr_label = f"DMR_{dmr+1}"
                                dmr_details.append({
                                    "id": dmr_label,
                                    "area": results.get("dmr_metadata", {}).get(dmr_label, {}).get("area", "N/A")
                                })

                            # Format gene details
                            gene_details = []
                            for gene in gene_nodes:
                                gene_name = results.get("node_labels", {}).get(gene, f"Gene_{gene}")
                                gene_details.append({
                                    "name": gene_name,
                                    "description": results.get("gene_metadata", {}).get(gene_name, {}).get("description", "N/A"),
                                    "is_split": gene in formatted_comp.get("split_genes", [])
                                })

                            formatted_bicliques.append({
                                "size": f"{len(dmr_nodes)}x{len(gene_nodes)}",
                                "details": {
                                    "dmrs": dmr_details,
                                    "genes": gene_details
                                }
                            })
                        formatted_comp["bicliques"] = formatted_bicliques
                    component = formatted_comp
                    break

        if component is None:
            return render_template("error.html", message=f"Component {component_id} not found")

        # Debug print to check visualization data
        if component.get("plotly_graph"):
            print("Visualization data present in component")
        else:
            print("No visualization data found in component")

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
