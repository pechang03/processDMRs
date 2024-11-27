# File: Processor.py
# Author: Peter Shaw
#
import networkx as nx
import pandas as pd
from typing import Dict, List, Set, Tuple
from utils import process_enhancer_info
import re
import pandas as pd
# Removed data_loader import
from typing import Dict
import networkx as nx
import pandas as pd
from .reader import read_bicliques_file
from .components import process_components


def process_bicliques(
    bipartite_graph: nx.Graph,
    bicliques_file: str,
    dataset_name: str,
    gene_id_mapping: Dict[str, int] = None,
    file_format: str = "gene_name",
) -> Dict:
    """Process bicliques and add detailed information."""
    print(f"\nProcessing bicliques for {dataset_name}")
    print(f"Using format: {file_format}")
    
    try:
        # Read bicliques using reader.py
        bicliques_result = read_bicliques_file(
            bicliques_file,
            bipartite_graph,
            gene_id_mapping=gene_id_mapping,
            file_format=file_format
        )
        
        if not bicliques_result or not bicliques_result.get("bicliques"):
            print(f"No bicliques found in {bicliques_file}")
            return {
                "bicliques": [],
                "components": [],
                "statistics": {},
                "graph_info": {
                    "name": dataset_name,
                    "total_dmrs": sum(1 for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 0),
                    "total_genes": sum(1 for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 1),
                    "total_edges": len(bipartite_graph.edges()),
                }
            }

        # Process components using components.py
        # Update this line to match the 6 return values from process_components
        (
            complex_components,
            interesting_components,
            simple_components,  # Add this variable
            non_simple_components,
            component_stats,
            statistics
        ) = process_components(
            bipartite_graph,
            bicliques_result,
            dominating_set=None  # Add dominating set if needed
        )

        # Add component information to result
        bicliques_result.update({
            "complex_components": complex_components,
            "interesting_components": interesting_components,
            "non_simple_components": non_simple_components,
            "component_stats": component_stats,
            "statistics": statistics
        })

        print(f"\nProcessed bicliques result:")
        print(f"Total bicliques: {len(bicliques_result.get('bicliques', []))}")
        print(f"Complex components: {len(complex_components)}")
        print(f"Interesting components: {len(interesting_components)}")
        
        return bicliques_result

    except FileNotFoundError:
        print(f"Warning: Bicliques file not found: {bicliques_file}")
        return {
            "bicliques": [],
            "components": [],
            "statistics": {},
            "graph_info": {
                "name": dataset_name,
                "total_dmrs": sum(1 for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 0),
                "total_genes": sum(1 for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 1),
                "total_edges": len(bipartite_graph.edges()),
            }
        }
    except Exception as e:
        print(f"Error processing bicliques: {str(e)}")
        raise


def _get_dmr_details(dmr_nodes: Set[int], df: pd.DataFrame) -> List[Dict]:
    """Get detailed information for DMR nodes."""
    dmr_details = []
    for dmr_id in dmr_nodes:
        dmr_row = df[df["DMR_No."] == dmr_id + 1].iloc[0]
        dmr_details.append(
            {
                "id": dmr_id,
                "area": dmr_row["Area_Stat"] if "Area_Stat" in df.columns else "N/A",
                "description": dmr_row["DMR_Description"]
                if "DMR_Description" in df.columns
                else "N/A",
            }
        )
    return dmr_details


def _get_gene_details(
    gene_nodes: Set[int], df: pd.DataFrame, gene_id_mapping: Dict
) -> List[Dict]:
    """Get detailed information for gene nodes."""
    gene_details = []
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    for gene_id in gene_nodes:
        gene_name = reverse_gene_mapping.get(gene_id, f"Unknown_{gene_id}")
        matching_rows = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        if not matching_rows.empty:
            gene_desc = matching_rows.iloc[0]["Gene_Description"]
            gene_details.append(
                {
                    "name": gene_name,
                    "description": gene_desc
                    if pd.notna(gene_desc) and gene_desc != "N/A"
                    else "N/A",
                }
            )
        else:
            gene_details.append({"name": gene_name, "description": "N/A"})
    return gene_details


def _add_biclique_details(
    bicliques: List, df: pd.DataFrame, gene_id_mapping: Dict
) -> Dict:
    """Add detailed information for each biclique."""
    detailed_info = {}
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        detailed_info[f"biclique_{idx+1}_details"] = {
            "dmrs": _get_dmr_details(dmr_nodes, df),
            "genes": _get_gene_details(gene_nodes, df, gene_id_mapping),
        }
    return detailed_info


def process_dataset(df: pd.DataFrame, bipartite_graph: nx.Graph, gene_id_mapping: Dict[str, int]):
    """Process a dataset with pre-loaded graph and dataframe.

    Args:
        df: Loaded dataframe
        bipartite_graph: Pre-created bipartite graph
        gene_id_mapping: Gene name to ID mapping

    Returns:
        Tuple of (bipartite_graph, dataframe, gene_id_mapping)
    """
    # Process enhancer information if not already processed
    if "Processed_Enhancer_Info" not in df.columns:
        df["Processed_Enhancer_Info"] = df[
            "ENCODE_Enhancer_Interaction(BingRen_Lab)"
        ].apply(process_enhancer_info)

    return bipartite_graph, df, gene_id_mapping


# Add other helper functions...
def create_node_metadata(
    df: pd.DataFrame,
    gene_id_mapping: Dict[str, int],
    node_biclique_map: Dict[int, List[int]],
) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """
    Create metadata dictionaries for DMRs and genes.

    Args:
        df: DataFrame containing DMR and gene information
        gene_id_mapping: Mapping of gene names to IDs
        node_biclique_map: Mapping of nodes to their bicliques

    Returns:
        Tuple of (dmr_metadata, gene_metadata)
    """
    # Create DMR metadata
    dmr_metadata = {}
    for _, row in df.iterrows():
        dmr_id = row["DMR_No."] - 1  # Convert to 0-based index
        dmr_metadata[f"DMR_{row['DMR_No.']}"] = {
            "area": str(row["Area_Stat"]) if "Area_Stat" in df.columns else "N/A",
            "description": str(row["Gene_Description"])
            if "Gene_Description" in df.columns
            else "N/A",
            "name": f"DMR_{row['DMR_No.']}",
            "bicliques": node_biclique_map.get(dmr_id, []),
        }

    # Create gene metadata
    gene_metadata = {}
    for gene_name, gene_id in gene_id_mapping.items():
        gene_matches = df[df["Gene_Symbol_Nearby"].str.lower() == gene_name.lower()]
        description = "N/A"
        if not gene_matches.empty and "Gene_Description" in gene_matches.columns:
            description = str(gene_matches.iloc[0]["Gene_Description"])

        gene_metadata[gene_name] = {
            "description": description,
            "id": gene_id,
            "bicliques": node_biclique_map.get(gene_id, []),
            "name": gene_name,
        }

    return dmr_metadata, gene_metadata


def create_biclique_metadata(bicliques: List[Tuple[Set[int], Set[int]]]) -> List[Dict]:
    """
    Create detailed metadata for each biclique.
    
    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples
        
    Returns:
        List of dictionaries containing metadata for each biclique
    """
    from .classifier import classify_biclique
    from collections import defaultdict
    
    metadata = []
    
    # Track nodes across all bicliques for overlap calculations
    all_dmrs = set()
    all_genes = set()
    node_to_bicliques = defaultdict(set)
    
    # First pass - collect basic info and track nodes
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        all_dmrs.update(dmr_nodes)
        all_genes.update(gene_nodes)
        
        # Track which bicliques each node belongs to
        for node in dmr_nodes | gene_nodes:
            node_to_bicliques[node].add(idx)
    
    # Second pass - create detailed metadata
    for idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        # Calculate basic metrics
        size = len(dmr_nodes) + len(gene_nodes)
        density = len(dmr_nodes) * len(gene_nodes) / (size * size) if size > 0 else 0
        
        # Calculate overlap with other bicliques
        overlapping_bicliques = set()
        for node in dmr_nodes | gene_nodes:
            overlapping_bicliques.update(node_to_bicliques[node])
        overlapping_bicliques.discard(idx)  # Remove self
        
        # Calculate shared nodes with overlapping bicliques
        shared_nodes = {
            other_idx: len((dmr_nodes | gene_nodes) &
                          (bicliques[other_idx][0] | bicliques[other_idx][1]))
            for other_idx in overlapping_bicliques
        }
        
        # Get biclique classification
        category = classify_biclique(dmr_nodes, gene_nodes)
        
        # Create metadata dictionary
        biclique_metadata = {
            "id": idx,
            "size": {
                "total": size,
                "dmrs": len(dmr_nodes),
                "genes": len(gene_nodes)
            },
            "nodes": {
                "dmrs": sorted(dmr_nodes),
                "genes": sorted(gene_nodes)
            },
            "metrics": {
                "density": density,
                "dmr_ratio": len(dmr_nodes) / len(all_dmrs) if all_dmrs else 0,
                "gene_ratio": len(gene_nodes) / len(all_genes) if all_genes else 0,
                "edge_count": len(dmr_nodes) * len(gene_nodes)
            },
            "classification": {
                "category": category.name.lower(),
                "is_interesting": classify_biclique(dmr_nodes, gene_nodes) == BicliqueSizeCategory.INTERESTING
            },
            "relationships": {
                "overlapping_bicliques": len(overlapping_bicliques),
                "shared_nodes": shared_nodes,
                "max_overlap": max(shared_nodes.values()) if shared_nodes else 0
            }
        }
        
        metadata.append(biclique_metadata)
    
    return metadata
