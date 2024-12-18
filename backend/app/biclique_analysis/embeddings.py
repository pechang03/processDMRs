"""Functions for generating embeddings of bicliques and components."""

from typing import List, Dict, Tuple, Set
import numpy as np
from sklearn.manifold import MDS
import networkx as nx
from rb_domination import greedy_rb_domination
from biclique_analysis.triconnected import analyze_triconnected_components

def generate_biclique_embeddings(
    bicliques: List[Tuple[Set[int], Set[int]]],
    graph: nx.Graph,
    connected_component_info: Dict,
    node_info: Dict[int, Dict] = None,
    dimensions: int = 2,
    random_state: int = 42
) -> List[Dict]:
    """
    Generate embeddings for biclique visualization within connected components.
    
    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        graph: Original bipartite graph
        connected_component_info: Dict containing RB dominating sets per component
        node_info: Optional dict of node metadata
        dimensions: Number of dimensions for embedding
        random_state: Random seed for reproducibility
    """
    if not bicliques:
        return []
        
    result = []
    for idx, (dmrs, genes) in enumerate(bicliques):
        # Find which connected component this biclique belongs to
        biclique_nodes = dmrs | genes
        for comp_id, comp_info in connected_component_info.items():
            if biclique_nodes & comp_info['nodes']:  # If there's overlap
                dominating_nodes = dmrs & comp_info['dominating_set']
                break
        else:
            dominating_nodes = set()  # No matching component found
            
        embedding_dict = {
            "id": idx,
            "size": len(dmrs) + len(genes),
            "dmr_count": len(dmrs),
            "gene_count": len(genes),
            "nodes": sorted(dmrs | genes),
            "dominating_nodes": sorted(dominating_nodes),
            "metadata": {
                "density": len(dmrs) * len(genes) / ((len(dmrs) + len(genes)) ** 2),
                "domination_ratio": len(dominating_nodes) / len(dmrs) if dmrs else 0,
                "node_info": {
                    node: node_info.get(node, {}) for node in (dmrs | genes)
                } if node_info else {}
            }
        }
        result.append(embedding_dict)
    
    return result

def generate_triconnected_embeddings(
    graph: nx.Graph,
    dimensions: int = 2,
    random_state: int = 42
) -> List[Dict]:
    """
    Generate embeddings for triconnected components visualization.
    
    Args:
        graph: NetworkX graph to analyze
        dimensions: Number of dimensions for embedding (default 2)
        random_state: Random seed for reproducibility
        
    Returns:
        List of dictionaries containing embedding info for each component
    """
    # Get triconnected components
    components, stats = analyze_triconnected_components(graph)
    result = []
    
    for idx, comp_nodes in enumerate(components):
        # Get component subgraph
        subgraph = graph.subgraph(comp_nodes)
        
        # Calculate spring layout for component
        pos = nx.spring_layout(
            subgraph,
            dim=dimensions,
            k=1/np.sqrt(len(comp_nodes)),
            iterations=50,
            seed=random_state
        )
        
        # Convert positions to list format
        positions = {
            node: list(coord) for node, coord in pos.items()
        }
        
        # Get DMR and gene counts
        dmrs = {n for n in comp_nodes if graph.nodes[n]['bipartite'] == 0}
        genes = {n for n in comp_nodes if graph.nodes[n]['bipartite'] == 1}
        
        # Create embedding dictionary
        embedding_dict = {
            "id": idx,
            "positions": positions,
            "size": len(comp_nodes),
            "nodes": sorted(comp_nodes),
            "metadata": {
                "dmr_count": len(dmrs),
                "gene_count": len(genes),
                "edge_count": subgraph.number_of_edges(),
                "density": 2 * subgraph.number_of_edges() / (len(comp_nodes) * (len(comp_nodes) - 1))
                          if len(comp_nodes) > 1 else 0
            }
        }
        result.append(embedding_dict)
    
    return result

def generate_component_embeddings(
    components: List[Dict],
    graph: nx.Graph,
    dimensions: int = 2,
    random_state: int = 42
) -> List[Dict]:
    """
    Generate embeddings for component visualization.
    
    Args:
        components: List of component dictionaries
        graph: Original graph containing components
        dimensions: Number of dimensions for embedding
        random_state: Random seed for reproducibility
        
    Returns:
        List of dictionaries containing embedding info for each component
    """
    result = []
    
    for idx, comp in enumerate(components):
        # Get component subgraph
        nodes = comp.get("component", set())
        if not nodes:
            continue
            
        subgraph = graph.subgraph(nodes)
        
        # Calculate spring layout for component
        pos = nx.spring_layout(
            subgraph,
            dim=dimensions,
            k=1/np.sqrt(len(nodes)),
            iterations=50,
            seed=random_state
        )
        
        # Convert positions to list format
        positions = {
            node: list(coord) for node, coord in pos.items()
        }
        
        # Create embedding dictionary
        embedding_dict = {
            "id": idx,
            "positions": positions,
            "size": len(nodes),
            "nodes": sorted(nodes),
            "metadata": {
                "category": comp.get("category", "unknown"),
                "dmr_count": comp.get("dmrs", 0),
                "gene_count": comp.get("genes", 0),
                "edge_count": comp.get("total_edges", 0),
                "density": 2 * comp.get("total_edges", 0) / (len(nodes) * (len(nodes) - 1))
                          if len(nodes) > 1 else 0
            }
        }
        result.append(embedding_dict)
    
    return result
