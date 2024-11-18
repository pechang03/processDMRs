# File : edge_classification.py
# Description : Edge classification module

from typing import Dict, Set, Tuple
import networkx as nx

def classify_edges(
    original_graph: nx.Graph,
    biclique_graph: nx.Graph
) -> Dict[str, Set[Tuple[int, int]]]:
    """
    Classify edges by comparing original and biclique graphs.

    Args:
        original_graph: The original input graph
        biclique_graph: The graph constructed from bicliques

    Returns:
        Dictionary containing sets of edges classified as:
            - permanent: edges present in both graphs
            - false_positive: edges in original but not in biclique graph
            - false_negative: edges in biclique but not in original graph
    """
    # Initialize edge sets
    permanent_edges = set()
    false_positive_edges = set()
    false_negative_edges = set()

    # Get all nodes (should be same in both graphs)
    nodes = set(original_graph.nodes())

    # Compare edges using pairwise enumeration
    for u in nodes:
        for v in nodes:
            if u < v:  # Only check each pair once
                # Normalize edge representation (smaller node ID first)
                edge = (u, v)

                # Check presence in both graphs
                in_original = original_graph.has_edge(u, v)
                in_biclique = biclique_graph.has_edge(u, v)

                if in_original and in_biclique:
                    permanent_edges.add(edge)
                elif in_original and not in_biclique:
                    false_positive_edges.add(edge)
                elif not in_original and in_biclique:
                    false_negative_edges.add(edge)

    # Create debug output
    print("\nEdge Classification Results:")
    print(f"Permanent edges: {len(permanent_edges)}")
    print(f"False positive edges: {len(false_positive_edges)}")
    print(f"False negative edges: {len(false_negative_edges)}")

    # Optional: Print first few edges of each type
    def print_edge_samples(edge_set: Set[Tuple[int, int]], label: str):
        if edge_set:
            sample = sorted(list(edge_set))[:5]
            print(f"\nSample {label}:")
            for edge in sample:
                print(f"  {edge}")

    print_edge_samples(permanent_edges, "permanent edges")
    print_edge_samples(false_positive_edges, "false positive edges")
    print_edge_samples(false_negative_edges, "false negative edges")

    return {
        "permanent": permanent_edges,
        "false_positive": false_positive_edges,
        "false_negative": false_negative_edges
    }

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
        print(f"Error: Not all edges classified. Found {total_edges}, expected
{expected_edges}")
        return False

    return True
