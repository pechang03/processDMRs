# visualization.py
import plotly.graph_objs as go
from typing import List, Tuple, Set, Dict

def create_node_traces(graph: nx.Graph, bicliques: List[Tuple[Set[int], Set[int]]], biclique_number: int) -> go.Scatter:
    """
    Create node traces for visualization, coloring nodes based on their biclique membership.
    
    Args:
        graph: NetworkX graph representing the bipartite structure
        bicliques: List of tuples, each containing sets of DMR and gene nodes forming a biclique
        biclique_number: The index of the biclique to highlight
    
    Returns:
        A Plotly Scatter object representing the node trace
    """
    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            color='gray',  # Default color for invalid biclique number
            size=10,
            line_width=2
        )
    )

    if 0 <= biclique_number < len(bicliques):
        biclique = bicliques[biclique_number]
        node_trace.marker.color = ['red' if node in biclique[0] or node in biclique[1] else 'blue' for node in graph.nodes()]
    else:
        # If the biclique number is invalid, all nodes should be gray
        node_trace.marker.color = ['gray'] * len(graph.nodes())

    return node_trace
