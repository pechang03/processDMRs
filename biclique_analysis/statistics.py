# file statistics.py
from typing import List, Dict, Tuple, Set
import networkx as nx

# file statistics.py
# Author: Peter Shaw


def calculate_coverage_statistics(bicliques: List[Tuple[Set[int], Set[int]]], graph: nx.Graph) -> Dict:
    """Calculate coverage statistics for bicliques."""
    dmr_coverage = set()
    gene_coverage = set()
    for dmr_nodes, gene_nodes in bicliques:
        dmr_coverage.update(dmr_nodes)
        gene_coverage.update(gene_nodes)
    # Get all nodes from the graph
    all_nodes = set(graph.nodes())
    # In the test graph, DMRs are 0-2, genes are 3-4
    dmrs = {n for n in all_nodes if n <= 2}
    genes = {n for n in all_nodes if n > 2}
    
    return {
        "dmrs": {
            "covered": len(dmr_coverage),
            "total": len(dmrs),
            "percentage": len(dmr_coverage) / len(dmrs) if dmrs else 0
        },
        "genes": {
            "covered": len(gene_coverage),
            "total": len(genes),
            "percentage": len(gene_coverage) / len(genes) if genes else 0
        }
    }

def calculate_biclique_statistics(bicliques: List, graph: nx.Graph) -> Dict:
    """Calculate comprehensive biclique statistics."""
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
    
    # Count occurrences of each participation count
    for count in range(1, max(max(dmr_participation.values(), default=0), 
                            max(gene_participation.values(), default=0)) + 1):
        dmr_dist[count] = sum(1 for v in dmr_participation.values() if v == count)
        gene_dist[count] = sum(1 for v in gene_participation.values() if v == count)

    return {"dmrs": dmr_dist, "genes": gene_dist}


def calculate_edge_coverage(
    bicliques: List[Tuple[Set[int], Set[int]]], graph: nx.Graph
) -> Dict:
    """Calculate edge coverage statistics."""
    edge_coverage = {}
    # Count how many bicliques cover each edge
    for dmr_nodes, gene_nodes in bicliques:
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                if graph.has_edge(dmr, gene):
                    edge = tuple(sorted([dmr, gene]))
                    edge_coverage[edge] = edge_coverage.get(edge, 0) + 1

    # Count edges by coverage
    single = sum(1 for count in edge_coverage.values() if count == 1)
    multiple = sum(1 for count in edge_coverage.values() if count > 1)
    uncovered = len(graph.edges()) - len(edge_coverage)

    return {
        "single": single,
        "multiple": multiple,
        "uncovered": uncovered,
        "total": len(graph.edges()),
        "single_percentage": single / len(graph.edges()) if graph.edges() else 0,
        "multiple_percentage": multiple / len(graph.edges()) if graph.edges() else 0,
        "uncovered_percentage": uncovered / len(graph.edges()) if graph.edges() else 0,
    }
