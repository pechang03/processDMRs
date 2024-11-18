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


from collections import Counter

def calculate_coverage_statistics(
    bicliques: List[Tuple[Set[int], Set[int]]], graph: nx.Graph
) -> Dict:
    """Calculate coverage statistics for bicliques."""
    # Validate graph structure first
    dmrs, genes = validate_graph(graph)

    # Initialize coverage sets
    dmr_coverage = set()
    gene_coverage = set()

    # Track participation counts
    dmr_participation = {}
    gene_participation = {}

    # Process each biclique
    for dmr_nodes, gene_nodes in bicliques:
        # Update coverage
        dmr_coverage.update(dmr_nodes)
        gene_coverage.update(gene_nodes)

        # Update participation counts
        for dmr in dmr_nodes:
            dmr_participation[dmr] = dmr_participation.get(dmr, 0) + 1
        for gene in gene_nodes:
            gene_participation[gene] = gene_participation.get(gene, 0) + 1

    # Calculate edge coverage
    covered_edges = set()
    multiple_covered = set()
    for dmr_nodes, gene_nodes in bicliques:
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                edge = (min(dmr, gene), max(dmr, gene))
                if edge in covered_edges:
                    multiple_covered.add(edge)
                covered_edges.add(edge)

    total_edges = len(graph.edges())
    single_covered = covered_edges - multiple_covered

    size_distribution = calculate_size_distribution(bicliques)
    return {
        "dmrs": {
            "covered": len(dmr_coverage),
            "total": len(dmrs),
            "percentage": len(dmr_coverage) / len(dmrs) if dmrs else 0,
            "participation": {k: v for k, v in sorted(Counter(dmr_participation.values()).items())}
        },
        "genes": {
            "covered": len(gene_coverage),
            "total": len(genes),
            "percentage": len(gene_coverage) / len(genes) if genes else 0,
            "participation": {k: v for k, v in sorted(Counter(gene_participation.values()).items())}
        },
        "edges": {
            "single_coverage": len(single_covered),
            "multiple_coverage": len(multiple_covered),
            "uncovered": total_edges - len(covered_edges),
            "total": total_edges,
            "single_percentage": len(single_covered) / total_edges if total_edges else 0,
            "multiple_percentage": len(multiple_covered) / total_edges if total_edges else 0,
            "uncovered_percentage": (total_edges - len(covered_edges)) / total_edges if total_edges else 0
        },
        "size_distribution": size_distribution
    }


def analyze_biconnected_components(graph: nx.Graph) -> Dict:
    """Analyze biconnected components of a graph."""
    # Get biconnected components
    biconn_comps = list(nx.biconnected_components(graph))
    
    # Initialize counters
    single_node = 0
    small = 0
    interesting = 0
    total_dmrs = 0
    total_genes = 0
    
    interesting_comps = []
    
    for comp in biconn_comps:
        dmrs = {n for n in comp if graph.nodes[n].get('bipartite') == 0}
        genes = {n for n in comp if graph.nodes[n].get('bipartite') == 1}
        
        if len(comp) == 1:
            single_node += 1
        elif len(dmrs) <= 1 or len(genes) <= 1:
            small += 1
        else:
            interesting += 1
            interesting_comps.append((comp, dmrs, genes))
            total_dmrs += len(dmrs)
            total_genes += len(genes)
    
    return {
        "total": len(biconn_comps),
        "single_node": single_node,
        "small": small,
        "interesting": interesting,
        "avg_dmrs": total_dmrs / interesting if interesting else 0,
        "avg_genes": total_genes / interesting if interesting else 0
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
        "components": calculate_component_statistics(bicliques, graph),  # Add this line
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

    # Initialize with 0 for all possible counts
    max_dmr_count = max(dmr_participation.values()) if dmr_participation else 0
    max_gene_count = max(gene_participation.values()) if gene_participation else 0
    # Count nodes by their participation frequency
    for count in set(dmr_participation.values()):
        dmr_dist[count] = sum(1 for v in dmr_participation.values() if v == count)
    for count in set(gene_participation.values()):
        gene_dist[count] = sum(1 for v in gene_participation.values() if v == count)

    # for i in range(1, max(max_dmr_count, max_gene_count) + 1):
    # dmr_dist[i] = sum(1 for count in dmr_participation.values() if count == i)
    # gene_dist[i] = sum(1 for count in gene_participation.values() if count == i)

    return {"dmrs": dmr_dist, "genes": gene_dist}


def calculate_edge_coverage(
    bicliques: List[Tuple[Set[int], Set[int]]], graph: nx.Graph
) -> Dict:
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
        "uncovered_percentage": uncovered / total_edges if total_edges > 0 else 0,
    }

def calculate_component_statistics(bicliques: List, graph: nx.Graph) -> Dict:
    """Calculate statistics about components in both original and biclique graphs."""
    # Get connected components from original graph
    original_connected_components = list(nx.connected_components(graph))
    original_connected_stats = analyze_components(original_connected_components, graph)
    
    original_biconn_components = list(nx.biconnected_components(graph))
    original_biconn_stats = analyze_components(original_biconn_components, graph)
    
    # Create biclique graph
    biclique_graph = nx.Graph()
    for dmr_nodes, gene_nodes in bicliques:
        biclique_graph.add_nodes_from(dmr_nodes, bipartite=0)
        biclique_graph.add_nodes_from(gene_nodes, bipartite=1)
        biclique_graph.add_edges_from((dmr, gene) for dmr in dmr_nodes for gene in gene_nodes)

    # Get connected components from biclique graph
    biclique_connected_components = list(nx.connected_components(biclique_graph))
    biclique_connected_stats = analyze_components(biclique_connected_components, biclique_graph)
    
    biclique_biconn_components = list(nx.biconnected_components(biclique_graph))
    biclique_biconn_stats = analyze_components(biclique_biconn_components, biclique_graph)
    
    return {
        "original": {
            "connected": original_connected_stats,
            "biconnected": original_biconn_stats,
        },
        "biclique": {
            "connected": biclique_connected_stats,
            "biconnected": biclique_biconn_stats,
        },
    }
