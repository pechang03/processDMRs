# File: graph_utils.py
# Author: Peter Shaw

import networkx as nx
import pandas as pd
from typing import Dict
import os


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


def read_excel_file(filepath):
    """Read and validate an Excel file."""
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Excel file not found: {filepath}")

        print(f"Reading Excel file from: {filepath}")
        df = pd.read_excel(filepath, header=0)
        print(f"Column names: {df.columns.tolist()}")
        print("\nSample of input data:")

        # Determine which columns to display based on what's available
        if "Gene_Symbol_Nearby" in df.columns:
            gene_col = "Gene_Symbol_Nearby"
        elif "Gene_Symbol" in df.columns:
            gene_col = "Gene_Symbol"
        else:
            raise KeyError("No gene symbol column found in the file")

        print(
            df[
                [
                    "DMR_No.",
                    gene_col,
                    "ENCODE_Enhancer_Interaction(BingRen_Lab)",
                    "Gene_Description",
                ]
            ].head(10)
        )
        return df
    except FileNotFoundError:
        error_msg = f"Error: The file {filepath} was not found."
        print(error_msg)
        raise
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        raise


def create_bipartite_graph(
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    closest_gene_col: str = "Gene_Symbol_Nearby",
) -> nx.Graph:
    """Create a bipartite graph from DataFrame."""
    B = nx.Graph()
    
    # Add DMR nodes (0-based indexing)
    dmr_nodes = set(row["DMR_No."] - 1 for _, row in df.iterrows())
    for dmr in dmr_nodes:
        B.add_node(dmr, bipartite=0)

    # Add all gene nodes from mapping
    for gene_name, gene_id in gene_id_mapping.items():
        B.add_node(gene_id, bipartite=1)

    # Process each row to add edges
    edges_added = 0
    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Zero-based indexing
        
        # Process closest gene
        if pd.notna(row.get(closest_gene_col)):
            gene_name = str(row[closest_gene_col]).strip().lower()
            if gene_name in gene_id_mapping:
                gene_id = gene_id_mapping[gene_name]
                B.add_edge(dmr_id, gene_id)
                edges_added += 1

        # Process enhancer genes if present
        if pd.notna(row.get("Processed_Enhancer_Info")):
            genes = row["Processed_Enhancer_Info"]
            if isinstance(genes, str):
                genes = [g.strip() for g in genes.split(';')]
            elif isinstance(genes, (list, set)):
                genes = list(genes)
            else:
                continue
                
            for gene_name in genes:
                gene_name = str(gene_name).strip().lower()
                if gene_name in gene_id_mapping:
                    gene_id = gene_id_mapping[gene_name]
                    if not B.has_edge(dmr_id, gene_id):
                        B.add_edge(dmr_id, gene_id)
                        edges_added += 1

        # Process Associated_Genes if present
        if pd.notna(row.get("Associated_Genes")):
            genes = row["Associated_Genes"]
            if isinstance(genes, str):
                genes = [g.strip() for g in genes.split(';')]
            elif isinstance(genes, (list, set)):
                genes = list(genes)
            else:
                continue
                
            for gene_name in genes:
                gene_name = str(gene_name).strip().lower()
                if gene_name in gene_id_mapping:
                    gene_id = gene_id_mapping[gene_name]
                    if not B.has_edge(dmr_id, gene_id):
                        B.add_edge(dmr_id, gene_id)
                        edges_added += 1

    # Ensure no isolated nodes
    isolated_nodes = list(nx.isolates(B))
    if isolated_nodes:
        for node in isolated_nodes:
            if B.nodes[node]['bipartite'] == 1:  # If it's a gene node
                # Find a DMR to connect to
                for dmr in dmr_nodes:
                    B.add_edge(dmr, node)
                    edges_added += 1
                    break

    print(f"\nGraph construction summary:")
    print(f"DMR nodes: {len([n for n in B.nodes() if B.nodes[n]['bipartite'] == 0])}")
    print(f"Gene nodes: {len([n for n in B.nodes() if B.nodes[n]['bipartite'] == 1])}")
    print(f"Total edges added: {edges_added}")

    return B
