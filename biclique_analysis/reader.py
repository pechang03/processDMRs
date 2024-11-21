# File reader.py
# Author: Peter Shaw

import os
from typing import Dict, List, Union, Tuple, Set
import networkx as nx


def read_bicliques_file(
    filename: str,
    max_DMR_id: int,
    original_graph: nx.Graph,
    gene_id_mapping: Dict[str, int] = None,  # Make optional
    file_format: str = "gene_name",  # Add format parameter, default to gene_name format
) -> Dict:
    """Read and process bicliques from a .biclusters file for any bipartite graph."""
    print(f"\nReading bicliques file: {filename}")
    print(f"Reading bicliques file in {file_format} format")
    print(f"Expected DMR range: 0 to {max_DMR_id-1}")

    # Validate input parameters
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Bicliques file not found: {filename}")

    try:
        with open(filename, "r") as f:
            lines = f.readlines()
    except IOError as e:
        print(f"Error reading bicliques file: {e}")
        return {"error": str(e), "bicliques": []}

    # Extensive logging for debugging
    print(f"Total lines in file: {len(lines)}")
    print("First 10 lines:")
    for line in lines[:10]:
        print(line.strip())

    # Process file contents
    try:
        statistics = parse_header_statistics(lines)
    except Exception as e:
        print(f"Error parsing header statistics: {e}")
        statistics = {}

    # Detailed gene mapping logging
    if gene_id_mapping:
        print("\nGene ID Mapping Debug:")
        print(f"Total genes in mapping: {len(gene_id_mapping)}")
        print("First 10 entries:")
        for gene, id in list(gene_id_mapping.items())[:10]:
            print(f"'{gene}': {id}")

        print("\nChecking for specific genes:")
        test_genes = ["oprk1", "sgk3", "xkr9", "col9a1"]
        for gene in test_genes:
            print(f"'{gene}' in mapping: {gene in gene_id_mapping}")

    # Parse bicliques with extensive error handling
    try:
        bicliques, line_idx = parse_bicliques(
            lines, max_DMR_id, gene_id_mapping, file_format=file_format
        )
        
        # Detailed biclique logging
        print("\nBiclique Parsing Results:")
        print(f"Total bicliques found: {len(bicliques)}")
        print("First 5 bicliques:")
        for i, (dmrs, genes) in enumerate(bicliques[:5], 1):
            print(f"Biclique {i}: {len(dmrs)} DMRs, {len(genes)} genes")
            print(f"  DMRs: {sorted(dmrs)}")
            print(f"  Genes: {sorted(genes)}")

    except Exception as e:
        print(f"Error parsing bicliques: {e}")
        bicliques = []
        line_idx = 0

    # Calculate coverage information
    try:
        coverage_info = calculate_coverage(bicliques, original_graph)
        edge_distribution = calculate_edge_distribution(bicliques, original_graph)
    except Exception as e:
        print(f"Error calculating coverage: {e}")
        coverage_info = {}
        edge_distribution = {}

    # Build and return result
    result = create_result_dict(
        filename,
        bicliques,
        statistics,
        original_graph,
        coverage_info,
        edge_distribution,
    )

    # Final validation and logging
    print("\nFinal Bicliques Result:")
    print(f"Total bicliques: {len(result.get('bicliques', []))}")
    print("Result keys:", list(result.keys()))

    return result


def parse_header_statistics(lines: List[str]) -> Dict:
    """Parse header statistics from file lines."""
    statistics = {
        "size_distribution": {},
        "coverage": {
            "dmrs": {"covered": 0, "total": 0, "percentage": 0},
            "genes": {"covered": 0, "total": 0, "percentage": 0},
        },
        "node_participation": {"dmrs": {}, "genes": {}},
        "edge_coverage": {"single": 0, "multiple": 0, "uncovered": 0},
    }

    line_idx = 0
    section = None

    while line_idx < len(lines):
        line = lines[line_idx].strip()

        if not line:
            line_idx += 1
            continue

        if line == "Biclique Size Distribution":
            section = "size_dist"
            line_idx += 2  # Skip header row
            continue

        if line == "Coverage Statistics":
            section = "coverage"
            line_idx += 1
            continue

        if line == "Node Participation":
            section = "participation"
            line_idx += 1
            continue

        if line == "Edge Coverage":
            section = "edge"
            line_idx += 1
            continue

        if section == "size_dist":
            if line.startswith("DMRs"):
                line_idx += 1
                continue
            parts = line.split()
            if (
                len(parts) == 3
            ):  # this is related to the file structure and not if a component is interesting
                statistics["size_distribution"][(int(parts[0]), int(parts[1]))] = int(
                    parts[2]
                )

        elif section == "coverage":
            if line.startswith("DMR Coverage"):
                line_idx += 1
                coverage_line = lines[line_idx].strip()
                if coverage_line.startswith("Covered:"):
                    parts = coverage_line.split()
                    covered, total = map(int, parts[1].split("/"))
                    percentage = float(parts[2].strip("()%")) / 100
                    statistics["coverage"]["dmrs"] = {
                        "covered": covered,
                        "total": total,
                        "percentage": percentage,
                    }
            elif line.startswith("Gene Coverage"):
                line_idx += 1
                coverage_line = lines[line_idx].strip()
                if coverage_line.startswith("Covered:"):
                    parts = coverage_line.split()
                    covered, total = map(int, parts[1].split("/"))
                    percentage = float(parts[2].strip("()%")) / 100
                    statistics["coverage"]["genes"] = {
                        "covered": covered,
                        "total": total,
                        "percentage": percentage,
                    }

        elif section == "participation":
            if line.startswith("DMR Participation"):
                line_idx += 2  # Skip header
                while line_idx < len(lines) and lines[line_idx].strip():
                    parts = lines[line_idx].strip().split()
                    if len(parts) == 2:
                        statistics["node_participation"]["dmrs"][int(parts[0])] = int(
                            parts[1]
                        )
                    line_idx += 1
            elif line.startswith("Gene Participation"):
                line_idx += 2  # Skip header
                while line_idx < len(lines) and lines[line_idx].strip():
                    parts = lines[line_idx].strip().split()
                    if len(parts) == 2:
                        statistics["node_participation"]["genes"][int(parts[0])] = int(
                            parts[1]
                        )
                    line_idx += 1

        elif section == "edge":
            parts = line.split()
            if len(parts) >= 3:
                if parts[0] == "Single":
                    statistics["edge_coverage"]["single"] = int(parts[1])
                elif parts[0] == "Multiple":
                    statistics["edge_coverage"]["multiple"] = int(parts[1])
                elif parts[0] == "Uncovered":
                    statistics["edge_coverage"]["uncovered"] = int(parts[1])

        line_idx += 1

    return statistics


def parse_bicliques(
    lines: List[str], 
    max_DMR_id: int,
    gene_id_mapping: Dict[str, int] = None,
    file_format: str = "gene_name"
) -> Tuple[List[Tuple[Set[int], Set[int]]], int]:
    """Parse bicliques from file lines."""
    bicliques = []
    line_idx = 0
    
    print("\nParsing bicliques:")
    print(f"Max DMR ID: {max_DMR_id}")
    print(f"Gene mapping size: {len(gene_id_mapping) if gene_id_mapping else 0}")

    # Skip header until we find "# Clusters"
    while line_idx < len(lines):
        if lines[line_idx].strip() == "# Clusters":
            line_idx += 1  # Move to first cluster line
            break
        line_idx += 1

    # Parse bicliques
    while line_idx < len(lines):
        line = lines[line_idx].strip()
        if not line:
            line_idx += 1
            continue

        try:
            # Split line into tokens
            tokens = line.split()
            if not tokens:
                line_idx += 1
                continue
                
            gene_ids = set()
            dmr_ids = set()
            
            # Process each token
            for token in tokens:
                token = token.strip().lower()  # Normalize to lowercase
                
                try:
                    # Try parsing as DMR ID first
                    dmr_id = int(token)
                    if dmr_id < max_DMR_id:
                        dmr_ids.add(dmr_id)
                    continue
                except ValueError:
                    # Not a number, must be a gene name
                    if gene_id_mapping and token in gene_id_mapping:
                        gene_ids.add(gene_id_mapping[token])
                    else:
                        print(f"Warning: Gene '{token}' not found in mapping")

            # Only add valid bicliques
            if dmr_ids and gene_ids:
                bicliques.append((dmr_ids, gene_ids))
                if len(bicliques) <= 3:  # Debug first 3 bicliques
                    print(f"\nBiclique {len(bicliques)}:")
                    print(f"  Original line: {line}")
                    print(f"  DMRs: {sorted(dmr_ids)}")
                    print(f"  Genes: {sorted(gene_ids)}")

        except Exception as e:
            print(f"Warning: Error parsing line {line_idx + 1}: {str(e)}")
            print(f"Line content: {line}")

        line_idx += 1

    print(f"\nParsing complete:")
    print(f"Total bicliques found: {len(bicliques)}")
    if bicliques:
        print(f"First biclique DMRs: {sorted(bicliques[0][0])}")
        print(f"First biclique genes: {sorted(bicliques[0][1])}")

    return bicliques, line_idx


def calculate_coverage(
    bicliques: List[Tuple[Set[int], Set[int]]], original_graph: nx.Graph
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
        },
    }


def calculate_edge_distribution(
    bicliques: List[Tuple[Set[int], Set[int]]], original_graph: nx.Graph
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
    edge_distribution: Dict,
) -> Dict:
    """Create the final result dictionary."""
    dmr_nodes = {n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 0}
    gene_nodes = {n for n, d in original_graph.nodes(data=True) if d["bipartite"] == 1}

    uncovered_edges = set(original_graph.edges()) - set(edge_distribution.keys())
    uncovered_nodes = {node for edge in uncovered_edges for node in edge}

    # Calculate edge coverage percentages
    total_edges = len(original_graph.edges())
    single_coverage = len([e for e, b in edge_distribution.items() if len(b) == 1])
    multiple_coverage = len([e for e, b in edge_distribution.items() if len(b) > 1])

    coverage_info["edges"] = {
        "single_coverage": single_coverage,
        "multiple_coverage": multiple_coverage,
        "uncovered": len(uncovered_edges),
        "total": total_edges,
        "single_percentage": single_coverage / total_edges if total_edges > 0 else 0,
        "multiple_percentage": multiple_coverage / total_edges
        if total_edges > 0
        else 0,
        "uncovered_percentage": len(uncovered_edges) / total_edges
        if total_edges > 0
        else 0,
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
