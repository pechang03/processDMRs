"""Utility functions for JSON serialization."""

import numpy as np
import networkx as nx
from typing import Any, Dict, List, Set, Tuple
import plotly.graph_objects as go
from flask import current_app

#  AI. 1 Keep data in native Python types throughout the business logic (biclique_analysis/*)
#  AI. 2 Otherwise always convert to JSON-safe formats at the API boundary (routes/*.py)


def convert_for_json(data: Any) -> Any:
    """Comprehensive conversion of data types for JSON serialization."""
    if isinstance(data, dict):
        return {
            "_".join(map(str, k)) if isinstance(k, tuple) else str(k): convert_for_json(
                v
            )
            for k, v in data.items()
        }
    elif isinstance(data, (list, tuple)):
        return [convert_for_json(i) for i in data]
    elif isinstance(data, set):
        return sorted(list(data))
    elif isinstance(data, (np.integer, np.int_)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64)):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, np.bool_):
        return bool(data)
    elif isinstance(data, nx.Graph):
        # Fix the edge attributes handling
        return {
            "nodes": list(data.nodes()),
            "edges": list(data.edges()),
            "node_attributes": {str(n): d for n, d in data.nodes(data=True)},
            "edge_attributes": {f"{u}_{v}": d for (u, v, d) in data.edges(data=True)},
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


def convert_plotly_object(obj: Any) -> Any:
    """Recursively convert Plotly objects to JSON-serializable dicts.
    If an object has a to_plotly_json() method, call it."""
    if hasattr(obj, "to_plotly_json"):
        result = obj.to_plotly_json()
        #current_app.logger.debug("Converting object %s, result: %s", obj, result)
        if result is None:
            current_app.logger.error("to_plotly_json returned None for object: %s", obj)
            return obj
        return result
    elif isinstance(obj, list):
        return [convert_plotly_object(item) for item in obj]
    elif isinstance(obj, dict):
        new_dict = {}
        for key, val in obj.items():
            new_dict[key] = convert_plotly_object(val)
        return new_dict
    elif isinstance(obj, (np.integer, np.int_)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj

# Alias for backward compatibility
def convert_plotly_fig(fig: dict) -> dict:
    """Convert the 'data' and 'layout' of a Plotly figure to dicts using to_plotly_json."""
    data = fig.get("data", [])
    layout = fig.get("layout", {})
    converted_data = [
        item.to_plotly_json() if hasattr(item, "to_plotly_json") else item
        for item in data
    ]
    converted_layout = layout.to_plotly_json() if hasattr(layout, "to_plotly_json") else layout
    return {"data": converted_data, "layout": converted_layout}

# Aliases for backward compatibility
convert_all_for_json = convert_for_json
convert_stats_for_json = convert_for_json
convert_dict_keys_to_str = convert_for_json
