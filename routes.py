from flask import render_template, request
import json
from process_data import process_data
from visualization import (
    create_biclique_visualization,
    create_node_biclique_map,
    OriginalGraphLayout,  # Add this
    CircularBicliqueLayout,  # Add this
    SpringLogicalLayout,  # Add this
)
from biclique_analysis.statistics import calculate_biclique_statistics


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

        detailed_stats = results.get('component_stats', {})

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
            "components": results.get('component_stats', {}).get('components', {}),
            "dominating_set": results.get('dominating_set', {
                "size": 0,
                "percentage": 0,
                "genes_dominated": 0,
                "components_with_ds": 0,
                "avg_size_per_component": 0
            }),
            "coverage": results.get('coverage', {}),
            "size_distribution": results.get('size_distribution', {}),
            "node_participation": results.get('node_participation', {}),
            "edge_coverage": results.get('edge_coverage', {})
        }

        # Debug logging
        print("\nDetailed stats structure:")
        print("Components key exists:", "components" in detailed_stats)
        if "components" in detailed_stats:
            print("Biclique key exists:", "biclique" in detailed_stats["components"])
            if "biclique" in detailed_stats["components"]:
                print("Connected key exists:", "connected" in detailed_stats["components"]["biclique"])
                if "connected" in detailed_stats["components"]["biclique"]:
                    print("Interesting key exists:", "interesting" in detailed_stats["components"]["biclique"]["connected"])

        # Merge component stats more carefully
        if "component_stats" in results:
            if "components" not in detailed_stats:
                detailed_stats["components"] = {}
            # Update instead of replace
            detailed_stats["components"].update(results["component_stats"]["components"])

        # Additional debug logging after merge
        print("\nFinal stats structure:")
        print("Keys in detailed_stats:", detailed_stats.keys())
        if "components" in detailed_stats:
            print("Keys in components:", detailed_stats["components"].keys())
            if "biclique" in detailed_stats["components"]:
                print("Keys in biclique:", detailed_stats["components"]["biclique"].keys())

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
        print("Debug - Dominating Set Stats:", detailed_stats.get('dominating_set', {}))
        print("\nFull detailed_stats structure:", json.dumps(detailed_stats, indent=2, default=str))
        print("\nDEBUG - All components being passed to template:")
        if 'interesting_components' in results:
            for comp in results['interesting_components']:
                print(f"Component {comp.get('id')}: {comp.get('dmrs', '?')} DMRs, {comp.get('total_genes', '?')} genes")
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
    try:
        results = process_data()
        if "error" in results:
            return render_template("error.html", message=results["error"])

        bipartite_graph = results.get("bipartite_graph")
        if not bipartite_graph:
            return render_template(
                "error.html", message="Bipartite graph not found in results"
            )

        # Define edge_classifications from results
        edge_classifications = results.get("edge_classifications", {})

        # Find the requested component
        component = None
        if "interesting_components" in results:
            for comp in results["interesting_components"]:
                if comp["id"] == component_id:
                    component = comp
                    # Create visualization if not already present
                    if "plotly_graph" not in comp:
                        try:
                            node_biclique_map = create_node_biclique_map(
                                comp["raw_bicliques"]
                            )
                            # Use CircularBicliqueLayout for biclique visualization
                            layout = CircularBicliqueLayout()
                            node_positions = layout.calculate_positions(
                                bipartite_graph,
                                NodeInfo(
                                    all_nodes=set(bipartite_graph.nodes()),
                                    dmr_nodes={n for n, d in bipartite_graph.nodes(data=True) if d['bipartite'] == 0},
                                    regular_genes={n for n, d in bipartite_graph.nodes(data=True) if d['bipartite'] == 1},
                                    split_genes=set(),  # Will be populated during processing
                                    node_degrees={n: len(list(bipartite_graph.neighbors(n))) for n in bipartite_graph.nodes()},
                                    min_gene_id=min(results.get("gene_id_mapping", {}).values(), default=0)
                                )
                            )
                            
                                     # Create original graph layout for comparison                                                                                            
                            original_layout = OriginalGraphLayout()                                                                                                  
                            original_positions = original_layout.calculate_positions(                                                                                
                                bipartite_graph,                                                                                                                     
                                NodeInfo(                                                                                                                            
                                    all_nodes=set(bipartite_graph.nodes()),                                                                                          
                                    dmr_nodes={n for n, d in bipartite_graph.nodes(data=True) if d['bipartite'] == 0},                                               
                                    regular_genes={n for n, d in bipartite_graph.nodes(data=True) if d['bipartite'] == 1},                                           
                                    split_genes=set(),                                                                                                               
                                    node_degrees={n: len(list(bipartite_graph.neighbors(n))) for n in bipartite_graph.nodes()},                                      
                                    min_gene_id=min(results.get("gene_id_mapping", {}).values(), default=0)                                                          
                                ),                                                                                                                                   
                                layout_type="spring"                                                                                                                 
                            )                                                                                                                                        
                            component_viz = create_biclique_visualization(                                                                                           
                                comp["raw_bicliques"],                                                                                                               
                                results["node_labels"],                                                                                                              
                                node_positions,                                                                                                                      
                                edge_classifications,                                                                                                                
                                original_graph=bipartite_graph,                                                                                                      
                                bipartite_graph=results.get("biclique_graph"),  # The graph constructed from bicliques
                                original_node_positions=original_positions,                                                                                          
                                node_biclique_map=node_biclique_map,
                                dmr_metadata=results.get("dmr_metadata", {}),                                                                                        
                                gene_metadata=results.get("gene_metadata", {}),                                                                                      
                                gene_id_mapping=results.get("gene_id_mapping", {}),                                                                                  
                                dominating_set=results.get("dominating_set", set())  

                            comp["plotly_graph"] = json.loads(component_viz)
                        except Exception as e:
                            print(f"Error creating visualization: {str(e)}")
                    break

        if component is None:
            return render_template(
                "error.html", message=f"Component {component_id} not found"
            )

        return render_template(
            "components.html",
            component=component,
            dmr_metadata=results.get("dmr_metadata", {}),
            gene_metadata=results.get("gene_metadata", {}),
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template("error.html", message=str(e))
