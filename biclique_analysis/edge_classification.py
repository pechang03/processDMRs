# File : edge_classification.py
# Description : Edge classification module

from typing import Dict, List, Tuple, Set
from collections import defaultdict
import networkx as nx

from .edge_info import EdgeInfo

def analyze_bridge_edges(
    graph: nx.Graph, 
    bicliques: List[Tuple[Set[int], Set[int]]]
) -> Dict[str, Set[Tuple[int, int]]]:
    """
    Analyze bridge edges in bipartite graph context.
    
    In biclique analysis:
    - Bridge edges between bicliques are likely false positives
    - However, some bridges might represent legitimate biclique connections
    - Need to consider DMR-Gene relationship in classification
    """
    # Find traditional bridge edges
    bridges = set(nx.bridges(graph))
    
    # Create biclique membership map
    node_to_bicliques = defaultdict(set)
    for idx, (dmrs, genes) in enumerate(bicliques):
        for node in dmrs | genes:
            node_to_bicliques[node].add(idx)
            
    # Classify bridge edges
    false_positives = set()
    potential_true_bridges = set()
    
    for u, v in bridges:
        # Get biclique memberships
        u_bicliques = node_to_bicliques[u]
        v_bicliques = node_to_bicliques[v]
        
        # If nodes belong to different bicliques, likely false positive
        if not (u_bicliques & v_bicliques):
            false_positives.add((u, v))
        else:
            # Could be legitimate if connects DMR to gene within biclique structure
            if (graph.nodes[u].get('bipartite') != 
                graph.nodes[v].get('bipartite')):
                potential_true_bridges.add((u, v))
            else:
                false_positives.add((u, v))
    
    return {
        "false_positives": false_positives,
        "potential_true_bridges": potential_true_bridges
    }

def classify_edges(
    original_graph: nx.Graph,
    biclique_graph: nx.Graph,
    edge_sources: Dict[Tuple[int, int], Set[str]],
    bicliques: List[Tuple[Set[int], Set[int]]] = None,
) -> Dict[str, List[EdgeInfo]]:
    """
    Classify edges by comparing original and biclique graphs.
    
    Classifications:
    - permanent: edges present in both graphs
    - false_positive: edges in original but not in biclique graph
    - false_negative: edges in biclique but not in original graph
    - bridge_false_positive: bridge edges likely to be noise
    - potential_true_bridge: bridge edges that may be legitimate
    
    Args:
        original_graph: The original input graph
        biclique_graph: The graph constructed from bicliques
        edge_sources: Dictionary mapping edges to their data sources
        bicliques: Optional list of bicliques for bridge analysis
    """
    # Get basic classification first
    permanent_edges: List[EdgeInfo] = []
    false_positive_edges: List[EdgeInfo] = []
    false_negative_edges: List[EdgeInfo] = []

    # Process each connected component separately for efficiency
    for component in nx.connected_components(original_graph):
        orig_subgraph = original_graph.subgraph(component)
        bic_subgraph = biclique_graph.subgraph(component)
        
        nodes = sorted(component)  # Sort for consistent ordering
        for i, u in enumerate(nodes):
            for v in nodes[i+1:]:
                edge = (u, v)
                in_original = orig_subgraph.has_edge(u, v)
                in_biclique = bic_subgraph.has_edge(u, v)
                
                sources = edge_sources.get(edge, set())

                if in_original and in_biclique:
                    edge_info = EdgeInfo(edge, label="permanent", sources=sources)
                    permanent_edges.append(edge_info)
                elif in_original and not in_biclique:
                    edge_info = EdgeInfo(edge, label="false_positive", sources=sources)
                    false_positive_edges.append(edge_info)
                elif not in_original and in_biclique:
                    edge_info = EdgeInfo(edge, label="false_negative", sources=sources)
                    false_negative_edges.append(edge_info)

    # Get bridge analysis if bicliques provided
    bridge_analysis = None
    if bicliques is not None:
        bridge_analysis = analyze_bridge_edges(original_graph, bicliques)

    result = {
        "permanent": permanent_edges,
        "false_positive": false_positive_edges,
        "false_negative": false_negative_edges
    }
    
    if bridge_analysis is not None:
        result["bridge_edges"] = {
            "false_positives": [
                EdgeInfo(edge, label="bridge_false_positive") 
                for edge in bridge_analysis["false_positives"]
            ],
            "potential_true_bridges": [
                EdgeInfo(edge, label="potential_true_bridge") 
                for edge in bridge_analysis["potential_true_bridges"]
            ]
        }
    
    return result

def validate_edge_classification(
    classification: Dict[str, Set[Tuple[int, int]]],
    original_graph: nx.Graph,
    biclique_graph: nx.Graph
) -> bool:
    """
    Validate the edge classification results.

    Args:
        classification: Dictionary of classified edges
        original_graph: The original input graph
        biclique_graph: The graph constructed from bicliques

    Returns:
        True if classification is valid, False otherwise
    """
    # Get edge sets
    permanent = classification["permanent"]
    false_positive = classification["false_positive"]
    false_negative = classification["false_negative"]

    # Check for overlap between sets
    if (permanent & false_positive or
        permanent & false_negative or
        false_positive & false_negative):
        print("Error: Edge sets overlap")
        return False

    # Verify permanent edges are in both graphs
    for edge in permanent:
        if not (original_graph.has_edge(*edge) and biclique_graph.has_edge(*edge)):
            print(f"Error: Permanent edge {edge} not in both graphs")
            return False

    # Verify false positives are only in original graph
    for edge in false_positive:
        if not (original_graph.has_edge(*edge) and not biclique_graph.has_edge(*edge)):
            print(f"Error: False positive edge {edge} classification incorrect")
            return False

    # Verify false negatives are only in biclique graph
    for edge in false_negative:
        if not (not original_graph.has_edge(*edge) and biclique_graph.has_edge(*edge)):
            print(f"Error: False negative edge {edge} classification incorrect")
            return False

    # Verify all edges are classified
    total_edges = (len(permanent) + len(false_positive) + len(false_negative))
    expected_edges = (len(original_graph.edges()) +
                    len(biclique_graph.edges()) -
                    len(permanent))

    if total_edges != expected_edges:
        print(f"Error: Not all edges classified. Found {total_edges}, expected {expected_edges}")
        return False

    return True
