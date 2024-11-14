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
            biclique_nodes = dmr_nodes_bic | gene_nodes_bic
            if biclique_nodes & set(component):
                component_raw_bicliques.append((dmr_nodes_bic, gene_nodes_bic))

        # Only process if component has interesting bicliques
        interesting_bicliques = [
            (dmr_nodes_bic, gene_nodes_bic) 
            for dmr_nodes_bic, gene_nodes_bic in component_raw_bicliques
            if len(dmr_nodes_bic) >= 3 and len(gene_nodes_bic) >= 3
        ]
        
        if interesting_bicliques:
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
) -> str:
    """Create visualization for a specific component."""
    
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    subgraph = bipartite_graph.subgraph(component_info["component"])
    
    # Create node labels
    node_labels = {}
    for node in component_info["component"]:
        if bipartite_graph.nodes[node]["bipartite"] == 0:
            node_labels[node] = f"DMR_{node+1}"
        else:
            node_labels[node] = reverse_gene_mapping.get(node, f"Gene_{node}")
    
    # Create visualization
    node_biclique_map = create_node_biclique_map(component_info["raw_bicliques"])
    node_positions = calculate_node_positions(component_info["raw_bicliques"], node_biclique_map)
    
    return create_biclique_visualization(
        component_info["raw_bicliques"],
        node_labels,
        node_positions,
        node_biclique_map,
        dmr_metadata=dmr_metadata,
        gene_metadata=gene_metadata,
        gene_id_mapping=gene_id_mapping,
        bipartite_graph=subgraph
    )

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
        plotly_graph = visualize_component(
            interesting_components[0],
            bipartite_graph,
            dmr_metadata,
            gene_metadata,
            gene_id_mapping
        )
        interesting_components[0]["plotly_graph"] = plotly_graph
    
    return interesting_components, []  # Empty list for simple_connections
