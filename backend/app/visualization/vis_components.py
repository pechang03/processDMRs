"""Component visualization functionality"""

from typing import Dict, List, Set, Tuple, Any
from flask import current_app

from .traces import create_edge_traces, create_dmr_trace, create_unified_gene_trace
from .layout import create_circular_layout
from .core import generate_biclique_colors
from backend.app.utils.node_info import NodeInfo
from backend.app.biclique_analysis.classifier import classify_biclique
from .traces import create_node_traces, create_edge_traces
from .layout import create_circular_layout


def create_component_visualization(
    component: Dict,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    edge_classifications: Dict[str, List],
    dmr_metadata: Dict = None,
    gene_metadata: Dict = None,
) -> Dict:
    """Create visualization data for a component with centralized shape configuration."""
    """Create visualization data for a component."""

    # Get nodes from component
    dmr_nodes = {n for n in component["component"] if n in component.get("dmrs", set())}
    gene_nodes = {n for n in component["component"] if n not in dmr_nodes}
    split_genes = {n for n in gene_nodes if len(node_biclique_map.get(n, [])) > 1}

    # Create NodeInfo object
    node_info = NodeInfo(
        all_nodes=dmr_nodes | gene_nodes,
        dmr_nodes=dmr_nodes,
        regular_genes=gene_nodes - split_genes,
        split_genes=split_genes,
        node_degrees={
            node: len(node_biclique_map.get(node, []))
            for node in (dmr_nodes | gene_nodes)
        },
        min_gene_id=min(gene_nodes) if gene_nodes else 0,
    )

    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(component.get("raw_bicliques", [])))
    # current_app.logger.debug("Point 3")

    # Create traces with edges first (drawn underneath), then nodes (drawn on top)
    traces = []
    # Add edge traces first
    edge_traces = create_edge_traces(
        edge_classifications,
        node_positions,
        node_labels,
        component["component"],
        split_genes,
        edge_style={"width": 1, "color": "gray"},
    )
    traces.extend(edge_traces)

    # Get dominating set from explicit data or metadata
    dominating_set = set()
    if dmr_metadata and "dominating_sets" in component:
        # Get from explicit dominating set first
        dominating_set = {int(dmr_id) for dmr_id in component["dominating_sets"]}

        # Fallback to metadata if empty
        if not dominating_set:
            dominating_set = {
                int(dmr_id)
                for dmr_id, info in dmr_metadata.items()
                if info.get("node_type", "").lower() == "hub"
            }

    current_app.logger.debug(f"Final dominating set: {dominating_set}")

    # Add DMR trace
    dmr_trace = create_dmr_trace(
        dmr_nodes=node_info.dmr_nodes,
        node_positions=node_positions,
        node_labels=node_labels,
        node_biclique_map=node_biclique_map,
        biclique_colors=biclique_colors,
        dominating_set=dominating_set,
        dmr_metadata=dmr_metadata,
    )
    if dmr_trace:
        traces.append(dmr_trace)

    # current_app.logger.debug("Point 3b")
    # Add gene traces using unified function
    gene_trace = create_unified_gene_trace(
        gene_nodes,  # All genes now
        node_positions,
        node_labels,
        node_biclique_map,
        biclique_colors,
        gene_metadata,
    )
    if gene_trace:
        traces.append(gene_trace)

    # current_app.logger.debug("Point 4")
    # Unified gene trace now handles both regular and split genes
    # split_gene_trace = create_unified_gene_trace(
    #     node_info.split_genes,
    #     node_positions,
    #     node_labels,
    #     node_biclique_map,
    #     biclique_colors,
    #     gene_metadata,
    #     is_split=True,
    # )
    # if split_gene_trace:
    #     traces.append(split_gene_trace)

    # current_app.logger.debug("Point 5")
    # Create layout using the unified layout function
    layout = create_circular_layout(node_info)

    return {
        "data": [trace.to_plotly_json() for trace in traces],  # Convert Scatter to dict
        "layout": layout.to_plotly_json()
        if hasattr(layout, "to_plotly_json")
        else layout,
    }


def create_component_details(
    component: Dict, dmr_metadata: Dict = None, gene_metadata: Dict = None
) -> Dict:
    """
    Create detailed information about a component.

    Args:
        component: Component data dictionary
        dmr_metadata: Optional metadata for DMR nodes
        gene_metadata: Optional metadata for gene nodes

    Returns:
        Dictionary containing detailed component information
    """
    # Identify split genes
    split_genes = []
    if "raw_bicliques" in component:
        # Track gene participation across bicliques
        gene_participation = {}
        for biclique in component["raw_bicliques"]:
            for gene in biclique[1]:
                if gene not in gene_participation:
                    gene_participation[gene] = []
                gene_participation[gene].append(biclique)

        # Find genes in multiple bicliques
        for gene, bicliques in gene_participation.items():
            if len(bicliques) > 1:
                gene_name = next(
                    (k for k, v in gene_metadata.items() if v.get("id") == gene),
                    f"Gene_{gene}",
                )
                split_genes.append(
                    {
                        "gene_name": gene_name,
                        "description": gene_metadata.get(gene_name, {}).get(
                            "description", "N/A"
                        ),
                        "bicliques": [
                            f"Biclique {component['raw_bicliques'].index(b)+1}"
                            for b in bicliques
                        ],
                    }
                )

    return {
        "split_genes": split_genes,
        "total_genes": len(component.get("genes", [])),
        "total_dmrs": len(component.get("dmrs", [])),
        "total_edges": component.get("total_edges", 0),
    }
from typing import Dict, List, Set, Tuple, Optional
import plotly.graph_objects as go
from ..core.data_loader import create_bipartite_graph
from ..visualization.traces import NODE_SHAPES, create_node_trace, create_edge_trace
from ..visualization.colors import get_biclique_colors, get_edge_colors

def create_component_visualization(
    component: Dict,
    node_positions: Dict,
    node_labels: Dict,
    node_biclique_map: Dict,
    edge_classifications: Dict,
    dmr_metadata: Dict,
    gene_metadata: Dict,
) -> Dict:
    """Create visualization data for a component."""
    # Get color mappings
    biclique_colors = get_biclique_colors(len(component.get('raw_bicliques', [])))
    edge_colors = get_edge_colors()

    # Create node traces for DMRs and genes
    dmr_traces = []
    gene_traces = []
    edge_traces = []

    # Process nodes
    for node_id in component['component']:
        is_dmr = node_id in component['dmrs']
        pos = node_positions.get(node_id, {'x': 0, 'y': 0})
        
        # Get node properties
        if is_dmr:
            info = dmr_metadata.get(node_id, {})
            is_hub = info.get('is_hub', False)
            shape = NODE_SHAPES['dmr_hub'] if is_hub else NODE_SHAPES['dmr']
            trace = create_node_trace([pos['x']], [pos['y']], shape, 'blue', node_labels.get(node_id, f'DMR_{node_id}'))
            dmr_traces.append(trace)
        else:
            info = gene_metadata.get(node_id, {})
            is_split = info.get('is_split', False)
            shape = NODE_SHAPES['gene_split'] if is_split else NODE_SHAPES['gene']
            trace = create_node_trace([pos['x']], [pos['y']], shape, 'red', node_labels.get(node_id, f'Gene_{node_id}'))
            gene_traces.append(trace)

    # Process edges
    for edge_type, edges in edge_classifications.items():
        color = edge_colors.get(edge_type, 'gray')
        for edge in edges:
            start_id, end_id = edge.edge
            start_pos = node_positions.get(start_id, {'x': 0, 'y': 0})
            end_pos = node_positions.get(end_id, {'x': 0, 'y': 0})
            trace = create_edge_trace(
                [start_pos['x'], end_pos['x']],
                [start_pos['y'], end_pos['y']],
                color
            )
            edge_traces.append(trace)

    # Create legend-only traces
    legend_traces = []
    
    # DMR legend entries
    legend_traces.append({
        'x': [None],
        'y': [None],
        'mode': 'markers',
        'marker': {
            'symbol': NODE_SHAPES['dmr_hub'],
            'size': 12,
            'color': 'blue'
        },
        'name': 'Hub DMRs',
        'showlegend': True,
        'legendgroup': 'dmr'
    })
    
    legend_traces.append({
        'x': [None],
        'y': [None],
        'mode': 'markers',
        'marker': {
            'symbol': NODE_SHAPES['dmr'],
            'size': 10,
            'color': 'blue'
        },
        'name': 'DMRs',
        'showlegend': True,
        'legendgroup': 'dmr'
    })

    # Gene legend entries
    legend_traces.append({
        'x': [None],
        'y': [None],
        'mode': 'markers',
        'marker': {
            'symbol': NODE_SHAPES['gene_split'],
            'size': 10,
            'color': 'red'
        },
        'name': 'Split Genes',
        'showlegend': True,
        'legendgroup': 'gene'
    })

    legend_traces.append({
        'x': [None],
        'y': [None],
        'mode': 'markers',
        'marker': {
            'symbol': NODE_SHAPES['gene'],
            'size': 10,
            'color': 'red'
        },
        'name': 'Genes',
        'showlegend': True,
        'legendgroup': 'gene'
    })

    # Add biclique legend entries if there are multiple bicliques
    if len(component.get('raw_bicliques', [])) > 1:
        for idx, color in enumerate(biclique_colors):
            legend_traces.append({
                'x': [None],
                'y': [None],
                'mode': 'markers',
                'marker': {
                    'symbol': 'circle',
                    'size': 10,
                    'color': color
                },
                'name': f'Biclique {idx + 1}',
                'showlegend': True,
                'legendgroup': f'biclique_{idx + 1}'
            })

    # Combine all traces
    all_traces = edge_traces + dmr_traces + gene_traces + legend_traces

    return {
        'data': all_traces,
        'layout': {
            'showlegend': True,
            'hovermode': 'closest',
            'margin': {'b': 40, 'l': 40, 'r': 40, 't': 40},
            'xaxis': {'showgrid': False, 'zeroline': False, 'showticklabels': False},
            'yaxis': {'showgrid': False, 'zeroline': False, 'showticklabels': False},
            'legend': {
                'x': 1.05,
                'y': 0.5,
                'xanchor': 'left',
                'yanchor': 'middle',
                'bgcolor': 'rgba(255,255,255,0.8)',
                'bordercolor': 'rgba(0,0,0,0.2)',
                'borderwidth': 1
            }
        }
    }
