import networkx as nx
import csv
from typing import Dict, Tuple, Set, List
from .id_mapping import create_dmr_id


def read_bipartite_graph(filepath: str, timepoint: str = "DSS1", dmr_id_offset: int = 0) -> nx.Graph:
    """
    Read a bipartite graph from file.
    First line contains: <num_dmrs> <num_genes> <first_gene_id>
    
    Args:
        filepath: Path to graph file
        timepoint: Timepoint identifier
        dmr_id_offset: Offset to add to DMR IDs for this timepoint
        
    Returns:
        NetworkX bipartite graph
    """
    try:
        B = nx.Graph()

        with open(filepath, "r") as f:
            # Read header: num_dmrs num_genes first_gene_id
            n_dmrs, n_genes, first_gene_id = map(int, f.readline().strip().split())

            # Read edges
            for line in f:
                dmr_id, gene_id = map(int, line.strip().split())
                # Map the DMR ID to its timepoint-specific range using offset
                actual_dmr_id = create_dmr_id(dmr_id, timepoint, first_gene_id) + dmr_id_offset
                # Add nodes with proper bipartite attributes
                B.add_node(actual_dmr_id, bipartite=0, timepoint=timepoint)
                B.add_node(gene_id, bipartite=1)
                # Add edge
                B.add_edge(actual_dmr_id, gene_id)

        print(f"\nRead graph from {filepath}:")
        print(f"DMRs: {n_dmrs}")
        print(f"Genes: {n_genes}")
        print(f"First Gene ID: {first_gene_id}")
        print(f"DMR ID Offset: {dmr_id_offset}")
        print(f"Edges: {B.number_of_edges()}")

        return B

    except Exception as e:
        print(f"Error reading graph from {filepath}: {e}")
        raise


def write_bipartite_graph(
    graph: nx.Graph,
    output_file: str,
    df,
    gene_id_mapping: dict,
    timepoint: str = "DSS1",
):
    """Write bipartite graph to file using consistent gene IDs and sequential DMR IDs."""
    try:
        # Convert all gene names to lowercase in mapping
        gene_id_mapping = {
            k.strip().lower(): v for k, v in gene_id_mapping.items() if k
        }

        # Get unique edges (DMR first, gene second) and collect DMR nodes
        unique_edges = set()
        dmr_nodes = set()
        gene_nodes = set()

        # Debug counters
        total_edges = 0
        duplicate_edges = 0

        for edge in graph.edges():
            total_edges += 1
            # Ensure DMR is first and gene is second in edge
            if graph.nodes[edge[0]]["bipartite"] == 0:
                dmr_node, gene_node = edge
            else:
                gene_node, dmr_node = edge

            # Always order edges as (DMR, gene)
            ordered_edge = (dmr_node, gene_node)
            if ordered_edge in unique_edges:
                duplicate_edges += 1
                continue

            unique_edges.add(ordered_edge)
            dmr_nodes.add(dmr_node)
            gene_nodes.add(gene_node)

        # Create sequential mapping for DMR IDs starting from 0
        sorted_dmrs = sorted(dmr_nodes)
        dmr_id_mapping = {
            original_id: idx for idx, original_id in enumerate(sorted_dmrs)
        }

        # Sort edges for deterministic output
        sorted_edges = sorted(unique_edges)

        with open(output_file, "w") as file:
            # Write header with correct counts and first gene ID
            n_dmrs = len(dmr_nodes)
            n_genes = len(gene_nodes)
            min_gene_id = min(gene_nodes)
            file.write(f"{n_dmrs} {n_genes} {min_gene_id}\n")

            # Write edges with sequential DMR IDs
            for dmr_id, gene_id in sorted_edges:
                sequential_dmr_id = dmr_id_mapping[dmr_id]
                file.write(f"{sequential_dmr_id} {gene_id}\n")

        # Debug output
        print(f"\nWrote graph to {output_file}:")
        print(f"Total edges processed: {total_edges}")
        print(f"Duplicate edges removed: {duplicate_edges}")
        print(f"Final unique edges: {len(sorted_edges)}")
        print(f"DMRs: {n_dmrs}")
        print(f"Genes: {n_genes}")
        print(f"First gene ID: {min_gene_id}")

        # Debug first few edges
        print("\nFirst 5 edges written:")
        for dmr_id, gene_id in sorted_edges[:5]:
            sequential_dmr_id = dmr_id_mapping[dmr_id]
            gene_name = next(
                (k for k, v in gene_id_mapping.items() if v == gene_id), "Unknown"
            )
            print(f"DMR_{sequential_dmr_id} -> Gene_{gene_id} ({gene_name})")

    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        raise


def write_gene_mappings(
    gene_id_mapping: Dict[str, int], output_file: str, dataset_name: str
):
    """Write gene ID mappings to CSV file for a specific dataset."""
    try:
        print(f"\nWriting gene mappings for {dataset_name}:")
        print(f"Number of genes to write: {len(gene_id_mapping)}")
        print(
            f"ID range: {min(gene_id_mapping.values())} to {max(gene_id_mapping.values())}"
        )
        print("\nFirst few mappings:")
        for gene, gene_id in sorted(list(gene_id_mapping.items())[:5]):
            print(f"{gene}: {gene_id}")

        with open(output_file, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Gene", "ID"])
            for gene, gene_id in sorted(gene_id_mapping.items()):
                csvwriter.writerow([gene, gene_id])
        print(f"Wrote {len(gene_id_mapping)} gene mappings to {output_file}")
    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        raise


def remove_isolated_nodes(graph: nx.Graph, keep_dmrs: bool = True) -> nx.Graph:
    """
    Remove isolated nodes from the graph.

    Args:
        graph: Input graph
        keep_dmrs: If True, keeps isolated DMR nodes (bipartite=0)

    Returns:
        Graph with isolated nodes removed
    """
    G = graph.copy()
    isolated_nodes = list(nx.isolates(G))

    if keep_dmrs:
        # Only remove isolated gene nodes (bipartite=1)
        isolated_genes = [n for n in isolated_nodes if G.nodes[n].get("bipartite") == 1]
        G.remove_nodes_from(isolated_genes)
        print(f"Removed {len(isolated_genes)} isolated gene nodes")
    else:
        # Remove all isolated nodes
        G.remove_nodes_from(isolated_nodes)
        print(f"Removed {len(isolated_nodes)} isolated nodes")

    return G


def remove_bridge_edges(graph: nx.Graph, min_component_size: int = 3) -> nx.Graph:
    """
    Remove bridge edges that connect small components.

    Args:
        graph: Input graph
        min_component_size: Minimum size for components to keep

    Returns:
        Graph with bridge edges removed
    """
    G = graph.copy()
    bridges = list(nx.bridges(G))

    removed_edges = []
    for edge in bridges:
        # Temporarily remove the edge
        G.remove_edge(*edge)

        # Check resulting components
        components = list(nx.connected_components(G))
        small_components = [c for c in components if len(c) < min_component_size]

        if small_components:
            # Keep the edge removed if it creates small components
            removed_edges.append(edge)
        else:
            # Put the edge back if components are large enough
            G.add_edge(*edge)

    print(f"Removed {len(removed_edges)} bridge edges")
    return G


def preprocess_graph_for_visualization(
    graph: nx.Graph,
    remove_isolates: bool = True,
    remove_bridges: bool = False,
    keep_dmrs: bool = True,
    min_component_size: int = 3,
) -> nx.Graph:
    """
    Preprocess graph for visualization by optionally removing isolates and bridges.

    Args:
        graph: Input graph
        remove_isolates: Whether to remove isolated nodes
        remove_bridges: Whether to remove bridge edges
        keep_dmrs: Whether to keep isolated DMR nodes when removing isolates
        min_component_size: Minimum component size when removing bridges

    Returns:
        Preprocessed graph
    """
    G = graph.copy()

    if remove_isolates:
        G = remove_isolated_nodes(G, keep_dmrs=keep_dmrs)

    if remove_bridges:
        G = remove_bridge_edges(G, min_component_size=min_component_size)

    # Print statistics about the preprocessed graph
    print("\nPreprocessed graph statistics:")
    print(f"Nodes: {G.number_of_nodes()} (original: {graph.number_of_nodes()})")
    print(f"Edges: {G.number_of_edges()} (original: {graph.number_of_edges()})")

    return G
