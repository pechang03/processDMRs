# File reader.py
# Author: Peter Shaw

from typing import Dict, List, Union, Tuple, Set
import networkx as nx

def read_bicliques_file(
    filename: str, max_DMR_id: int, original_graph: nx.Graph
) -> Dict:
    """Read and process bicliques from a .biclusters file."""
    statistics = {}
    bicliques = []
    dmr_coverage = set()
    gene_coverage = set()
    edge_coverage = {'single': 0, 'multiple': 0, 'uncovered': 0, 'total': original_graph.number_of_edges()}
    covered_edges = {}

    with open(filename, "r") as f:
        lines = f.readlines()
        statistics = _parse_header_statistics(lines)
        bicliques = _parse_bicliques(lines, max_DMR_id)

    coverage_stats = _calculate_coverage(bicliques, original_graph)
    edge_distribution = _track_edge_distribution(bicliques, original_graph)

    # Add graph info
    graph_info = {
        "name": filename.split("/")[-1].split(".")[0],  # Extract name from filename
        "total_dmrs": len([n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 0]),
        "total_genes": len([n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 1]),
        "total_edges": original_graph.number_of_edges()
    }

    return {
        "bicliques": bicliques,
        "statistics": statistics,
        "coverage": coverage_stats,
        "edge_distribution": edge_distribution,
        "graph_info": graph_info,  # Add graph info to return dict
        "debug": {
            "header_stats": statistics,
            "edge_distribution": edge_distribution,
            "uncovered_edges": [],  # Add placeholder for uncovered edges
            "uncovered_nodes": 0    # Add placeholder for uncovered nodes count
        }
    }

def _parse_bicliques(lines: List[str], max_DMR_id: int) -> List[Tuple[Set[int], Set[int]]]:
    """Parse bicliques from file lines."""
    bicliques = []
    current_biclique = None
    for line in lines:
        if line.startswith("Biclique"):
            if current_biclique:
                bicliques.append(current_biclique)
            current_biclique = (set(), set())
        elif line.startswith("DMR"):
            dmr_id = int(line.split(":")[1].strip())
            if dmr_id < max_DMR_id:
                current_biclique[0].add(dmr_id)
        elif line.startswith("Gene"):
            gene_id = int(line.split(":")[1].strip())
            current_biclique[1].add(gene_id)
    if current_biclique:
        bicliques.append(current_biclique)
    return bicliques

def _calculate_coverage(bicliques: List[Tuple[Set[int], Set[int]]], original_graph: nx.Graph) -> Dict:
    """Calculate coverage statistics."""
    dmr_coverage = set()
    gene_coverage = set()
    covered_edges = {}  # Initialize covered_edges dictionary
    edge_coverage = {'single': 0, 'multiple': 0, 'uncovered': 0, 'total': original_graph.number_of_edges()}  # Initialize edge_coverage dictionary

    for dmr_nodes, gene_nodes in bicliques:
        dmr_coverage.update(dmr_nodes)
        gene_coverage.update(gene_nodes)
        
        # Track edge coverage
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                if original_graph.has_edge(dmr, gene):
                    edge = tuple(sorted([dmr, gene]))
                    covered_edges[edge] = covered_edges.get(edge, 0) + 1
    # Calculate edge coverage statistics
    for edge_count in covered_edges.values():
        if edge_count == 1:
            edge_coverage['single'] += 1
        else:
            edge_coverage['multiple'] += 1
    
    edge_coverage['uncovered'] = edge_coverage['total'] - len(covered_edges)
    
    # Calculate percentages
    edge_coverage['single_percentage'] = edge_coverage['single'] / edge_coverage['total']
    edge_coverage['multiple_percentage'] = edge_coverage['multiple'] / edge_coverage['total']
    edge_coverage['uncovered_percentage'] = edge_coverage['uncovered'] / edge_coverage['total']

    return {
        "dmrs": {
            "covered": len(dmr_coverage),
            "total": len([n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 0]),
            "percentage": len(dmr_coverage) / original_graph.number_of_nodes()
        },
        "genes": {
            "covered": len(gene_coverage),
            "total": len([n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 1]),
            "percentage": len(gene_coverage) / original_graph.number_of_nodes()
        },
        "edges": edge_coverage  # Add edge coverage information
    }

def _track_edge_distribution(bicliques: List[Tuple[Set[int], Set[int]]], original_graph: nx.Graph) -> Dict:
    """Track edge distribution across bicliques."""
    edge_distribution = {}
    for dmr_nodes, gene_nodes in bicliques:
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                edge = (dmr, gene)
                if edge in edge_distribution:
                    edge_distribution[edge] += 1
                else:
                    edge_distribution[edge] = 1
    return edge_distribution


def _parse_header_statistics(lines: List[str]) -> Dict:
    """Parse header statistics from file lines."""
    statistics = {}
    for line in lines:
        if not line.startswith("- "):
            continue
        line = line[2:]
        if ":" in line:
            key, value = line.split(":", 1)
            statistics[key.strip()] = _convert_statistic_value(
                key.strip(), value.strip()
            )
    return statistics


def _convert_statistic_value(key: str, value: str) -> Union[int, str]:
    """Convert statistic value to appropriate type."""
    if key in ["Nb operations", "Nb splits", "Nb deletions", "Nb additions"]:
        return int(value)
    return value


# Add other helper functions...
