import networkx as nx
import pandas as pd
from typing import Dict, List, Set, Tuple
from .reader import read_bicliques_file
import pandas as pd

def process_enhancer_info(enhancer_info):
    """Process enhancer interaction information."""
    if pd.isna(enhancer_info) or not enhancer_info:
        return set()
    return {gene.strip() for gene in str(enhancer_info).split(";") if gene.strip()}

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

def process_dataset(excel_file: str):
    """Process an Excel dataset and create bipartite graph.
    
    Args:
        excel_file: Path to Excel file
        
    Returns:
        Tuple of (bipartite_graph, dataframe, gene_id_mapping)
    """
    from processDMR import read_excel_file, create_bipartite_graph
    
    # Read the Excel file
    df = read_excel_file(excel_file)
    
    # Process enhancer information
    df["Processed_Enhancer_Info"] = df["ENCODE_Enhancer_Interaction(BingRen_Lab)"].apply(process_enhancer_info)
    
    # Create gene ID mapping
    all_genes = set()
    all_genes.update(df["Gene_Symbol_Nearby"].dropna())
    all_genes.update([g for genes in df["Processed_Enhancer_Info"] for g in genes])
    gene_id_mapping = {gene: idx + len(df) for idx, gene in enumerate(sorted(all_genes))}
    
    # Create bipartite graph
    bipartite_graph = create_bipartite_graph(df, gene_id_mapping)
    
    return bipartite_graph, df, gene_id_mapping

# Add other helper functions...
