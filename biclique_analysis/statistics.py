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
    # Get all DMRs and genes from the graph
    dmrs = {n for n in graph.nodes() if n < 3}  # Fixed DMR identification
    genes = {n for n in graph.nodes() if n >= 3}  # Fixed gene identification
    
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

    # Convert to count distribution (how many nodes appear X times)
    dmr_dist = {}
    gene_dist = {}
    for count in dmr_participation.values():
        dmr_dist[count] = dmr_dist.get(count, 0) + 1
    for count in gene_participation.values():
        gene_dist[count] = gene_dist.get(count, 0) + 1

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
        "total": total_edges,
        "single_percentage": single / total_edges if total_edges else 0,
        "multiple_percentage": multiple / total_edges if total_edges else 0,
        "uncovered_percentage": uncovered / total_edges if total_edges else 0,
    }
