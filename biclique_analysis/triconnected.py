
from typing import Tuple, List, Set, Dict
import networkx as nx
from .classifier import BicliqueSizeCategory, classify_component

def analyze_triconnected_components(graph: nx.Graph) -> Tuple[List[Set], Dict]:
    """
    Find and analyze triconnected components of a graph.
    
    Args:
        graph: NetworkX graph to analyze
        
    Returns:
        Tuple of:
        - List[Set]: Sets of nodes forming triconnected components
        - Dict: Statistics about the components
    """
    # First get connected components
    connected_components = list(nx.connected_components(graph))
    
    triconnected_components = []
    stats = {
        "total": 0,
        "single_node": 0,
        "small": 0,
        "interesting": 0,
        "avg_dmrs": 0,
        "avg_genes": 0,
        "skipped_simple": 0  # Track components we skip
    }
    
    total_dmrs = 0
    total_genes = 0
    
    for component in connected_components:
        subgraph = graph.subgraph(component)
        
        # Skip if component is simple (star-like with single DMR)
        dmr_nodes = {n for n in component if graph.nodes[n]['bipartite'] == 0}
        gene_nodes = {n for n in component if graph.nodes[n]['bipartite'] == 1}
        
        if len(dmr_nodes) == 1:  # Star-like component
            stats["skipped_simple"] += 1
            continue
            
        # For non-simple components, find separation pairs
        if len(component) > 3:  # Only process if enough nodes
            try:
                # Use NetworkX's implementation for now
                # In future could implement Hopcroft-Tarjan algorithm
                tricomps = find_separation_pairs(subgraph)
                
                for tricomp in tricomps:
                    triconnected_components.append(tricomp)
                    
                    # Classify component
                    tri_dmrs = {n for n in tricomp if graph.nodes[n]['bipartite'] == 0}
                    tri_genes = {n for n in tricomp if graph.nodes[n]['bipartite'] == 1}
                    
                    if len(tricomp) == 1:
                        stats["single_node"] += 1
                    elif len(tri_dmrs) <= 1 or len(tri_genes) <= 1:
                        stats["small"] += 1
                    else:
                        stats["interesting"] += 1
                        total_dmrs += len(tri_dmrs)
                        total_genes += len(tri_genes)
                        
                stats["total"] += len(tricomps)
                
            except nx.NetworkXError:
                # Handle case where triconnected decomposition fails
                stats["skipped_simple"] += 1
                continue
    
    # Calculate averages
    if stats["interesting"] > 0:
        stats["avg_dmrs"] = total_dmrs / stats["interesting"]
        stats["avg_genes"] = total_genes / stats["interesting"]
    
    return triconnected_components, stats, avg_dmrs, avg_genes, is_simple

def find_separation_pairs(graph: nx.Graph) -> List[Set]:
    """
    Find separation pairs (vertices whose removal disconnects graph).
    
    This is a placeholder implementation using NetworkX's biconnected components.
    Future implementation should use Hopcroft-Tarjan algorithm.
    """
    # For now, use biconnected components as approximation
    # Real implementation would find actual separation pairs
    bicomps = list(nx.biconnected_components(graph))
    
    # Further break down large bicomponents
    tricomps = []
    for bicomp in bicomps:
        if len(bicomp) > 3:
            # Find articulation points within bicomponent
            subgraph = graph.subgraph(bicomp)
            cut_vertices = list(nx.articulation_points(subgraph))
            
            if cut_vertices:
                # Use cut vertices to split component
                remaining = set(bicomp)
                for vertex in cut_vertices:
                    component = {vertex}
                    component.update(next(nx.bfs_edges(subgraph, vertex)))
                    tricomps.append(component)
                    remaining -= component
                if remaining:
                    tricomps.append(remaining)
            else:
                tricomps.append(bicomp)
        else:
            tricomps.append(bicomp)
            
    return tricomps
