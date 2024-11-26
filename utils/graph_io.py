import networkx as nx
from typing import Tuple

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
        # Get unique edges (DMR first, gene second) and collect DMR nodes
        unique_edges = set()
        dmr_nodes = set()
        for edge in graph.edges():
            dmr_node = edge[0] if graph.nodes[edge[0]]["bipartite"] == 0 else edge[1]
            gene_node = edge[1] if graph.nodes[edge[0]]["bipartite"] == 0 else edge[0]
            unique_edges.add((dmr_node, gene_node))
            dmr_nodes.add(dmr_node)

        # Create sequential mapping for DMR IDs
        sorted_dmrs = sorted(dmr_nodes)
        dmr_id_mapping = {original_id: idx for idx, original_id in enumerate(sorted_dmrs)}

        # Sort edges for deterministic output
        sorted_edges = sorted(unique_edges)

        with open(output_file, "w") as file:
            # Write header
            n_dmrs = len(dmr_nodes)
            n_genes = len(gene_id_mapping)
            file.write(f"{n_dmrs} {n_genes}\n")

            # Write edges with sequential DMR IDs
            for dmr_id, gene_id in sorted_edges:
                sequential_dmr_id = dmr_id_mapping[dmr_id]
                file.write(f"{sequential_dmr_id} {gene_id}\n")

        # Validation output
        print(f"\nWrote graph to {output_file}:")
        print(f"DMRs: {n_dmrs}")
        print(f"Genes: {n_genes}")
        print(f"Edges: {len(sorted_edges)}")

        # Debug first few edges
        print("\nFirst 5 edges written:")
        for dmr_id, gene_id in sorted_edges[:5]:
            sequential_dmr_id = dmr_id_mapping[dmr_id]
            gene_name = [k for k, v in gene_id_mapping.items() if v == gene_id][0]
            print(f"DMR_{sequential_dmr_id} -> Gene_{gene_id} ({gene_name})")

        # Debug mapping
        print("\nDMR ID mapping sample (first 5):")
        for original_id in sorted(dmr_nodes)[:5]:
            print(f"Original ID: {original_id} -> Sequential ID: {dmr_id_mapping[original_id]}")

    except Exception as e:
        print(f"Error writing {output_file}: {e}")
        raise
