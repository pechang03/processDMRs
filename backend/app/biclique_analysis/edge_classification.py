# File : edge_classification.py
# Description : Edge classification module

from typing import Dict, List, Tuple, Set
from collections import defaultdict
import networkx as nx

from backend.app.utils.edge_info import EdgeInfo
from backend.app.biclique_analysis.classifier import BicliqueSizeCategory


def analyze_bridge_edges(
    graph: nx.Graph, bicliques: List[Tuple[Set[int], Set[int]]]
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
            if graph.nodes[u].get("bipartite") != graph.nodes[v].get("bipartite"):
                potential_true_bridges.add((u, v))
            else:
                false_positives.add((u, v))

    return {
        "false_positives": false_positives,
        "potential_true_bridges": potential_true_bridges,
    }


def calculate_edge_statistics(
    total_edges: int,
    permanent_edges: int,
    false_positives: int,
    false_negatives: int
) -> Dict[str, float]:
    """Calculate statistical measures for edge classification reliability."""
    # Total possible edges in the comparison
    total_compared = total_edges + false_negatives
    
    # Calculate error rates
    false_positive_rate = false_positives / total_edges if total_edges > 0 else 0
    false_negative_rate = false_negatives / total_compared if total_compared > 0 else 0
    
    # Calculate accuracy
    correct_edges = permanent_edges
    accuracy = correct_edges / total_compared if total_compared > 0 else 0
    
    # Calculate noise percentage (combined error rate)
    noise_percentage = ((false_positives + false_negatives) / 
                       (total_edges + false_negatives)) * 100 if total_edges > 0 else 0
    
    return {
        "accuracy": accuracy,
        "noise_percentage": noise_percentage,
        "false_positive_rate": false_positive_rate,
        "false_negative_rate": false_negative_rate
    }

def classify_edges(
    original_graph: nx.Graph,
    biclique_graph: nx.Graph,
    edge_sources: Dict[Tuple[int, int], Set[str]],
    bicliques: List[Tuple[Set[int], Set[int]]] = None,
) -> Dict[str, List[EdgeInfo]]:
    """Classify edges and calculate edge classification statistics."""
    
    # First validate node sets match
    original_nodes = set(original_graph.nodes())
    biclique_nodes = set(biclique_graph.nodes())
    
    if original_nodes != biclique_nodes:
        raise ValueError(
            f"Node mismatch: Original graph has {len(original_nodes)} nodes, "
            f"Biclique graph has {len(biclique_nodes)} nodes"
        )

    # Initialize classification containers
    permanent_edges: List[EdgeInfo] = []
    false_positive_edges: List[EdgeInfo] = []
    false_negative_edges: List[EdgeInfo] = []

    # Process each connected component from original graph
    for component in nx.connected_components(original_graph):
        orig_subgraph = original_graph.subgraph(component)
        bic_subgraph = biclique_graph.subgraph(component)

        # Process edges within this component
        for u, v in orig_subgraph.edges():
            edge = (min(u, v), max(u, v))
            sources = edge_sources.get(edge, set())
            
            if bic_subgraph.has_edge(u, v):
                edge_info = EdgeInfo(edge, label="permanent", sources=sources)
                permanent_edges.append(edge_info)
            else:
                edge_info = EdgeInfo(edge, label="false_positive", sources=sources)
                false_positive_edges.append(edge_info)

        # Check for edges in biclique graph not in original
        for u, v in bic_subgraph.edges():
            if not orig_subgraph.has_edge(u, v):
                edge = (min(u, v), max(u, v))
                edge_info = EdgeInfo(edge, label="false_negative", sources=set())
                false_negative_edges.append(edge_info)

    # Calculate per-biclique false negative statistics
    biclique_false_negatives = defaultdict(int)
    if bicliques:
        for edge_info in false_negative_edges:
            u, v = edge_info.edge
            # Find which biclique(s) this edge belongs to
            for idx, biclique in enumerate(bicliques):
                # Safely unpack biclique tuple, expecting only dmrs and genes
                if len(biclique) >= 2:  # Check if we have at least 2 elements
                    dmrs, genes = biclique[:2]  # Take first two elements only
                    if (u in dmrs and v in genes) or (v in dmrs and u in genes):
                        biclique_false_negatives[idx] += 1

    # Initialize per-biclique statistics
    biclique_stats = defaultdict(lambda: {
        "total_edges": 0,
        "permanent": 0,
        "false_positives": 0,
        "false_negatives": 0
    })

    # Calculate per-biclique statistics
    if bicliques:
        for idx, biclique in enumerate(bicliques):
            if len(biclique) >= 2:
                dmrs, genes = biclique[:2]
                # Count edges in original graph for this biclique
                biclique_edges = set()
                for u in dmrs:
                    for v in genes:
                        if original_graph.has_edge(u, v):
                            biclique_edges.add((min(u, v), max(u, v)))
                            if biclique_graph.has_edge(u, v):
                                biclique_stats[idx]["permanent"] += 1
                            else:
                                biclique_stats[idx]["false_positives"] += 1
                
                # Count false negatives
                for u in dmrs:
                    for v in genes:
                        edge = (min(u, v), max(u, v))
                        if (biclique_graph.has_edge(u, v) and 
                            not original_graph.has_edge(u, v)):
                            biclique_stats[idx]["false_negatives"] += 1
                
                biclique_stats[idx]["total_edges"] = len(biclique_edges)

    # Calculate component-wide statistics
    component_stats = calculate_edge_statistics(
        total_edges=len(original_graph.edges()),
        permanent_edges=len(permanent_edges),
        false_positives=len(false_positive_edges),
        false_negatives=len(false_negative_edges)
    )

    # Calculate per-biclique statistics
    biclique_reliability = {}
    for idx, stats in biclique_stats.items():
        biclique_reliability[idx] = calculate_edge_statistics(
            total_edges=stats["total_edges"],
            permanent_edges=stats["permanent"],
            false_positives=stats["false_positives"],
            false_negatives=stats["false_negatives"]
        )

    return {
        "permanent": permanent_edges,
        "false_positive": false_positive_edges,
        "false_negative": false_negative_edges,
        "component_stats": component_stats,
        "biclique_stats": {
            "edge_counts": dict(biclique_stats),
            "reliability": biclique_reliability,
            "total_false_negatives": len(false_negative_edges)
        }
    }


def validate_edge_classification(
    classification: Dict[str, Set[Tuple[int, int]]],
    original_graph: nx.Graph,
    biclique_graph: nx.Graph,
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
    if (
        permanent & false_positive
        or permanent & false_negative
        or false_positive & false_negative
    ):
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
    total_edges = len(permanent) + len(false_positive) + len(false_negative)
    expected_edges = (
        len(original_graph.edges()) + len(biclique_graph.edges()) - len(permanent)
    )

    if total_edges != expected_edges:
        print(
            f"Error: Not all edges classified. Found {total_edges}, expected {expected_edges}"
        )
        return False

    return True


def create_biclique_edge_classifications(
    bicliques: List[Tuple[Set[int], Set[int]]],
    edge_classification: Dict[str, List[EdgeInfo]],
) -> List[Dict]:
    """
    Create structured edge classification data for each biclique.

    Returns:
        List of dictionaries, one per biclique, containing:
        - biclique_id
        - edge_counts: counts by classification
        - edges: list of {source, target, label, sources}
    """
    result = []

    for b_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        biclique_data = {
            "biclique_id": b_idx,
            "edge_counts": {label: 0 for label in EdgeInfo.VALID_LABELS},
            "edges": [],
        }

        # For each potential edge in biclique
        for i, dmr in enumerate(sorted(dmr_nodes)):
            for j, gene in enumerate(sorted(gene_nodes)):
                edge = (min(dmr, gene), max(dmr, gene))

                # Find classification for this edge
                edge_info = None
                for label in EdgeInfo.VALID_LABELS:
                    matching = [e for e in edge_classification[label] if e.edge == edge]
                    if matching:
                        edge_info = matching[0]
                        biclique_data["edge_counts"][label] += 1
                        break

                if edge_info:
                    biclique_data["edges"].append(
                        {
                            "source": dmr,
                            "target": gene,
                            "label": edge_info.label,
                            "sources": list(edge_info.sources),
                            "dmr_index": i,
                            "gene_index": j,
                        }
                    )

        result.append(biclique_data)

    return result
