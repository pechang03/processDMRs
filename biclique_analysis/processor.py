import networkx as nx
import pandas as pd
from typing import Dict, List
from .reader import read_bicliques_file

def process_bicliques(bipartite_graph: nx.Graph, df: pd.DataFrame, gene_id_mapping: Dict) -> Dict:
    """Process bicliques and add detailed information."""
    max_dmr_id = max(df["DMR_No."])
    bicliques_result = read_bicliques_file(
        "./data/bipartite_graph_output.txt.biclusters", 
        max_dmr_id, 
        bipartite_graph
    )
    
    detailed_info = _add_biclique_details(
        bicliques_result["bicliques"],
        df,
        gene_id_mapping
    )
    bicliques_result.update(detailed_info)
    
    return bicliques_result

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
