"""Utilities package"""

import re
import pandas as pd
from flask import Blueprint

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

main_bp = Blueprint('main', __name__)
components_bp = Blueprint('components', __name__)

def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(main_bp)  # Register at root URL
    app.register_blueprint(components_bp, url_prefix='/components')

# Import routes after blueprint creation to avoid circular imports
from . import main_routes
from . import component_routes

def process_enhancer_info(enhancer_str):
    """
    Process enhancer interaction string and return set of gene names.
    
    Args:
        enhancer_str (str): Raw enhancer interaction string
    
    Returns:
        set: Set of unique gene names
    """
    if pd.isna(enhancer_str) or not isinstance(enhancer_str, str):
        return set()
    
    # Split by semicolon first, then handle potential gene/number pairs
    genes = set()
    for entry in str(enhancer_str).strip().split(';'):
        entry = entry.strip()
        if entry:
            # Split on / and take only the gene part
            if '/' in entry:
                gene = entry.split('/')[0].strip()
            else:
                gene = entry.strip()
            if gene:  # Only add non-empty genes
                genes.add(gene)
    
    return genes

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
