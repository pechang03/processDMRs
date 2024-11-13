# file statistics.py
import warnings
from typing import List, Dict, Tuple, Set
import networkx as nx

class InvalidGraphError(Exception):
    """Exception raised for invalid graph structures."""
    pass

def validate_graph(graph: nx.Graph) -> Tuple[Set[int], Set[int]]:
    """
    Validate graph structure and return DMR and gene node sets.
    
    Args:
        graph: NetworkX graph to validate
        
    Returns:
        Tuple of (dmr_nodes, gene_nodes)
        
    Raises:
        InvalidGraphError: If graph structure is invalid
    """
    if not graph.nodes():
        raise InvalidGraphError("Graph contains no nodes")
        
    # Check for degree 0 nodes
    zero_degree_nodes = [n for n, d in graph.degree() if d == 0]
    if zero_degree_nodes:
        raise InvalidGraphError(f"Graph contains isolated nodes: {zero_degree_nodes}")
        
    # Check for multi-edges
    if any(len(graph[u][v]) > 1 for u, v in graph.edges()):
        raise InvalidGraphError("Graph contains multi-edges")
        
    # Identify DMR and gene nodes (DMRs are 0-2, genes are 3+)
    all_nodes = set(graph.nodes())
    dmr_nodes = {n for n in all_nodes if n <= 2}
    gene_nodes = {n for n in all_nodes if n > 2}
    
    # Check for empty partite sets
    if not dmr_nodes:
        raise InvalidGraphError("Graph contains no DMR nodes")
    if not gene_nodes:
        raise InvalidGraphError("Graph contains no gene nodes")
        
    return dmr_nodes, gene_nodes


def calculate_coverage_statistics(bicliques: List[Tuple[Set[int], Set[int]]], graph: nx.Graph) -> Dict:
    """Calculate coverage statistics for bicliques."""
    # Validate graph structure first
    dmrs, genes = validate_graph(graph)
    
    dmr_coverage = set()
    gene_coverage = set()
    for dmr_nodes, gene_nodes in bicliques:
        dmr_coverage.update(dmr_nodes)
        gene_coverage.update(gene_nodes)
    
    return {
        "dmrs": {
            "covered": len(dmr_coverage),
            "total": len(dmrs),
            "percentage": len(dmr_coverage) / len(dmrs)
        },
        "genes": {
            "covered": len(gene_coverage),
            "total": len(genes),
            "percentage": len(gene_coverage) / len(genes)
        }
    }

def calculate_biclique_statistics(bicliques: List, graph: nx.Graph) -> Dict:
    """Calculate comprehensive biclique statistics."""
    # Validate graph structure first
    validate_graph(graph)
    
    node_participation = calculate_node_participation(bicliques)
    edge_coverage = calculate_edge_coverage(bicliques, graph)
    return {
        "size_distribution": calculate_size_distribution(bicliques),
        "coverage": calculate_coverage_statistics(bicliques, graph),
        "node_participation": node_participation,
        "edge_coverage": edge_coverage,
    }


def calculate_size_distribution(bicliques: List) -> Dict:
    """Calculate size distribution of bicliques."""
    distribution = {}
    for dmr_nodes, gene_nodes in bicliques:
        size_key = (len(dmr_nodes), len(gene_nodes))
        distribution[size_key] = distribution.get(size_key, 0) + 1
    return distribution


def calculate_node_participation(bicliques: List[Tuple[Set[int], Set[int]]]) -> Dict:
    """Calculate how many nodes participate in multiple bicliques."""
    dmr_participation = {}
    gene_participation = {}

    # First count participation for each node
    for dmr_nodes, gene_nodes in bicliques:
        for node in dmr_nodes:
            dmr_participation[node] = dmr_participation.get(node, 0) + 1
        for node in gene_nodes:
            gene_participation[node] = gene_participation.get(node, 0) + 1

    # Convert to count distribution
    dmr_dist = {}
    gene_dist = {}
    
    # Count how many nodes appear exactly k times
    for k in set(dmr_participation.values()):
        dmr_dist[k] = sum(1 for count in dmr_participation.values() if count == k)
    for k in set(gene_participation.values()):
        gene_dist[k] = sum(1 for count in gene_participation.values() if count == k)

    return {"dmrs": dmr_dist, "genes": gene_dist}


def calculate_edge_coverage(bicliques: List[Tuple[Set[int], Set[int]]], graph: nx.Graph) -> Dict:
    """Calculate edge coverage statistics."""
    # Validate graph structure first
    validate_graph(graph)
    
    edge_coverage = {}
    # Count how many bicliques cover each edge
    for dmr_nodes, gene_nodes in bicliques:
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                if graph.has_edge(dmr, gene):  # Only count edges that exist in graph
                    edge = tuple(sorted([dmr, gene]))
                    edge_coverage[edge] = edge_coverage.get(edge, 0) + 1

    # Count edges by coverage
    single = sum(1 for count in edge_coverage.values() if count == 1)
    multiple = sum(1 for count in edge_coverage.values() if count > 1)
    covered_edges = set(edge_coverage.keys())
    uncovered = len(graph.edges()) - len(covered_edges)

    total_edges = len(graph.edges())
    return {
        "single": single,
        "multiple": multiple, 
        "uncovered": uncovered,
        "total": total_edges,
        "single_percentage": single / total_edges if total_edges > 0 else 0,
        "multiple_percentage": multiple / total_edges if total_edges > 0 else 0,
        "uncovered_percentage": uncovered / total_edges if total_edges > 0 else 0
    }

    return {
        "single": single,
        "multiple": multiple,
        "uncovered": uncovered,
        "total": len(graph.edges()),
        "single_percentage": single / len(graph.edges()),
        "multiple_percentage": multiple / len(graph.edges()),
        "uncovered_percentage": uncovered / len(graph.edges()),
    }
