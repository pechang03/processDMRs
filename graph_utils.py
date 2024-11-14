# File: graph_utils.py
# Author: Peter Shaw

import networkx as nx
import pandas as pd
from typing import Dict
from biclique_analysis.processor import process_enhancer_info


def validate_bipartite_graph(B):
    """Validate the bipartite graph properties and print detailed statistics"""
    # Check for nodes with degree 0
    zero_degree_nodes = [n for n, d in B.degree() if d == 0]
    if zero_degree_nodes:
        print(f"\nERROR: Found {len(zero_degree_nodes)} nodes with degree 0:")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")
        raise ValueError("Graph contains nodes with degree 0")
    else:
        print("✓ All nodes have degree > 0")

    # Get node sets by bipartite attribute
    top_nodes = {n for n, d in B.nodes(data=True) if d.get("bipartite") == 0}  # DMRs
    bottom_nodes = {
        n for n, d in B.nodes(data=True) if d.get("bipartite") == 1
    }  # Genes

    print(f"\nNode distribution:")
    print(f"  - DMR nodes (bipartite=0): {len(top_nodes)}")
    print(f"  - Gene nodes (bipartite=1): {len(bottom_nodes)}")

    # Degree statistics
    degrees = dict(B.degree())
    min_degree = min(degrees.values())
    max_degree = max(degrees.values())
    avg_degree = sum(degrees.values()) / len(degrees)

    print(f"\nDegree statistics:")
    print(f"  - Minimum degree: {min_degree}")
    print(f"  - Maximum degree: {max_degree}")
    print(f"  - Average degree: {avg_degree:.2f}")

    # Connected components analysis
    components = list(nx.connected_components(B))
    print(f"\nConnected components:")
    print(f"  - Number of components: {len(components)}")
    print(f"  - Largest component size: {len(max(components, key=len))}")
    print(f"  - Smallest component size: {len(min(components, key=len))}")

    # Verify bipartite property
    if not nx.is_bipartite(B):
        print("\nERROR: Graph is not bipartite")
        raise ValueError("Graph is not bipartite")
    else:
        print("\n✓ Graph is bipartite")

    # Print overall graph size
    print(f"\nTotal graph size:")
    print(f"  - Nodes: {B.number_of_nodes()}")
    print(f"  - Edges: {B.number_of_edges()}")


def validate_node_ids(dmr, gene_id, max_dmr_id, gene_id_mapping):
    """Validate node IDs are properly assigned"""
    if dmr >= max_dmr_id:
        print(f"Warning: Invalid DMR ID {dmr}")
        return False
    if gene_id not in set(gene_id_mapping.values()):
        print(f"Warning: Invalid gene ID {gene_id}")
        return False
    return True

def create_bipartite_graph(df: pd.DataFrame, gene_id_mapping: Dict[str, int], closest_gene_col: str = "Gene_Symbol_Nearby") -> nx.Graph:
    """Create a bipartite graph from DataFrame."""
    B = nx.Graph()
    
    # Get number of DMRs (convert from 1-based to 0-based)
    n_dmrs = len(df["DMR_No."].unique())
    max_dmr = n_dmrs - 1
    
    print("\nDEBUG: Bipartite Graph Creation")
    print(f"Number of unique DMRs: {n_dmrs}")
    print(f"DMR ID range: 0 to {max_dmr}")
    
    # Add DMR nodes (0-based)
    for dmr in df["DMR_No."].values:
        dmr_id = dmr - 1  # Convert 1-based to 0-based
        B.add_node(dmr_id, bipartite=0)
    
    # Track unique edges and genes
    edges_seen = set()
    genes_seen = set()
    
    print("\nCreating bipartite graph:")
    print(f"Input rows: {len(df)}")
    print(f"Available gene mappings: {len(gene_id_mapping)}")
    
    # Add DMR nodes (0-based)
    dmr_nodes = set(df["DMR_No."].values)
    for dmr in dmr_nodes:
        dmr_id = dmr - 1  # Convert to 0-based
        B.add_node(dmr_id, bipartite=0)
    
    # Process each row
    for idx, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Convert to 0-based
        associated_genes = set()
        
        # Add closest gene if it exists
        if pd.notna(row[closest_gene_col]):
            gene_name = str(row[closest_gene_col]).strip().lower()
            if gene_name:
                associated_genes.add(gene_name)
        
        # Add enhancer genes if they exist
        if isinstance(row["Processed_Enhancer_Info"], (set, list)):
            enhancer_genes = {g.strip().lower() for g in row["Processed_Enhancer_Info"] if g}
            associated_genes.update(enhancer_genes)
        
        # Debug first few rows
        if idx < 5:
            print(f"\nDMR {dmr_id + 1}:")
            print(f"Associated genes: {associated_genes}")
        
        # Add edges
        for gene_name in associated_genes:
            if gene_name in gene_id_mapping:
                gene_id = gene_id_mapping[gene_name]
                
                # Create unique edge tuple (always DMR first)
                edge = (dmr_id, gene_id)
                
                if edge not in edges_seen:
                    # Add gene node if new
                    if gene_id not in genes_seen:
                        B.add_node(gene_id, bipartite=1)
                        genes_seen.add(gene_id)
                    
                    # Add edge
                    B.add_edge(*edge)
                    edges_seen.add(edge)
                    
                    # Debug first few edges
                    if len(edges_seen) <= 5:
                        print(f"Added edge: DMR_{dmr_id + 1} -> Gene_{gene_id} ({gene_name})")
    
    # Validation
    print("\nGraph Statistics:")
    print(f"DMR nodes: {len([n for n, d in B.nodes(data=True) if d['bipartite'] == 0])}")
    print(f"Gene nodes: {len([n for n, d in B.nodes(data=True) if d['bipartite'] == 1])}")
    print(f"Total edges: {len(B.edges())}")
    
    # Verify first few genes have edges
    gene_nodes = sorted([n for n, d in B.nodes(data=True) if d['bipartite'] == 1])[:5]
    print("\nFirst 5 gene nodes and their connections:")
    for gene_id in gene_nodes:
        gene_name = [k for k, v in gene_id_mapping.items() if v == gene_id][0]
        neighbors = list(B.neighbors(gene_id))
        print(f"Gene {gene_id} ({gene_name}): connected to DMRs {[n+1 for n in neighbors]}")
    
    return B

    print("\nGraph Creation Summary:")
    print(f"Total edges added: {edges_added}")
    print(f"Edges skipped (duplicates): {edges_skipped}")
    print(f"DMR nodes: {sum(1 for _, d in B.nodes(data=True) if d['bipartite'] == 0)}")
    print(f"Gene nodes: {sum(1 for _, d in B.nodes(data=True) if d['bipartite'] == 1)}")
    print(f"Total nodes: {len(B.nodes())}")
    print(f"Total edges: {len(B.edges())}")
    
    # Verify first few gene nodes have edges
    first_genes = sorted([n for n, d in B.nodes(data=True) if d['bipartite'] == 1])[:5]
    print("\nFirst 5 gene nodes and their edges:")
    for gene_id in first_genes:
        gene_name = [k for k, v in gene_id_mapping.items() if v == gene_id][0]
        print(f"Gene {gene_id} ({gene_name}): {list(B.neighbors(gene_id))}")

    return B
