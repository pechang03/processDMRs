# File: graph_utils.py
# Author: Peter Shaw

import networkx as nx
import pandas as pd
from typing import Dict, List, Set
import os

# Configuration constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DSS1_FILE = os.path.join(DATA_DIR, "DSS1.xlsx")
DSS_PAIRWISE_FILE = os.path.join(DATA_DIR, "DSS_PAIRWISE.xlsx")
BIPARTITE_GRAPH_TEMPLATE = os.path.join(
    DATA_DIR, "bipartite_graph_output_{}_pairwise.txt"
)
BIPARTITE_GRAPH_OVERALL = os.path.join(
    DATA_DIR, "bipartite_graph_output_DSS_overall.txt"
)

def create_dmr_id(dmr_num: int, timepoint: str) -> int:
    """Create a unique DMR ID for a specific timepoint."""
    # Use a large offset (e.g., 1000000) for each timepoint to ensure no overlap
    timepoint_offsets = {
        "P21-P28": 1000000,
        "P21-P40": 2000000,
        "P21-P60": 3000000,
        "P21-P180": 4000000,
        "TP28-TP180": 5000000,
        "TP40-TP180": 6000000,
        "TP60-TP180": 7000000,
        "DSS1": 0  # Base timepoint uses original numbers
    }
    offset = timepoint_offsets.get(timepoint, 8000000)  # Default offset for unknown timepoints
    return offset + dmr_num


def validate_bipartite_graph(B):
    """Validate the bipartite graph properties and print detailed statistics"""
    # Check total degree sum
    total_degree = sum(dict(B.degree()).values())
    print(f"\nDegree Analysis:")
    print(f"Total edges: {B.number_of_edges()}")
    print(f"Sum of degrees: {total_degree}")
    print(f"Expected sum of degrees: {2 * B.number_of_edges()}")

    # Check for nodes with degree 0
    zero_degree_nodes = [n for n, d in B.degree() if d == 0]
    if zero_degree_nodes:
        print(f"\nWARNING: Found {len(zero_degree_nodes)} nodes with degree 0:")
        print(f"First 5 zero-degree nodes: {zero_degree_nodes[:5]}")
        
        # Analyze distribution of zero-degree nodes
        dmr_zeros = [n for n in zero_degree_nodes if B.nodes[n].get('bipartite') == 0]
        gene_zeros = [n for n in zero_degree_nodes if B.nodes[n].get('bipartite') == 1]
        print(f"Zero-degree DMRs: {len(dmr_zeros)}")
        print(f"Zero-degree Genes: {len(gene_zeros)}")

    # Get node sets by bipartite attribute
    top_nodes = {n for n, d in B.nodes(data=True) if d.get("bipartite") == 0}  # DMRs
    bottom_nodes = {n for n, d in B.nodes(data=True) if d.get("bipartite") == 1}  # Genes

    print(f"\nNode distribution:")
    print(f"  - DMR nodes (bipartite=0): {len(top_nodes)}")
    print(f"  - Gene nodes (bipartite=1): {len(bottom_nodes)}")

    # Detailed degree statistics
    dmr_degrees = [d for n, d in B.degree() if B.nodes[n].get('bipartite') == 0]
    gene_degrees = [d for n, d in B.degree() if B.nodes[n].get('bipartite') == 1]
    
    print(f"\nDegree statistics:")
    print(f"DMR degrees - min: {min(dmr_degrees)}, max: {max(dmr_degrees)}, avg: {sum(dmr_degrees)/len(dmr_degrees):.2f}")
    print(f"Gene degrees - min: {min(gene_degrees)}, max: {max(gene_degrees)}, avg: {sum(gene_degrees)/len(gene_degrees):.2f}")

    # Instead of raising an error, just warn about zero-degree nodes
    if zero_degree_nodes:
        print("\nWARNING: Graph contains nodes with degree 0")
        return False
    
    # Verify bipartite property
    if not nx.is_bipartite(B):
        print("\nERROR: Graph is not bipartite")
        return False

    # Print overall graph size
    print(f"\nTotal graph size:")
    print(f"  - Nodes: {B.number_of_nodes()}")
    print(f"  - Edges: {B.number_of_edges()}")

    return True


def validate_node_ids(dmr, gene_id, max_dmr_id, gene_id_mapping):
    """Validate node IDs are properly assigned"""
    if dmr >= max_dmr_id:
        print(f"Warning: Invalid DMR ID {dmr}")
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
        if sheet_name:
            print(f"Reading sheet: {sheet_name}")
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=0)
        else:
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
    timepoint: str = "DSS1",
) -> nx.Graph:
    """Create a bipartite graph from DataFrame with timepoint-specific DMR IDs."""
    B = nx.Graph()

    # Add DMR nodes with timepoint-specific IDs
    dmr_nodes = set(create_dmr_id(dmr-1, timepoint) for dmr in df["DMR_No."])
    for dmr in dmr_nodes:
        B.add_node(dmr, bipartite=0, timepoint=timepoint)

    # Add ALL gene nodes from mapping (even if not used in this timepoint)
    for gene_name, gene_id in gene_id_mapping.items():
        B.add_node(gene_id, bipartite=1)

    # Process each row to add edges
    edges_added = set()
    for _, row in df.iterrows():
        dmr_id = create_dmr_id(row["DMR_No."] - 1, timepoint)

        # Process closest gene
        if pd.notna(row.get("Gene_Symbol_Nearby")):
            gene_name = str(row["Gene_Symbol_Nearby"]).strip().lower()
            if gene_name in gene_id_mapping:
                gene_id = gene_id_mapping[gene_name]
                edge = (dmr_id, gene_id)
                if edge not in edges_added:
                    B.add_edge(*edge)
                    edges_added.add(edge)

        # Process enhancer genes
        if pd.notna(row.get("Processed_Enhancer_Info")):
            genes = row["Processed_Enhancer_Info"]
            if isinstance(genes, str):
                genes = [g.strip() for g in genes.split(";")]
            elif isinstance(genes, (list, set)):
                genes = list(genes)
            else:
                continue

            for gene_name in genes:
                gene_name = str(gene_name).strip().lower()
                if gene_name in gene_id_mapping:
                    gene_id = gene_id_mapping[gene_name]
                    edge = (dmr_id, gene_id)
                    if edge not in edges_added:
                        B.add_edge(*edge)
                        edges_added.add(edge)

    # Print detailed statistics
    print(f"\nGraph construction summary for timepoint {timepoint}:")
    print(f"Total DMR nodes: {len(dmr_nodes)}")
    print(f"Total Gene nodes: {len(gene_id_mapping)}")
    print(f"Active edges: {len(edges_added)}")
    
    # Print degree statistics
    zero_degree_dmrs = sum(1 for n in dmr_nodes if B.degree(n) == 0)
    zero_degree_genes = sum(1 for n in gene_id_mapping.values() if B.degree(n) == 0)
    print(f"DMR nodes with degree 0: {zero_degree_dmrs}")
    print(f"Gene nodes with degree 0: {zero_degree_genes}")

    return B


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
