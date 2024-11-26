import networkx as nx
import csv
from typing import Dict, Tuple

def read_bipartite_graph(filepath: str, timepoint: str = "DSS1") -> Tuple[nx.Graph, int]:
    """
    Read a bipartite graph from file, including the first gene ID.
    
    Returns:
        Tuple of (graph, first_gene_id)
    """
    try:
        B = nx.Graph()
        
        with open(filepath, 'r') as f:
            # Read header
            n_dmrs, n_genes = map(int, f.readline().strip().split())
            # Read first gene ID
            first_gene_id = int(f.readline().strip())
            
            # Read edges
            for line in f:
                dmr_id, gene_id = map(int, line.strip().split())
                # Map the DMR ID to its timepoint-specific range
                from .id_mapping import create_dmr_id
                actual_dmr_id = create_dmr_id(dmr_id, timepoint, first_gene_id)
                # Add nodes with proper bipartite attributes
                B.add_node(actual_dmr_id, bipartite=0, timepoint=timepoint)
                B.add_node(gene_id, bipartite=1)
                # Add edge
                B.add_edge(actual_dmr_id, gene_id)
                
        print(f"\nRead graph from {filepath}:")
        print(f"DMRs: {n_dmrs}")
        print(f"Genes: {n_genes}")
        print(f"First Gene ID: {first_gene_id}")
        print(f"Edges: {B.number_of_edges()}")
        
        return B, first_gene_id
        
    except Exception as e:
        print(f"Error reading graph from {filepath}: {e}")
        raise

def write_bipartite_graph(
    graph: nx.Graph, output_file: str, df, gene_id_mapping: dict, timepoint: str = "DSS1"
):
    """Write bipartite graph to file using consistent gene IDs and sequential DMR IDs."""
    try:
        # Convert all gene names to lowercase in mapping
        gene_id_mapping = {k.strip().lower(): v for k, v in gene_id_mapping.items() if k}
        
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
        dmr_id_mapping = {original_id: idx for idx, original_id in enumerate(sorted_dmrs)}

        # Sort edges for deterministic output
        sorted_edges = sorted(unique_edges)

        with open(output_file, "w") as file:
            # Write header with correct counts
            n_dmrs = len(dmr_nodes)
            n_genes = len(gene_nodes)
            file.write(f"{n_dmrs} {n_genes}\n")
            
            # Write first gene ID (minimum gene ID) on second line
            min_gene_id = min(gene_nodes)
            file.write(f"{min_gene_id}\n")

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
            gene_name = next((k for k, v in gene_id_mapping.items() if v == gene_id), "Unknown")
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
