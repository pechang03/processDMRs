# File reader.py
# Author: Peter Shaw

from typing import Dict, List, Union, Tuple, Set
import networkx as nx


def read_bicliques_file(
    filename: str, max_DMR_id: int, original_graph: nx.Graph
) -> Dict:
    """Read and process bicliques from a .biclusters file for any bipartite graph."""
    print("\nReading bicliques file:")
    print(f"Expected DMR range: 0 to {max_DMR_id-1}")

    with open(filename, "r") as f:
        lines = f.readlines()

    # Process file contents
    statistics = parse_header_statistics(lines)
    bicliques, line_idx = parse_bicliques(lines, max_DMR_id)
    
    # Calculate coverage information
    coverage_info = calculate_coverage(bicliques, original_graph)
    edge_distribution = calculate_edge_distribution(bicliques, original_graph)
    
    # Build and return result
    return create_result_dict(
        filename, bicliques, statistics, original_graph,
        coverage_info, edge_distribution
    )

def parse_header_statistics(lines: List[str]) -> Dict:
    """Parse header statistics from file lines."""
    statistics = {}
    line_idx = 0
    while line_idx < len(lines):
        line = lines[line_idx].strip()
        if not line or line.startswith("#"):
            line_idx += 1
            continue
        
        if line.startswith("- "):
            line = line[2:]
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                statistics[key] = (
                    int(value.strip())
                    if key in ["Nb operations", "Nb splits", "Nb deletions", "Nb additions"]
                    else value.strip()
                )
            line_idx += 1
            continue
        break
    return statistics

def parse_bicliques(lines: List[str], max_DMR_id: int) -> Tuple[List[Tuple[Set[int], Set[int]]], int]:
    """Parse bicliques from file lines."""
    bicliques = []
    line_idx = 0
    
    # Skip to first biclique
    while line_idx < len(lines) and (not lines[line_idx].strip() or 
          lines[line_idx].strip().startswith(("#", "- "))):
        line_idx += 1
    
    # Parse bicliques
    while line_idx < len(lines):
        line = lines[line_idx].strip()
        if not line:
            line_idx += 1
            continue
            
        nodes = [int(x) for x in line.split()]
        dmr_nodes = {n for n in nodes if n < max_DMR_id}
        gene_nodes = {n for n in nodes if n >= max_DMR_id}
        bicliques.append((dmr_nodes, gene_nodes))
        line_idx += 1
        
    return bicliques, line_idx

def calculate_coverage(
    bicliques: List[Tuple[Set[int], Set[int]]], 
    original_graph: nx.Graph
) -> Dict:
    """Calculate coverage statistics."""
    dmr_coverage = set()
    gene_coverage = set()
    
    for dmr_nodes, gene_nodes in bicliques:
        dmr_coverage.update(dmr_nodes)
        gene_coverage.update(gene_nodes)
    
    dmr_nodes = {n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 0}
    gene_nodes = {n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 1}
    
    return {
        "dmrs": {
            "covered": len(dmr_coverage),
            "total": len(dmr_nodes),
            "percentage": len(dmr_coverage) / len(dmr_nodes),
        },
        "genes": {
            "covered": len(gene_coverage),
            "total": len(gene_nodes),
            "percentage": len(gene_coverage) / len(gene_nodes),
        }
    }

def calculate_edge_distribution(
    bicliques: List[Tuple[Set[int], Set[int]]], 
    original_graph: nx.Graph
) -> Dict:
    """Calculate edge distribution across bicliques."""
    edge_distribution = {}
    
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                edge = (dmr, gene)
                if original_graph.has_edge(dmr, gene):
                    if edge not in edge_distribution:
                        edge_distribution[edge] = []
                    edge_distribution[edge].append(biclique_idx)
    
    return edge_distribution

def create_result_dict(
    filename: str,
    bicliques: List[Tuple[Set[int], Set[int]]],
    statistics: Dict,
    original_graph: nx.Graph,
    coverage_info: Dict,
    edge_distribution: Dict
) -> Dict:
    """Create the final result dictionary."""
    dmr_nodes = {n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 0}
    gene_nodes = {n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 1}
    
    uncovered_edges = set(original_graph.edges()) - set(edge_distribution.keys())
    uncovered_nodes = {node for edge in uncovered_edges for node in edge}
    
    coverage_info["edges"] = {
        "single_coverage": len([e for e, b in edge_distribution.items() if len(b) == 1]),
        "multiple_coverage": len([e for e, b in edge_distribution.items() if len(b) > 1]),
        "uncovered": len(uncovered_edges),
        "total": len(original_graph.edges()),
    }
    
    return {
        "bicliques": bicliques,
        "statistics": statistics,
        "graph_info": {
            "name": filename.split("/")[-1].split(".")[0],
            "total_dmrs": len(dmr_nodes),
            "total_genes": len(gene_nodes),
            "total_edges": len(original_graph.edges()),
        },
        "coverage": coverage_info,
        "debug": {
            "uncovered_edges": list(uncovered_edges)[:5],
            "uncovered_nodes": len(uncovered_nodes),
            "edge_distribution": edge_distribution,
            "header_stats": {
                "Nb operations": statistics.get("Nb operations", 0),
                "Nb splits": statistics.get("Nb splits", 0),
                "Nb deletions": statistics.get("Nb deletions", 0),
                "Nb additions": statistics.get("Nb additions", 0),
            },
        },
    }


def _parse_bicliques(
    lines: List[str], max_DMR_id: int
) -> List[Tuple[Set[int], Set[int]]]:
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


def _calculate_coverage(
    bicliques: List[Tuple[Set[int], Set[int]]], original_graph: nx.Graph
) -> Dict:
    """Calculate coverage statistics."""
    dmr_coverage = set()
    gene_coverage = set()
    covered_edges = {}  # Initialize covered_edges dictionary
    edge_coverage = {
        "single": 0,
        "multiple": 0,
        "uncovered": 0,
        "total": original_graph.number_of_edges(),
    }  # Initialize edge_coverage dictionary

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
            edge_coverage["single"] += 1
        else:
            edge_coverage["multiple"] += 1

    edge_coverage["uncovered"] = edge_coverage["total"] - len(covered_edges)

    # Calculate percentages
    edge_coverage["single_percentage"] = (
        edge_coverage["single"] / edge_coverage["total"]
    )
    edge_coverage["multiple_percentage"] = (
        edge_coverage["multiple"] / edge_coverage["total"]
    )
    edge_coverage["uncovered_percentage"] = (
        edge_coverage["uncovered"] / edge_coverage["total"]
    )

    return {
        "dmrs": {
            "covered": len(dmr_coverage),
            "total": len(
                [n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 0]
            ),
            "percentage": len(dmr_coverage) / original_graph.number_of_nodes(),
        },
        "genes": {
            "covered": len(gene_coverage),
            "total": len(
                [n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 1]
            ),
            "percentage": len(gene_coverage) / original_graph.number_of_nodes(),
        },
        "edges": edge_coverage,  # Add edge coverage information
    }


def _track_edge_distribution(
    bicliques: List[Tuple[Set[int], Set[int]]], original_graph: nx.Graph
) -> Dict:
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
