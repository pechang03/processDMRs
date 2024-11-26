"""Functions for generating embeddings of bicliques and components."""

from typing import List, Dict, Tuple, Set
import numpy as np
from sklearn.manifold import MDS
import networkx as nx

def generate_biclique_embeddings(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_info: Dict[int, Dict] = None,
    dimensions: int = 2,
    perplexity: float = 30.0,
    random_state: int = 42
) -> List[Dict]:
    """
    Generate embeddings for biclique visualization.
    
    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        node_info: Optional dict of node metadata
        dimensions: Number of dimensions for embedding (default 2)
        perplexity: Perplexity parameter for t-SNE (if used)
        random_state: Random seed for reproducibility
        
    Returns:
        List of dictionaries containing embedding info for each biclique
    """
    if not bicliques:
        return []
        
    # Create distance matrix between bicliques
    n_bicliques = len(bicliques)
    distances = np.zeros((n_bicliques, n_bicliques))
    
    # Calculate Jaccard distances between bicliques
    for i in range(n_bicliques):
        dmrs_i, genes_i = bicliques[i]
        nodes_i = dmrs_i | genes_i
        
        for j in range(i+1, n_bicliques):
            dmrs_j, genes_j = bicliques[j]
            nodes_j = dmrs_j | genes_j
            
            # Calculate Jaccard distance
            intersection = len(nodes_i & nodes_j)
            union = len(nodes_i | nodes_j)
            distance = 1 - (intersection / union if union > 0 else 0)
            
            distances[i,j] = distance
            distances[j,i] = distance
    
    # Use MDS for initial embedding
    mds = MDS(n_components=dimensions, 
              dissimilarity='precomputed',
              random_state=random_state)
    
    embeddings = mds.fit_transform(distances)
    
    # Create result dictionaries
    result = []
    for idx, (dmrs, genes) in enumerate(bicliques):
        embedding_dict = {
            "id": idx,
            "position": embeddings[idx].tolist(),
            "size": len(dmrs) + len(genes),
            "dmr_count": len(dmrs),
            "gene_count": len(genes),
            "nodes": sorted(dmrs | genes),
            "metadata": {
                "density": len(dmrs) * len(genes) / ((len(dmrs) + len(genes)) ** 2),
                "node_info": {
                    node: node_info.get(node, {}) for node in (dmrs | genes)
                } if node_info else {}
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
