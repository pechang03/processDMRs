"""Utility functions for JSON serialization."""

import numpy as np
from typing import Any, Dict, List, Set, Tuple

def convert_for_json(data: Any) -> Any:
    """Comprehensive conversion of data types for JSON serialization."""
    if isinstance(data, dict):
        return {
            "_".join(map(str, k)) if isinstance(k, tuple) else str(k): convert_for_json(v)
            for k, v in data.items()
        }
    elif isinstance(data, (list, tuple)):
        return [convert_for_json(i) for i in data]
    elif isinstance(data, set):
        return sorted(list(data))
    elif isinstance(data, (np.integer, np.int_)):
        return int(data)
    elif isinstance(data, (np.floating, np.float_)):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, np.bool_):
        return bool(data)
    elif isinstance(data, nx.Graph):
        # Convert NetworkX graph to serializable format
        return {
            "nodes": list(data.nodes()),
            "edges": list(data.edges()),
            "node_attributes": {str(n): d for n, d in data.nodes(data=True)},
            "edge_attributes": {str(e): d for e, d in data.edges(data=True)}
        }
    return data

def convert_sets_to_lists(data: Any) -> Any:
    """Convert sets to sorted lists recursively."""
    if isinstance(data, dict):
        return {k: convert_sets_to_lists(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_sets_to_lists(i) for i in data]
    elif isinstance(data, set):
        return sorted(list(data))
    elif isinstance(data, tuple):
        return list(data)
    return data

# Alias for backward compatibility
convert_all_for_json = convert_for_json
convert_stats_for_json = convert_for_json
convert_dict_keys_to_str = convert_for_json
