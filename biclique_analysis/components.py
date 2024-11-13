import networkx as nx
from typing import List, Dict
from visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    calculate_node_positions
)

def process_components(
    bipartite_graph: nx.Graph, 
    bicliques_result: Dict,
    dmr_metadata: Dict[str, Dict] = None,  # Add these parameters
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None  # Add this parameter
) -> List[Dict]:
    """Process connected components of the graph."""
    print(f"Starting component processing...")  # Debug logging
    components = list(nx.connected_components(bipartite_graph))
    component_data = []

    print(f"Found {len(components)} components")  # Debug logging
    print(f"Number of bicliques: {len(bicliques_result['bicliques'])}")  # Debug logging

    for idx, component in enumerate(components):
        subgraph = bipartite_graph.subgraph(component)
        component_bicliques = []
        single_connection_genes = []

        # Get nodes in this component
        component_nodes = set(component)
        
        # First, collect all genes in bicliques
        genes_in_bicliques = set()
        for _, gene_nodes in bicliques_result["bicliques"]:
            genes_in_bicliques.update(gene_nodes)
        
        # Find genes with single DMR connections
        for node in component_nodes:
            if node in gene_id_mapping.values():  # If it's a gene
                if node not in genes_in_bicliques:  # And not in any biclique
                    neighbors = list(bipartite_graph.neighbors(node))
                    if len(neighbors) == 1:  # Single DMR connection
                        dmr = neighbors[0]
                        gene_name = reverse_gene_mapping.get(node, f"Gene_{node}")
                        single_connection_genes.append({
                            "gene": node,
                            "dmr": dmr,
                            "gene_name": gene_name,
                            "description": gene_metadata.get(gene_name, {}).get("description", "N/A")
                        })

        # Process bicliques as before
        for bidx, (dmr_nodes, gene_nodes) in enumerate(bicliques_result["bicliques"]):
            # Check if this biclique belongs to this component
            biclique_nodes = dmr_nodes | gene_nodes
            if biclique_nodes & component_nodes:  # If there's any overlap
                # Create reverse mapping for gene IDs to names
                reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()} if gene_id_mapping else {}
                
                biclique_info = {
                    "dmrs": sorted(list(dmr_nodes)),
                    "genes": sorted(list(gene_nodes)),
                    "size": f"{len(dmr_nodes)}×{len(gene_nodes)}",
                    "details": {
                        "dmrs": [
                            {
                                "id": f"DMR_{dmr+1}",
                                "area": dmr_metadata.get(f"DMR_{dmr+1}", {}).get("area", "N/A"),
                                "description": dmr_metadata.get(f"DMR_{dmr+1}", {}).get("description", "N/A")
                            } 
                            for dmr in dmr_nodes
                        ],
                        "genes": [
                            {
                                "name": reverse_gene_mapping.get(gene, f"Gene_{gene}"),
                                "description": gene_metadata.get(
                                    reverse_gene_mapping.get(gene, f"Gene_{gene}"), 
                                    {}
                                ).get("description", "N/A")
                            }
                            for gene in gene_nodes
                        ]
                    }
                }
                if len(dmr_nodes) > 1 or len(gene_nodes) > 1:
                    component_bicliques.append(biclique_info)

        if component_bicliques or single_connection_genes:
            dmr_count = len([n for n in subgraph.nodes() if bipartite_graph.nodes[n]["bipartite"] == 0])
            gene_count = len([n for n in subgraph.nodes() if bipartite_graph.nodes[n]["bipartite"] == 1])
            
            # Create visualization for this component
            node_biclique_map = create_node_biclique_map([
                (bic["dmrs"], bic["genes"]) for bic in component_bicliques
            ])
            
            node_positions = calculate_node_positions(
                [(set(bic["dmrs"]), set(bic["genes"])) for bic in component_bicliques],
                node_biclique_map
            )
            
            # Create node labels
            node_labels = {
                node: f"DMR_{node+1}" if bipartite_graph.nodes[node]["bipartite"] == 0 else f"Gene_{node}"
                for node in component_nodes
            }
            
            # Create visualization
            plotly_graph = create_biclique_visualization(
                [(set(bic["dmrs"]), set(bic["genes"])) for bic in component_bicliques],
                node_labels,
                node_positions,
                node_biclique_map,
                bipartite_graph=subgraph,  # Add this parameter
                dmr_metadata=dmr_metadata,  # Pass these parameters
                gene_metadata=gene_metadata
            )

            component_info = {
                "id": idx + 1,
                "size": len(component),
                "dmrs": dmr_count,
                "genes": gene_count,
                "bicliques": component_bicliques,
                "single_connection_genes": single_connection_genes,
                "plotly_graph": plotly_graph
            }
            component_data.append(component_info)
            print(f"Processed component {idx + 1} with {len(component_bicliques)} bicliques")  # Debug logging

    print(f"Completed processing {len(component_data)} components with bicliques")  # Debug logging
    return component_data
