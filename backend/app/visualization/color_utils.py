"""Color utility functions for visualization."""

import re
import numpy as np

def get_rgb_arr(color_string: str) -> np.ndarray:
    """Convert color string to RGB array."""
    if color_string.startswith('#'):
        return np.array([
            int(color_string[1:3], 16),
            int(color_string[3:5], 16),
            int(color_string[5:7], 16)
        ])
    
    rgb_match = re.match(r'rgb\((\d+),(\d+),(\d+)\)', color_string)
    if rgb_match:
        return np.array([int(x) for x in rgb_match.groups()])
        
    rgba_match = re.match(r'rgba\((\d+),(\d+),(\d+),[\d.]+\)', color_string)
    if rgba_match:
        return np.array([int(x) for x in rgba_match.groups()])
        
    return np.array([127, 127, 127])

def get_rgba_str(rgb_arr: np.ndarray, alpha: float = 1.0) -> str:
    """Convert RGB array to RGBA string in Plotly's format (no spaces)."""
    return f"rgba({int(rgb_arr[0])},{int(rgb_arr[1])},{int(rgb_arr[2])},{alpha})"

def get_rgb_str(rgb_arr: np.ndarray) -> str:
    """Convert RGB array to RGB string in Plotly's format (no spaces)."""
    return f"rgb({int(rgb_arr[0])},{int(rgb_arr[1])},{int(rgb_arr[2])})"
