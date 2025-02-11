# File : edge_classification.py
# Description : Edge classification module

from typing import Dict, List, Tuple, Set, Union, Any
from collections import defaultdict
import networkx as nx

from backend.app.utils.edge_info import EdgeInfo
from backend.app.biclique_analysis.classifier import BicliqueSizeCategory
from backend.app.utils.json_utils import convert_for_json


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
    # Add null checks
    if total_edges is None or permanent_edges is None or false_positives is None or false_negatives is None:
        return {
            "accuracy": 0.0,
            "noise_percentage": 0.0,
            "false_positive_rate": 0.0,
            "false_negative_rate": 0.0
        }
    
    # Total possible edges in the comparison
    total_compared = total_edges + false_negatives
    
    # Calculate error rates with null checks
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
    component: Dict = None
) -> Dict[str, Union[List[EdgeInfo], Dict[str, Any]]]:
    """Classify edges and calculate edge classification statistics."""
    
    # First validate node sets match
    original_nodes = set(original_graph.nodes())
    biclique_nodes = set(biclique_graph.nodes())
    
    # Ensure all biclique nodes are included in component
    if bicliques and component:
        for dmrs, genes in bicliques:
            component["component"].update(dmrs)
            component["component"].update(genes)
            component["dmrs"].update(dmrs)
            component["genes"].update(genes)

    # Explicitly mark edges from single-DMR bicliques
    if bicliques:
        for idx, (dmrs, genes) in enumerate(bicliques):
            if len(dmrs) == 1:  # Simple biclique
                dmr = next(iter(dmrs))
                for gene in genes:
                    edge = (min(dmr, gene), max(dmr, gene))
                    edge_sources.setdefault(edge, set()).add(f"simple_biclique_{idx}")
    
    if original_nodes != biclique_nodes:
        raise ValueError(
            f"Node mismatch: Original graph has {len(original_nodes)} nodes, "
            f"Biclique graph has {len(biclique_nodes)} nodes"
        )

    # Initialize classification containers
    classifications = {
        "permanent": [],
        "false_positive": [],
        "false_negative": []
    }

    # Track simple biclique edges
    simple_biclique_edges = set()
    if bicliques:
        for idx, (dmrs, genes) in enumerate(bicliques):
            if len(dmrs) == 1:  # Simple biclique
                dmr = next(iter(dmrs))
                for gene in genes:
                    edge = (dmr, gene) if dmr < gene else (gene, dmr)
                    simple_biclique_edges.add(edge)
                    edge_sources.setdefault(edge, set()).add(f"simple_biclique_{idx}")

    # Get all edges from both graphs
    original_edges = set(original_graph.edges())
    biclique_edges = set(biclique_graph.edges())

    # Classify each edge
    for u, v in original_edges:
        edge = (u, v) if u < v else (v, u)
        
        if edge in simple_biclique_edges:
            classifications["permanent"].append(
                EdgeInfo(edge=edge, sources=edge_sources[edge])
            )
        elif biclique_graph.has_edge(u, v):
            classifications["permanent"].append(
                EdgeInfo(edge=edge, sources=edge_sources.get(edge, set()))
            )
        else:
            classifications["false_positive"].append(
                EdgeInfo(edge=edge, sources=edge_sources.get(edge, set()))
            )

    # 3. Edges only in biclique graph are false negatives
    for u, v in biclique_edges - original_edges:
        edge = (min(u, v), max(u, v))
        classifications["false_negative"].append(EdgeInfo(edge, sources=set()))

    # Calculate component-wide statistics
    component_stats = calculate_edge_statistics(
        total_edges=len(original_edges),
        permanent_edges=len(classifications["permanent"]),
        false_positives=len(classifications["false_positive"]),
        false_negatives=len(classifications["false_negative"])
    )

    # Calculate per-biclique statistics if bicliques are provided
    biclique_stats = {
        "edge_counts": {},
        "reliability": {},
        "total_false_negatives": len(classifications["false_negative"])
    }

    if bicliques:
        for idx, (dmrs, genes) in enumerate(bicliques):
            biclique_edges = set()
            for dmr in dmrs:
                for gene in genes:
                    edge = (min(dmr, gene), max(dmr, gene))
                    biclique_edges.add(edge)

            stats = {
                "total_edges": len(biclique_edges),
                "permanent": sum(1 for e in classifications["permanent"] if e.edge in biclique_edges),
                "false_positives": sum(1 for e in classifications["false_positive"] if e.edge in biclique_edges),
                "false_negatives": sum(1 for e in classifications["false_negative"] if e.edge in biclique_edges)
            }
            
            biclique_stats["edge_counts"][idx] = stats
            biclique_stats["reliability"][idx] = calculate_edge_statistics(
                total_edges=stats["total_edges"],
                permanent_edges=stats["permanent"],
                false_positives=stats["false_positives"],
                false_negatives=stats["false_negatives"]
            )

    return {
        "classifications": classifications,
        "stats": {
            "component": convert_for_json(component_stats),
            "bicliques": convert_for_json(biclique_stats)
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
