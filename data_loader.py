# File: graph_utils.py
# Author: Peter Shaw

import networkx as nx
import pandas as pd
from typing import Dict, List, Set, Tuple
import os

from utils.id_mapping import create_dmr_id, create_gene_mapping, validate_gene_mapping
from utils.data_processing import process_enhancer_info
from utils.graph_io import (
    read_bipartite_graph, 
    write_bipartite_graph,
    remove_isolated_nodes,
    preprocess_graph_for_visualization
)
from utils.constants import START_GENE_ID


# Configuration constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "processDMRs", "data")
DSS1_FILE = os.path.join(DATA_DIR, "DSS1.xlsx")
DSS_PAIRWISE_FILE = os.path.join(DATA_DIR, "DSS_PAIRWISE.xlsx")
BIPARTITE_GRAPH_TEMPLATE = os.path.join(
    DATA_DIR, "bipartite_graph_output_{}_pairwise.txt"
)
BIPARTITE_GRAPH_OVERALL = os.path.join(
    DATA_DIR, "bipartite_graph_output_DSS_overall.txt"
)


def validate_bipartite_graph(B):
    """Validate the bipartite graph properties and print detailed statistics"""
    # Create a copy of the graph to work with
    G = B.copy()

    # Find and remove isolated nodes
    isolated_nodes = list(nx.isolates(G))
    if isolated_nodes:
        print(f"\nRemoving {len(isolated_nodes)} isolated nodes")
        # Only remove isolated gene nodes (bipartite=1)
        isolated_genes = [n for n in isolated_nodes if G.nodes[n].get("bipartite") == 1]
        G.remove_nodes_from(isolated_genes)
        print(f"Removed {len(isolated_genes)} isolated gene nodes")

    # Check total degree sum
    total_degree = sum(dict(G.degree()).values())
    print(f"\nDegree Analysis:")
    print(f"Total edges: {G.number_of_edges()}")
    print(f"Sum of degrees: {total_degree}")
    print(f"Expected sum of degrees: {2 * G.number_of_edges()}")

    # Validate node types
    dmr_nodes = {n for n, d in G.nodes(data=True) if d.get("bipartite") == 0}
    gene_nodes = {n for n, d in G.nodes(data=True) if d.get("bipartite") == 1}

    print(f"\nNode type validation:")
    print(f"Total DMR nodes: {len(dmr_nodes)}")
    print(f"Total Gene nodes: {len(gene_nodes)}")

    # Check for nodes without proper bipartite attribute
    invalid_nodes = {n for n, d in G.nodes(data=True) if "bipartite" not in d}
    if invalid_nodes:
        print(f"\nWARNING: {len(invalid_nodes)} nodes without bipartite attribute")
        print(f"First 5 invalid nodes: {list(invalid_nodes)[:5]}")

    # Get node sets by bipartite attribute
    top_nodes = {n for n, d in G.nodes(data=True) if d.get("bipartite") == 0}  # DMRs
    bottom_nodes = {
        n for n, d in G.nodes(data=True) if d.get("bipartite") == 1
    }  # Genes

    print(f"\nNode distribution:")
    print(f"  - DMR nodes (bipartite=0): {len(top_nodes)}")
    print(f"  - Gene nodes (bipartite=1): {len(bottom_nodes)}")

    # Detailed degree statistics
    dmr_degrees = [d for n, d in G.degree() if G.nodes[n].get("bipartite") == 0]
    gene_degrees = [d for n, d in G.degree() if G.nodes[n].get("bipartite") == 1]

    if dmr_degrees and gene_degrees:  # Only calculate if we have nodes
        print(f"\nDegree statistics:")
        print(
            f"DMR degrees - min: {min(dmr_degrees)}, max: {max(dmr_degrees)}, avg: {sum(dmr_degrees)/len(dmr_degrees):.2f}"
        )
        print(
            f"Gene degrees - min: {min(gene_degrees)}, max: {max(gene_degrees)}, avg: {sum(gene_degrees)/len(gene_degrees):.2f}"
        )

    # Verify bipartite property
    if not nx.is_bipartite(G):
        print("\nERROR: Graph is not bipartite")
        return False

    # Print overall graph size
    print(f"\nTotal graph size:")
    print(f"  - Nodes: {G.number_of_nodes()}")
    print(f"  - Edges: {G.number_of_edges()}")

    return G  # Return the cleaned graph instead of True


def validate_node_ids(dmr, gene_id, gene_id_mapping):
    """Validate node IDs are properly assigned"""

    if dmr >= START_GENE_ID:
        print(f"Warning: DMR ID {dmr} is >= START_GENE_ID ({START_GENE_ID})")
        return False
    if gene_id not in set(gene_id_mapping.values()):
        print(f"Warning: Invalid gene ID {gene_id}")
        return False
    return True


def read_excel_file(filepath, sheet_name=None):
    """Read and validate an Excel file."""
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Excel file not found: {filepath}")

        print(f"Reading Excel file from: {filepath}")

        # Read the Excel file with explicit dtypes
        dtype_map = {
            "DMR_No.": int,
            "Gene_Symbol_Nearby": str,
            "ENCODE_Enhancer_Interaction(BingRen_Lab)": str
        }
        
        if sheet_name:
            df = pd.read_excel(filepath, sheet_name=sheet_name, dtype=dtype_map)
        else:
            df = pd.read_excel(filepath, dtype=dtype_map)

        # Add Processed_Enhancer_Info column if not already present
        if "Processed_Enhancer_Info" not in df.columns:
            df["Processed_Enhancer_Info"] = df[
                "ENCODE_Enhancer_Interaction(BingRen_Lab)"
            ].apply(process_enhancer_info)

        print(f"Read {len(df)} rows with DMR range: {df['DMR_No.'].min()}-{df['DMR_No.'].max()}")
        return df  # Return the DataFrame directly

    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        raise


def get_excel_sheets(filepath: str) -> List[str]:
    """Get all sheet names from an Excel file."""
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Excel file not found: {filepath}")

        print(f"Reading sheet names from: {filepath}")
        xl = pd.ExcelFile(filepath)
        sheets = xl.sheet_names
        print(f"Found sheets: {sheets}")
        return sheets
    except Exception as e:
        print(f"Error reading sheet names from {filepath}: {e}")
        raise


def read_bipartite_graph(
    filepath: str, timepoint: str = "DSS1"
) -> Tuple[nx.Graph, int]:
    """
    Read a bipartite graph from file, including the first gene ID.

    Returns:
        Tuple of (graph, first_gene_id)
    """
    try:
        B = nx.Graph()

        with open(filepath, "r") as f:
            # Read header
            n_dmrs, n_genes = map(int, f.readline().strip().split())
            # Read first gene ID
            first_gene_id = int(f.readline().strip())

            # Read edges
            for line in f:
                dmr_id, gene_id = map(int, line.strip().split())
                # Map the DMR ID to its timepoint-specific range
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


def create_bipartite_graph(
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    timepoint: str = "DSS1",
    closest_gene_col: str = "Gene_Symbol_Nearby",
) -> nx.Graph:
    """Create a bipartite graph from DataFrame."""
    B = nx.Graph()

    print(f"\nCreating bipartite graph for timepoint: {timepoint}")

    # Convert gene mapping to lowercase for case-insensitive matching
    gene_id_mapping = {k.lower(): v for k, v in gene_id_mapping.items() if k}

    # Validate gene mapping
    max_dmr_id = df["DMR_No."].max() - 1  # Convert to 0-based index
    if not validate_gene_mapping(gene_id_mapping, max_dmr_id):
        print("Warning: Gene mapping validation failed")

    # Add DMR nodes first with proper timepoint-specific IDs
    dmr_nodes = set()
    for _, row in df.iterrows():
        dmr_num = int(row["DMR_No."]) - 1  # Convert to 0-based index
        dmr_id = create_dmr_id(dmr_num, timepoint, min(gene_id_mapping.values()))
        dmr_nodes.add(dmr_id)
        B.add_node(dmr_id, bipartite=0, timepoint=timepoint)

    # Add gene nodes
    for gene_name, gene_id in gene_id_mapping.items():
        B.add_node(gene_id, bipartite=1)

    # Process edges
    edges_added = set()
    for _, row in df.iterrows():
        dmr_num = int(row["DMR_No."]) - 1
        dmr_id = create_dmr_id(dmr_num, timepoint, min(gene_id_mapping.values()))

        # Add edge for closest gene
        if pd.notna(row.get(closest_gene_col)):
            gene_name = str(row[closest_gene_col]).strip().lower()
            if gene_name in gene_id_mapping:
                gene_id = gene_id_mapping[gene_name]
                edge = (dmr_id, gene_id)
                if edge not in edges_added:
                    B.add_edge(*edge)
                    edges_added.add(edge)

        # Add edges for enhancer genes
        if pd.notna(row.get("ENCODE_Enhancer_Interaction(BingRen_Lab)")):
            enhancer_genes = process_enhancer_info(
                row["ENCODE_Enhancer_Interaction(BingRen_Lab)"]
            )
            for gene_name in enhancer_genes:
                gene_name = gene_name.lower()
                if gene_name in gene_id_mapping:
                    gene_id = gene_id_mapping[gene_name]
                    edge = (dmr_id, gene_id)
                    if edge not in edges_added:
                        B.add_edge(*edge)
                        edges_added.add(edge)

    # Remove isolated nodes and preprocess graph
    B = remove_isolated_nodes(B, keep_dmrs=True)
    B = preprocess_graph_for_visualization(B, remove_isolates=True, keep_dmrs=True)

    print(f"\nGraph construction summary for {timepoint}:")
    print(f"DMR nodes: {len(dmr_nodes)}")
    print(f"Gene nodes: {len([n for n in B.nodes() if B.nodes[n]['bipartite'] == 1])}")
    print(f"Total edges added: {len(edges_added)}")

    return B
