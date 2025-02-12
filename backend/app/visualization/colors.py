"""Color utilities for visualization"""

from .core import generate_biclique_colors

def get_biclique_colors(num_bicliques):
    """
    Return a list of colors for the given number of bicliques.
    Uses generate_biclique_colors from core.
    """
    return generate_biclique_colors(num_bicliques)

def get_edge_colors():
    """
    Return a mapping from edge type to color.
    """
    return {
        "permanent": "rgb(119,119,119)", 
        "false_positive": "rgb(255,0,0)",
        "false_negative": "rgb(0,0,255)"
    }
