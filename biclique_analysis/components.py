import networkx as nx
from typing import List, Dict, Tuple
from visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    calculate_node_positions
)

def find_interesting_components(
    bipartite_graph: nx.Graph, 
    bicliques_result: Dict,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None
) -> List[Dict]:
    """Find and analyze interesting components without visualization."""
    
    components = list(nx.connected_components(bipartite_graph))
    print(f"Found {len(components)} total components")
    
    interesting_components = []
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()} if gene_id_mapping else {}

    for idx, component in enumerate(components):
        subgraph = bipartite_graph.subgraph(component)
        
        # Get unique DMRs and genes in this component
        dmr_nodes = {n for n in component if bipartite_graph.nodes[n]["bipartite"] == 0}
        gene_nodes = {n for n in component if bipartite_graph.nodes[n]["bipartite"] == 1}

        # Collect component's bicliques
        component_raw_bicliques = []
        for dmr_nodes_bic, gene_nodes_bic in bicliques_result["bicliques"]:
            # Convert node IDs to integers if they're strings
            dmr_set = {int(d) if isinstance(d, str) else d for d in dmr_nodes_bic}
            gene_set = {int(g) if isinstance(g, str) else g for g in gene_nodes_bic}
            
            biclique_nodes = dmr_set | gene_set
            if biclique_nodes & set(component):
                component_raw_bicliques.append((dmr_set, gene_set))

        # Only process if component has interesting bicliques
        interesting_bicliques = [
            (dmr_nodes_bic, gene_nodes_bic) 
            for dmr_nodes_bic, gene_nodes_bic in component_raw_bicliques
            if len(dmr_nodes_bic) >= 3 and len(gene_nodes_bic) >= 3
        ]
        
        if interesting_bicliques:
            # Debug print
            print(f"\nComponent {idx + 1}:")
            print(f"DMRs: {len(dmr_nodes)}, Genes: {len(gene_nodes)}")
            print(f"Interesting bicliques: {len(interesting_bicliques)}")
            
            component_info = {
                "id": idx + 1,
                "size": len(component),
                "dmrs": len(dmr_nodes),
                "genes": len(gene_nodes),
                "component": component,
                "raw_bicliques": interesting_bicliques,
                "total_edges": len(subgraph.edges()),
            }
            interesting_components.append(component_info)
            
    return interesting_components

def visualize_component(
    component_info: Dict,
    bipartite_graph: nx.Graph,
    dmr_metadata: Dict[str, Dict],
    gene_metadata: Dict[str, Dict],
    gene_id_mapping: Dict[str, int]
) -> Dict:  # Change return type to Dict to include both visualization and data
    """Create visualization and data summary for a specific component."""
    
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    subgraph = bipartite_graph.subgraph(component_info["component"])
    
    # Create node labels
    node_labels = {}
    for node in component_info["component"]:
        if bipartite_graph.nodes[node]["bipartite"] == 0:
            # For DMRs, use DMR_1 format
            dmr_label = f"DMR_{node+1}"
            node_labels[node] = dmr_label
        else:
            # For genes, use actual gene name from reverse mapping
            gene_name = reverse_gene_mapping.get(node)
            if gene_name:
                node_labels[node] = gene_name
            else:
                node_labels[node] = f"Gene_{node}"
    
    # Create visualization
    node_biclique_map = create_node_biclique_map(component_info["raw_bicliques"])
    node_positions = calculate_node_positions(component_info["raw_bicliques"], node_biclique_map)
    
    # Generate biclique summary data
    biclique_data = []
    for idx, (dmr_nodes, gene_nodes) in enumerate(component_info["raw_bicliques"]):
        # Get DMR details
        dmrs = []
        for dmr_id in sorted(dmr_nodes):
            dmr_label = f"DMR_{dmr_id+1}"
            if dmr_label in dmr_metadata:
                dmrs.append({
                    "id": dmr_label,
                    "area": dmr_metadata[dmr_label].get("area", "N/A"),
                    "description": dmr_metadata[dmr_label].get("description", "N/A")
                })

        # Get gene details
        genes = []
        split_genes = []
        for gene_id in sorted(gene_nodes):
            gene_name = reverse_gene_mapping.get(gene_id, f"Gene_{gene_id}")
            gene_info = {
                "name": gene_name,
                "description": gene_metadata.get(gene_name, {}).get("description", "N/A")
            }
            # Check if it's a split gene (appears in multiple bicliques)
            if len(node_biclique_map.get(gene_id, [])) > 1:
                split_genes.append(gene_info)
            else:
                genes.append(gene_info)

        biclique_data.append({
            "id": idx + 1,
            "dmrs": dmrs,
            "genes": genes,
            "split_genes": split_genes,
            "size": {
                "dmrs": len(dmr_nodes),
                "genes": len(gene_nodes),
                "split_genes": len(split_genes)
            }
        })

    # Create visualization
    plotly_graph = create_biclique_visualization(
        component_info["raw_bicliques"],
        node_labels,
        node_positions,
        node_biclique_map,
        dmr_metadata=dmr_metadata,
        gene_metadata=gene_metadata,
        gene_id_mapping=gene_id_mapping,
        bipartite_graph=subgraph
    )

    return {
        "visualization": plotly_graph,
        "bicliques": biclique_data,
        "summary": {
            "component_id": component_info["id"],
            "total_nodes": component_info["size"],
            "total_dmrs": component_info["dmrs"],
            "total_genes": component_info["genes"],
            "total_edges": component_info["total_edges"],
            "total_bicliques": len(component_info["raw_bicliques"])
        }
    }

def process_components(
    bipartite_graph: nx.Graph, 
    bicliques_result: Dict,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None
) -> Tuple[List[Dict], List[Dict]]:
    """Process connected components of the graph."""
    
    interesting_components = find_interesting_components(
        bipartite_graph, 
        bicliques_result,
        dmr_metadata,
        gene_metadata,
        gene_id_mapping
    )
    
    # Only visualize first component initially
    if interesting_components:
        component_data = visualize_component(
            interesting_components[0],
            bipartite_graph,
            dmr_metadata,
            gene_metadata,
            gene_id_mapping
        )
        interesting_components[0].update(component_data)
    
    return interesting_components, []  # Empty list for simple_connections
