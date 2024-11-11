"""Node trace creation functionality"""

from typing import Dict, List, Tuple
import plotly.graph_objs as go
from node_info import NodeInfo

def create_node_traces(
    node_info: NodeInfo,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    biclique_colors: List[str]
) -> List[go.Scatter]:
    """Create node traces with proper styling based on node type."""
    traces = []
    
    # Create separate traces for DMRs and genes
    dmr_x, dmr_y, dmr_colors, dmr_text = [], [], [], []
    gene_x, gene_y, gene_colors, gene_text = [], [], [], []
    
    for node in node_info.all_nodes:
        pos = node_positions[node]
        # Get node color based on its biclique membership
        biclique_nums = node_biclique_map.get(node, [])
        # Use first biclique color if node belongs to any biclique, otherwise gray
        if biclique_nums and biclique_nums[0] <= len(biclique_colors):
            color = biclique_colors[biclique_nums[0]-1]
        else:
            color = "gray"
        
        if node in node_info.dmr_nodes:
            dmr_x.append(pos[0])
            dmr_y.append(pos[1])
            dmr_colors.append(color)
            dmr_text.append(node_labels.get(node, f"DMR_{node}"))
        else:
            gene_x.append(pos[0])
            gene_y.append(pos[1])
            gene_colors.append(color)
            gene_text.append(node_labels.get(node, f"Gene_{node}"))
    
    # Add DMR nodes
    if dmr_x:
        traces.append(go.Scatter(
            x=dmr_x,
            y=dmr_y,
            mode="markers+text",
            marker=dict(size=10, color=dmr_colors, line=dict(color="black", width=1)),
            text=dmr_text,
            textposition="middle left",
            hoverinfo="text",
            name="DMRs"
        ))
    
    # Add gene nodes
    if gene_x:
        traces.append(go.Scatter(
            x=gene_x,
            y=gene_y,
            mode="markers+text",
            marker=dict(
                size=10,
                color=gene_colors,
                symbol="diamond",
                line=dict(color="black", width=1)
            ),
            text=gene_text,
            textposition="middle right",
            hoverinfo="text",
            name="Genes"
        ))
    
    return traces
