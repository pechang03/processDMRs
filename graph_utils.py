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
    dmr_nodes = df["DMR_No."].values  # Ensure this is zero-based

    # Add DMR nodes with explicit bipartite attribute (0-based indexing)
    for dmr in dmr_nodes:
        B.add_node(dmr - 1, bipartite=0)  # Zero-based indexing

    # Add all gene nodes from mapping with bipartite=1 attribute
    for gene_name, gene_id in gene_id_mapping.items():
        B.add_node(gene_id, bipartite=1)

    # Initialize edge sources dictionary in graph
    B.graph["edge_sources"] = {}

    # Track edges and their sources
    edges_seen = set()
    edges_added = 0

    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Zero-based indexing
        associated_genes = set()
        gene_sources = {}

        # Add closest gene if it exists
        if pd.notna(row[closest_gene_col]) and row[closest_gene_col]:
            gene_name = str(row[closest_gene_col]).strip().lower()
            associated_genes.add(gene_name)
            gene_sources[gene_name] = {"Gene_Symbol_Nearby"}

        # Add enhancer genes if they exist
        if isinstance(row["Processed_Enhancer_Info"], (set, list)):
            enhancer_genes = {g.lower() for g in row["Processed_Enhancer_Info"] if g}
            associated_genes.update(enhancer_genes)
            for gene in enhancer_genes:
                if gene in gene_sources:
                    gene_sources[gene].add("ENCODE_Enhancer_Interaction(BingRen_Lab)")
                else:
                    gene_sources[gene] = {"ENCODE_Enhancer_Interaction(BingRen_Lab)"}

        # Add edges and track their sources
        for gene_name in associated_genes:
            gene_name = gene_name.lower()
            if gene_name in gene_id_mapping:
                gene_id = gene_id_mapping[gene_name]
                edge = tuple(sorted([dmr_id, gene_id]))
                
                if edge not in edges_seen:
                    # Add edge to graph
                    B.add_edge(dmr_id, gene_id)
                    edges_seen.add(edge)
                    edges_added += 1

                    # Store edge sources in graph attribute
                    B.graph["edge_sources"][edge] = gene_sources[gene_name]
                else:
                    # Update sources for existing edge
                    B.graph["edge_sources"][edge].update(gene_sources[gene_name])

    print(f"\nGraph construction summary:")
    print(f"DMR nodes: {len([n for n in B.nodes() if B.nodes[n]['bipartite'] == 0])}")
    print(f"Gene nodes: {len([n for n in B.nodes() if B.nodes[n]['bipartite'] == 1])}")
    print(f"Total edges added: {edges_added}")

    return B
