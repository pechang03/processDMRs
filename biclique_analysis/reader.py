# File reader.py
# Author: Peter Shaw

from typing import Dict, List, Union, Tuple, Set
import networkx as nx


def read_bicliques_file(
    filename: str, 
    max_DMR_id: int, 
    original_graph: nx.Graph,
    gene_id_mapping: Dict[str, int] = None,  # Make optional
    file_format: str = "id"  # Add format parameter, default to old format
) -> Dict:
    """Read and process bicliques from a .biclusters file for any bipartite graph."""
    print("\nReading bicliques file:")
    print(f"Expected DMR range: 0 to {max_DMR_id-1}")
    print(f"File format: {file_format}")

    with open(filename, "r") as f:
        lines = f.readlines()

    # Process file contents
    statistics = parse_header_statistics(lines)
    # Debug prints for gene_id_mapping
    print("\nFirst 10 entries in gene_id_mapping:")
    for gene, id in list(gene_id_mapping.items())[:10]:
        print(f"'{gene}': {id}")

    print("\nChecking for specific genes:")
    test_genes = ['oprk1', 'sgk3', 'xkr9', 'col9a1']
    for gene in test_genes:
        print(f"'{gene}' in mapping: {gene in gene_id_mapping}")

    bicliques, line_idx = parse_bicliques(lines, max_DMR_id, gene_id_mapping)

    # Calculate coverage information
    coverage_info = calculate_coverage(bicliques, original_graph)
    edge_distribution = calculate_edge_distribution(bicliques, original_graph)

    # Build and return result
    return create_result_dict(
        filename,
        bicliques,
        statistics,
        original_graph,
        coverage_info,
        edge_distribution,
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
                    if key
                    in ["Nb operations", "Nb splits", "Nb deletions", "Nb additions"]
                    else value.strip()
                )
            line_idx += 1
            continue
        break
    return statistics


def parse_bicliques(
    lines: List[str], 
    max_DMR_id: int,
    gene_id_mapping: Dict[str, int] = None,
    file_format: str = "id"
) -> Tuple[List[Tuple[Set[int], Set[int]]], int]:
    """Parse bicliques from file lines."""
    bicliques = []
    line_idx = 0
    
    # Add debug print for gene_id_mapping
    print(f"\nGene ID mapping size: {len(gene_id_mapping) if gene_id_mapping else 0}")
    if gene_id_mapping:
        print(f"Sample of gene names: {list(gene_id_mapping.keys())[:5]}")
    
    # Create set of valid DMR IDs (0 to max_DMR_id-1)
    valid_dmr_ids = set(range(max_DMR_id))

    # Skip to first biclique
    while line_idx < len(lines) and (
        not lines[line_idx].strip() or lines[line_idx].strip().startswith(("#", "- "))
    ):
        line_idx += 1

    # Parse bicliques
    while line_idx < len(lines):
        line = lines[line_idx].strip()
        if not line:
            line_idx += 1
            continue

        # Split line into tokens
        tokens = line.split()
        
        if file_format == "name":
            gene_ids = set()
            dmr_ids = set()
            
            for token in tokens:
                token = token.strip().lower()  # Normalize token
                
                # First check if it's a valid gene name
                if gene_id_mapping and token in gene_id_mapping:
                    gene_ids.add(gene_id_mapping[token])
                    continue
                    
                # Then try to parse as DMR ID
                try:
                    dmr_id = int(token)
                    if dmr_id in valid_dmr_ids:
                        dmr_ids.add(dmr_id)
                    else:
                        print(f"Warning: DMR ID {dmr_id} out of valid range on line {line_idx + 1}")
                except ValueError:
                    print(f"Warning: Token '{token}' not found in gene mapping on line {line_idx + 1}")
        else:
            # Handle original ID format
            try:
                parts = line.split(None, 1)
                if len(parts) != 2:
                    line_idx += 1
                    continue
                    
                gene_ids = {int(x) for x in parts[0].split()}
                dmr_ids = {int(x) for x in parts[1].split()}
                
            except ValueError as e:
                print(f"Warning: Error parsing line {line_idx + 1}: {e}")
                line_idx += 1
                continue

        # Only add valid bicliques
        if dmr_ids and gene_ids:  # Require both parts to be non-empty
            bicliques.append((dmr_ids, gene_ids))
        else:
            print(f"Warning: Skipping line {line_idx + 1} - missing DMRs or genes")
        
        line_idx += 1

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

    coverage_info["edges"] = {
        "single_coverage": len(
            [e for e, b in edge_distribution.items() if len(b) == 1]
        ),
        "multiple_coverage": len(
            [e for e, b in edge_distribution.items() if len(b) > 1]
        ),
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
