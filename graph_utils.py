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
    print(f"\nDMR Analysis:")
    print(f"Number of unique DMRs: {n_dmrs}")
    print(f"DMR ID range: 0 to {max_dmr}")
    
    # Get all unique genes (case-insensitive)
    all_genes = set()
    
    # First add all genes from Gene_Symbol_Nearby (these are always valid)
    all_genes.update(df[closest_gene_col].dropna().str.strip().str.lower())
    
    # Add genes from enhancer interactions
    enhancer_col = "ENCODE_Enhancer_Interaction(BingRen_Lab)"
    if enhancer_col in df.columns:
        for genes in df["Processed_Enhancer_Info"]:
            if isinstance(genes, set):
                all_genes.update(g.lower() for g in genes)
                
    # Add genes from promoter interactions
    promoter_col = "ENCODE_Promoter_Interaction(BingRen_Lab)"
    if promoter_col in df.columns:
        df["Processed_Promoter_Info"] = df[promoter_col].apply(process_enhancer_info)
        for genes in df["Processed_Promoter_Info"]:
            if isinstance(genes, set):
                all_genes.update(g.lower() for g in genes)
    
    n_genes = len(all_genes)
    max_valid_gene_id = max_dmr + n_genes
    
    print(f"\nGene Analysis:")
    print(f"Number of unique genes: {n_genes}")
    print(f"Valid gene ID range: {max_dmr} to {max_valid_gene_id}")
    
    # Create gene mapping with continuous IDs
    gene_id_mapping.clear()
    start_id = max_dmr + 1  # Start right after last DMR
    for idx, gene in enumerate(sorted(all_genes)):
        gene_id = start_id + idx  # Ensure continuous IDs
        gene_id_mapping[gene] = gene_id
        
    print(f"\nGene ID Assignment:")
    print(f"Starting ID: {start_id}")
    print(f"Number of genes: {len(all_genes)}")
    print(f"ID range: {start_id} to {start_id + len(all_genes) - 1}")
    
    # Debug: Print first few mappings
    print("\nFirst few gene mappings:")
    for gene, gene_id in list(sorted(gene_id_mapping.items()))[:5]:
        print(f"{gene}: {gene_id}")
    
    # Add DMR nodes (0-based)
    for dmr in df["DMR_No."].values:
        dmr_id = dmr - 1  # Convert 1-based to 0-based
        B.add_node(dmr_id, bipartite=0)
    
    # Add edges
    edges_added = 0
    edges_seen = set()
    
    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1
        associated_genes = set()

        # Always add the closest gene if it exists
        if pd.notna(row[closest_gene_col]):
            gene_name = str(row[closest_gene_col]).strip().lower()
            associated_genes.add(gene_name)

        # Add valid enhancer genes
        if isinstance(row["Processed_Enhancer_Info"], set):
            associated_genes.update(g.lower() for g in row["Processed_Enhancer_Info"])
            
        # Add promoter genes if they exist
        if "Processed_Promoter_Info" in row and isinstance(row["Processed_Promoter_Info"], set):
            associated_genes.update(g.lower() for g in row["Processed_Promoter_Info"])

        # Add edges
        for gene in associated_genes:
            if gene in gene_id_mapping:
                gene_id = gene_id_mapping[gene]
                edge = tuple(sorted([dmr_id, gene_id]))
                if edge not in edges_seen:
                    B.add_node(gene_id, bipartite=1)
                    B.add_edge(dmr_id, gene_id)
                    edges_seen.add(edge)
                    edges_added += 1

    print(f"\nGraph Summary:")
    print(f"Total edges added: {edges_added}")
    print(f"Final graph: {len(B.nodes())} nodes, {len(B.edges())} edges")
    
    # Validation
    max_gene_id = max(gene_id_mapping.values())
    if max_gene_id >= n_dmrs + len(all_genes):
        print(f"WARNING: Maximum gene ID {max_gene_id} exceeds expected range!")
    
    return B
