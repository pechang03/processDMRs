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
    return data
