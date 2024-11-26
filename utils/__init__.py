"""Utilities package"""

import re
import pandas as pd

from .edge_info import EdgeInfo
from .node_info import NodeInfo
from .json_utils import (
    convert_for_json,
    convert_sets_to_lists,
    convert_all_for_json,
    convert_stats_for_json,
    convert_dict_keys_to_str,
)
from .graph_utils import create_node_biclique_map, get_node_position
from .graph_io import read_bipartite_graph, write_bipartite_graph
from .id_mapping import create_dmr_id

def process_enhancer_info(enhancer_str):
    """
    Process enhancer interaction string and return list of genes.
    
    Args:
        enhancer_str (str): Raw enhancer interaction string
    
    Returns:
        list: List of unique gene names
    """
    if pd.isna(enhancer_str) or not isinstance(enhancer_str, str):
        return []
    
    # Split by various delimiters and clean
    genes = re.split(r'[,;/]', str(enhancer_str))
    genes = [g.strip() for g in genes if g.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_genes = [g for g in genes if not (g in seen or seen.add(g))]
    
    return unique_genes

__all__ = [
    "EdgeInfo",
    "NodeInfo",
    "convert_for_json",
    "convert_sets_to_lists",
    "convert_all_for_json",
    "convert_stats_for_json",
    "convert_dict_keys_to_str",
    "create_node_biclique_map",
    "get_node_position",
    "read_bipartite_graph",
    "write_bipartite_graph",
    "create_dmr_id",
    "process_enhancer_info",
]
"""Utilities package"""
