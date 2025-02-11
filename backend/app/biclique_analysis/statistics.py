# file statistics.py
import warnings
from typing import List, Dict, Tuple, Set
import networkx as nx
import json
from backend.app.biclique_analysis.classifier import (
    classify_biclique,
    classify_biclique_types,
)


def analyze_components(components: List[Set[int]], graph: nx.Graph) -> Dict[str, float]:
    """
    Analyze graph components and calculate statistics.

    Args:
        components: List of sets of node IDs representing components
        graph: NetworkX graph containing the components

    Returns:
        Dictionary containing:
            - total: Total number of components
            - single_node: Number of single-node components
            - small: Number of components with ≤2 nodes or ≤1 DMR/gene
            - interesting: Number of components with >2 nodes and ≥2 DMR/gene
            - complex: Number of components with multiple interesting bicliques
            - avg_dmrs: Average number of DMRs in interesting components
            - avg_genes: Average number of genes in interesting components
    """
    interesting_comps = []
    single_node = 0
    small = 0
    complex = 0  # Add complex counter

    for comp in components:
        dmrs = {n for n in comp if graph.nodes[n].get("bipartite") == 0}
        genes = {n for n in comp if graph.nodes[n].get("bipartite") == 1}

        if len(comp) == 1:
            single_node += 1
        elif len(dmrs) <= 1 or len(genes) <= 1:
            small += 1
        else:
            # Check if component is complex (has multiple interesting bicliques)
            from .classifier import classify_component, BicliqueSizeCategory

            category = classify_component(dmrs, genes, [(dmrs, genes)])
            if category == BicliqueSizeCategory.COMPLEX:
                complex += 1
            else:
                interesting_comps.append((comp, dmrs, genes))

    interesting = len(interesting_comps)

    # Calculate averages for interesting components
    total_dmrs = sum(len(dmrs) for _, dmrs, _ in interesting_comps)
    total_genes = sum(len(genes) for _, _, genes in interesting_comps)

    return {
        "total": len(components),
        "single_node": single_node,
        "small": small,
        "interesting": interesting,
        "complex": complex,  # Add complex count
        "avg_dmrs": total_dmrs / interesting if interesting else 0,
        "avg_genes": total_genes / interesting if interesting else 0,
    }


class InvalidGraphError(Exception):
    """Exception raised for invalid graph structures."""

    pass


def validate_graph(
    graph: nx.Graph, remove_isolates: bool = True
) -> Tuple[Set[int], Set[int]]:
    """
    Validate graph structure and return DMR and gene node sets.
    Checks:
    - Graph has nodes
    - Both partite sets non-empty
    - Split genes have degree > 2 in both graphs

    Args:
        graph: NetworkX graph to validate
        remove_isolates: If True, removes isolated gene nodes before validation

    Returns:
        Tuple of (dmr_nodes, gene_nodes)

    Raises:
        InvalidGraphError: If graph structure is invalid
    """
    if not graph.nodes():
        raise InvalidGraphError("Graph contains no nodes")

    # Get partite sets based on bipartite attribute
    all_nodes = set(graph.nodes())
    dmr_nodes = {n for n, d in graph.nodes(data=True) if d.get("bipartite") == 0}
    gene_nodes = {n for n, d in graph.nodes(data=True) if d.get("bipartite") == 1}

    # Check for empty partite sets
    if not dmr_nodes:
        raise InvalidGraphError("Graph contains no DMR nodes")
    if not gene_nodes:
        raise InvalidGraphError("Graph contains no gene nodes")

    # Handle isolated nodes
    if remove_isolates:
        # Find isolated gene nodes
        isolated_genes = [n for n in gene_nodes if graph.degree(n) == 0]
        if isolated_genes:
            print(f"Found {len(isolated_genes)} isolated gene nodes - removing them")
            gene_nodes = gene_nodes - set(isolated_genes)
            # Don't raise error for isolated nodes since we're handling them

    # Validate split genes have sufficient degree
    split_genes = {n for n in gene_nodes if graph.degree(n) > 2}
    for gene in split_genes:
        if graph.degree(gene) <= 2:
            raise InvalidGraphError(
                f"Split gene {gene} has insufficient degree ({graph.degree(gene)})"
            )

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
            "participation": {
                k: v for k, v in sorted(Counter(dmr_participation.values()).items())
            },
        },
        "genes": {
            "covered": len(gene_coverage),
            "total": len(genes),
            "percentage": len(gene_coverage) / len(genes) if genes else 0,
            "participation": {
                k: v for k, v in sorted(Counter(gene_participation.values()).items())
            },
        },
        "edges": {
            "single_coverage": len(single_covered),
            "multiple_coverage": len(multiple_covered),
            "uncovered": total_edges - len(covered_edges),
            "total": total_edges,
            "single_percentage": len(single_covered) / total_edges
            if total_edges
            else 0,
            "multiple_percentage": len(multiple_covered) / total_edges
            if total_edges
            else 0,
            "uncovered_percentage": (total_edges - len(covered_edges)) / total_edges
            if total_edges
            else 0,
        },
        "size_distribution": size_distribution,
    }


def analyze_biconnected_components_depricated(
    graph: nx.Graph,
) -> Tuple[List[Set], Dict]:
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
        dmrs = {n for n in comp if graph.nodes[n].get("bipartite") == 0}
        genes = {n for n in comp if graph.nodes[n].get("bipartite") == 1}

        if len(comp) == 1:
            single_node += 1
        elif len(dmrs) <= 1 or len(genes) <= 1:
            small += 1
        else:
            interesting += 1
            interesting_comps.append((comp, dmrs, genes))
            total_dmrs += len(dmrs)
            total_genes += len(genes)

    stats = {
        "total": len(biconn_comps),
        "single_node": single_node,
        "small": small,
        "interesting": interesting,
        "avg_dmrs": total_dmrs / interesting if interesting else 0,
        "avg_genes": total_genes / interesting if interesting else 0,
    }

    return biconn_comps, stats  # Return both components and stats


def calculate_dominating_set_statistics(
    graph: nx.Graph, dominating_set: Set[int]
) -> Dict:
    """Calculate statistics about the dominating set."""
    dmr_nodes = {n for n, d in graph.nodes(data=True) if d["bipartite"] == 0}
    gene_nodes = {n for n, d in graph.nodes(data=True) if d["bipartite"] == 1}

    # Calculate dominated genes
    dominated_genes = set()
    for dmr in dominating_set:
        dominated_genes.update(graph.neighbors(dmr))

    return {
        "size": len(dominating_set),
        "percentage": len(dominating_set) / len(dmr_nodes) if dmr_nodes else 0,
        "genes_dominated": len(dominated_genes),
        "genes_dominated_percentage": len(dominated_genes) / len(gene_nodes)
        if gene_nodes
        else 0,
    }


def calculate_biclique_statistics(
    bicliques: List[Tuple[Set[int], Set[int]]],
    graph: nx.Graph,
    dominating_set: Set[int] = None,
) -> Dict:
    """Calculate comprehensive biclique statistics."""
    # Validate graph structure first and get cleaned node sets
    dmr_nodes, gene_nodes = validate_graph(graph, remove_isolates=True)

    # Calculate node participation first
    node_participation = calculate_node_participation(bicliques)

    # Calculate edge coverage
    edge_coverage = calculate_edge_coverage(bicliques, graph)

    # Calculate size distribution
    size_dist = calculate_size_distribution(bicliques)

    # Calculate coverage statistics using cleaned node sets
    coverage_stats = calculate_coverage_statistics(bicliques, graph)

    # Calculate component statistics
    component_stats = calculate_component_statistics(bicliques, graph)

    # Combine all statistics
    stats = {
        "size_distribution": size_dist,
        "coverage": coverage_stats,
        "node_participation": node_participation,
        "edge_coverage": edge_coverage,
        "components": component_stats,
        "dominating_set": calculate_dominating_set_statistics(graph, dominating_set)
        if dominating_set
        else {},
        "biclique_types": classify_biclique_types(bicliques),
    }

    return stats


def calculate_size_distribution(bicliques: List) -> Dict:
    """Calculate size distribution of bicliques."""
    distribution = {}
    for dmr_nodes, gene_nodes in bicliques:
        key = (len(dmr_nodes), len(gene_nodes))  # Use tuple key
        distribution[key] = distribution.get(key, 0) + 1
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

    # Count nodes by their participation frequency
    for count in sorted(set(dmr_participation.values())):
        dmr_dist[count] = sum(1 for v in dmr_participation.values() if v == count)
    for count in sorted(set(gene_participation.values())):
        gene_dist[count] = sum(1 for v in gene_participation.values() if v == count)

    return {"dmrs": dmr_dist, "genes": gene_dist}


def calculate_edge_coverage(
    bicliques: List[Tuple[Set[int], Set[int]]], graph: nx.Graph
) -> Dict:
    """Calculate edge coverage statistics."""
    print("\nCalculating edge coverage...")
    print(f"Number of bicliques: {len(bicliques)}")
    print(f"Number of edges in graph: {len(graph.edges())}")

    # Track coverage for each edge
    edge_coverage = {}

    # Count how many bicliques cover each edge
    for dmr_nodes, gene_nodes in bicliques:
        # Create edges for each DMR-gene pair in the biclique
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                # Try both orderings of the edge
                edge1 = tuple(sorted([dmr, gene]))
                edge2 = tuple(sorted([gene, dmr]))

                # Check if either ordering exists in the graph
                if graph.has_edge(dmr, gene) or graph.has_edge(gene, dmr):
                    edge = edge1  # Use consistent ordering
                    edge_coverage[edge] = edge_coverage.get(edge, 0) + 1

    # Calculate coverage statistics
    total_edges = len(graph.edges())
    covered_edges = set(edge_coverage.keys())
    single_covered = {e for e in covered_edges if edge_coverage[e] == 1}
    multiple_covered = {e for e in covered_edges if edge_coverage[e] > 1}
    uncovered = set(map(tuple, map(sorted, graph.edges()))) - covered_edges

    # Debug output
    print(f"\nEdge coverage details:")
    print(f"Total edges in graph: {total_edges}")
    print(f"Single covered edges: {len(single_covered)}")
    print(f"Multiple covered edges: {len(multiple_covered)}")
    print(f"Uncovered edges: {len(uncovered)}")

    # If all edges are uncovered, print some debug info
    if len(uncovered) == total_edges:
        print("\nWARNING: All edges uncovered! Debug info:")
        print(
            f"First biclique DMRs: {list(next(iter(bicliques))[0]) if bicliques else []}"
        )
        print(
            f"First biclique genes: {list(next(iter(bicliques))[1]) if bicliques else []}"
        )
        print("First few graph edges:", list(graph.edges())[:5])

    return {
        "single_coverage": len(single_covered),
        "multiple_coverage": len(multiple_covered),
        "uncovered": len(uncovered),
        "total": total_edges,
        "single_percentage": len(single_covered) / total_edges if total_edges else 0,
        "multiple_percentage": len(multiple_covered) / total_edges
        if total_edges
        else 0,
        "uncovered_percentage": len(uncovered) / total_edges if total_edges else 0,
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
        biclique_graph.add_edges_from(
            (dmr, gene) for dmr in dmr_nodes for gene in gene_nodes
        )

    # Get connected components from biclique graph
    biclique_connected_components = list(nx.connected_components(biclique_graph))
    biclique_connected_stats = analyze_components(
        biclique_connected_components, biclique_graph
    )

    biclique_biconn_components = list(nx.biconnected_components(biclique_graph))
    biclique_biconn_stats = analyze_components(
        biclique_biconn_components, biclique_graph
    )

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
