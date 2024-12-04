# statistics.py
import networkx as nx
from typing import List, Tuple, Set, Dict

def calculate_edge_coverage(graph: nx.Graph, bicliques: List[Tuple[Set[int], Set[int]]]) -> Dict:
    """
    Calculate edge coverage statistics for bicliques in the graph.
    
    Args:
        graph: NetworkX graph representing the bipartite structure
        bicliques: List of tuples, each containing sets of DMR and gene nodes forming a biclique
    
    Returns:
        Dictionary containing edge coverage statistics:
        - 'total': Total number of edges in the graph
        - 'covered': Number of edges covered by at least one biclique
        - 'single': Number of edges covered by exactly one biclique
        - 'multiple': Number of edges covered by more than one biclique
    """
    edge_coverage = {
        'total': len(graph.edges()),
        'covered': 0,
        'single': 0,
        'multiple': 0
    }
    
    covered_edges = set()
    for biclique in bicliques:
        edges = set((u, v) for u in biclique[0] for v in biclique[1])
        new_edges = edges - covered_edges
        edge_coverage['covered'] += len(new_edges)
        if len(new_edges) == 1:
            edge_coverage['single'] += 1
        else:
            edge_coverage['multiple'] += len(new_edges)
        covered_edges.update(edges)
    
    return edge_coverage
