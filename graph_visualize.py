"""
Functions for visualizing bicliques using Matplotlib and TikZplotlib
"""

from visualization.core import create_biclique_visualization


def create_dmr_table(dmr_metadata: Dict[str, Dict]) -> go.Table:
    """Create a Plotly table for DMR metadata."""
    headers = ["DMR", "Area", "Bicliques"]
    rows = [
        [
            dmr,
            metadata.get("area", "N/A"),
            ", ".join(map(str, metadata.get("bicliques", []))),
        ]
        for dmr, metadata in dmr_metadata.items()
    ]
    return go.Table(header=dict(values=headers), cells=dict(values=list(zip(*rows))))


def create_gene_table(
    gene_metadata: Dict[str, Dict],
    gene_id_mapping: Dict[str, int],
    node_biclique_map: Dict[int, List[int]],
) -> go.Table:
    """Create a Plotly table for gene metadata."""
    headers = ["Gene", "Description", "Bicliques"]
    rows = [
        [
            gene,
            metadata.get("description", "N/A"),
            ", ".join(map(str, node_biclique_map.get(gene_id_mapping[gene], []))),
        ]
        for gene, metadata in gene_metadata.items()
    ]
    return go.Table(header=dict(values=headers), cells=dict(values=list(zip(*rows))))



def create_node_biclique_map(
    bicliques: List[Tuple[Set[int], Set[int]]],
) -> Dict[int, List[int]]:
    """
    Create mapping of nodes to their biclique numbers.

    Args:
        bicliques: List of (dmr_nodes, gene_nodes) tuples

    Returns:
        Dictionary mapping node IDs to list of biclique numbers they belong to
    """
    node_biclique_map = {}

    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        for node in dmr_nodes | gene_nodes:
            if node not in node_biclique_map:
                node_biclique_map[node] = []
            node_biclique_map[node].append(biclique_idx + 1)

    return node_biclique_map


def generate_biclique_colors(num_bicliques: int) -> List[str]:
    """Generate distinct colors for bicliques"""
    import plotly.colors

    colors = plotly.colors.qualitative.Set3 * (
        num_bicliques // len(plotly.colors.qualitative.Set3) + 1
    )
    return colors[:num_bicliques]
def create_biclique_boxes(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]],
    biclique_colors: List[str]
) -> List[go.Scatter]:
    """Create box traces around bicliques."""
    traces = []
    for biclique_idx, (dmr_nodes, gene_nodes) in enumerate(bicliques):
        nodes = dmr_nodes | gene_nodes
        if not nodes:
            continue
            
        x_coords = [node_positions[n][0] for n in nodes]
        y_coords = [node_positions[n][1] for n in nodes]
        
        padding = 0.05
        x_min, x_max = min(x_coords) - padding, max(x_coords) + padding
        y_min, y_max = min(y_coords) - padding, max(y_coords) + padding
        
        traces.append(go.Scatter(
            x=[x_min, x_max, x_max, x_min, x_min],
            y=[y_min, y_min, y_max, y_max, y_min],
            mode="lines",
            line=dict(color=biclique_colors[biclique_idx], width=2, dash="dot"),
            fill="toself",
            fillcolor=biclique_colors[biclique_idx],
            opacity=0.1,
            name=f"Biclique {biclique_idx + 1}",
            showlegend=True
        ))
    return traces

def create_biclique_edges(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_positions: Dict[int, Tuple[float, float]]
) -> List[go.Scatter]:
    """Create edge traces for all bicliques."""
    traces = []
    for dmr_nodes, gene_nodes in bicliques:
        for dmr in dmr_nodes:
            for gene in gene_nodes:
                traces.append(go.Scatter(
                    x=[node_positions[dmr][0], node_positions[gene][0]],
                    y=[node_positions[dmr][1], node_positions[gene][1]],
                    mode="lines",
                    line=dict(width=1, color="gray"),
                    hoverinfo="none",
                    showlegend=False
                ))
    return traces
