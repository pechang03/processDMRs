import networkx as nx
import pandas as pd
from typing import Dict, List, Set
from .reader import read_bicliques_file

def process_bicliques(
    bipartite_graph: nx.Graph, 
    bicliques_file: str,
    max_dmr_id: int,
    dataset_name: str
) -> Dict:
    """Process bicliques and add detailed information."""
    bicliques_result = read_bicliques_file(
        bicliques_file,
        max_dmr_id, 
        bipartite_graph
    )
    
    return bicliques_result

def _get_dmr_details(dmr_nodes: Set[int], df: pd.DataFrame) -> List[Dict]:
    """Get detailed information for DMR nodes."""
    dmr_details = []
    for dmr_id in dmr_nodes:
        dmr_row = df[df["DMR_No."] == dmr_id + 1].iloc[0]
        dmr_details.append({
            "id": dmr_id,
            "area": dmr_row["Area_Stat"] if "Area_Stat" in df.columns else "N/A",
            "description": dmr_row["DMR_Description"] if "DMR_Description" in df.columns else "N/A"
        })
    return dmr_details

def _get_gene_details(gene_nodes: Set[int], df: pd.DataFrame, gene_id_mapping: Dict) -> List[Dict]:
    """Get detailed information for gene nodes."""
    gene_details = []
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    for gene_id in gene_nodes:
        gene_name = reverse_gene_mapping.get(gene_id, f"Unknown_{gene_id}")
        matching_rows = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        if not matching_rows.empty:
            gene_desc = matching_rows.iloc[0]["Gene_Description"]
            gene_details.append({
                "name": gene_name,
                "description": gene_desc if pd.notna(gene_desc) and gene_desc != "N/A" else "N/A"
            })
        else:
            gene_details.append({
                "name": gene_name,
                "description": "N/A"
            })
    return gene_details

def _add_biclique_details(bicliques: List, df: pd.DataFrame, gene_id_mapping: Dict) -> Dict:
    """Add detailed information for each biclique."""
    detailed_info = {}
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        detailed_info[f"biclique_{idx+1}_details"] = {
            "dmrs": _get_dmr_details(dmr_nodes, df),
            "genes": _get_gene_details(gene_nodes, df, gene_id_mapping)
        }
    return detailed_info

# Add other helper functions...
def process_enhancer_info(enhancer_str: str) -> set:
    """
    Process the enhancer information from the ENCODE data.

    Parameters:
    enhancer_str (str): A string containing enhancer information, separated by ';'.

    Returns:
    set: A set of processed gene names, with any suffixes removed.
    """
    if pd.isna(enhancer_str) or enhancer_str == ".":
        return set()
    genes = enhancer_str.split(";")
    processed_genes = {gene.split("/")[0].strip().lower() for gene in genes if gene}
    return processed_genes
