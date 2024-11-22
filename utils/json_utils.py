"""Utility functions for JSON serialization."""

import numpy as np
from typing import Any, Dict, List, Set, Tuple


def convert_for_json(data: Any) -> Any:
    """
    Recursively convert data structures to JSON-serializable formats.

    Handles:
    - Numpy types (int, float, arrays)
    - Sets (converted to sorted lists)
    - Tuples (converted to lists)
    - Nested dictionaries and lists
    - Dictionaries with tuple keys (converted to string keys)

    Args:
        data: Input data to convert

    Returns:
        JSON-serializable version of the input data
    """
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
    elif isinstance(data, (np.floating, np.float_)):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    return data


def convert_stats_for_json(stats):
    """Convert dictionary with tuple keys to use string keys for JSON serialization."""
    if isinstance(stats, dict):
        return {
            str(k) if isinstance(k, tuple) else k: convert_stats_for_json(v)
            for k, v in stats.items()
        }
    elif isinstance(stats, list):
        return [convert_stats_for_json(x) for x in stats]
    elif isinstance(stats, set):
        return list(stats)  # Convert sets to lists
    return stats


def convert_for_json(data):
    """Convert data structures for JSON serialization."""
    if isinstance(data, dict):
        return {
            "_".join(map(str, k)) if isinstance(k, tuple) else str(k): convert_for_json(
                v
            )
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [convert_for_json(i) for i in data]
    elif isinstance(data, set):
        return sorted(list(data))
    elif isinstance(data, tuple):
        return list(data)
    return data


def convert_all_for_json(data):
    """Comprehensive conversion of all data types for JSON serialization."""

    if isinstance(data, dict):
        return {
            str(k) if isinstance(k, tuple) else k: convert_all_for_json(v)
            for k, v in data.items()
        }
    elif isinstance(data, (list, tuple)):
        return [convert_all_for_json(i) for i in data]
    elif isinstance(data, set):
        return sorted(list(data))
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    return data
