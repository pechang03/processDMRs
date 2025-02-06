"""Component visualization functionality"""

from typing import Dict, List, Set, Tuple, Any
from flask import current_app

from .traces import create_edge_traces, create_dmr_trace, create_unified_gene_trace, split_genes
from .layout import create_circular_layout
from .core import generate_biclique_colors
from backend.app.utils.node_info import NodeInfo
from backend.app.biclique_analysis.classifier import classify_biclique
from .traces import create_node_traces, create_edge_traces, create_legend_traces, NODE_SHAPES
from .layout import create_circular_layout
from backend.app.utils.json_utils import convert_plotly_object


def create_component_visualization(
    component: Dict,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    edge_classifications: Dict[str, Any],
    dmr_metadata: Dict = None,
    gene_metadata: Dict = None,
) -> Dict:
    """Create visualization data for a component with centralized shape configuration."""
    """Create visualization data for a component."""

    # Extract classifications and stats from edge_classifications
    if "classifications" in edge_classifications:
        classifications = edge_classifications["classifications"]
    else:
        classifications = edge_classifications

    # Get or compute stats
    stats = edge_classifications.get("stats")
    if stats is None:
        stats = {
            "component": {
                "permanent": len(classifications.get("permanent", [])),
                "false_positive": len(classifications.get("false_positive", [])),
                "false_negative": len(classifications.get("false_negative", [])),
            },
            "bicliques": {},
        }

    # Extract nodes from the component data
    dmr_nodes = {n for n in component.get("component", set()) if n in set(component.get("dmrs", []))}
    gene_nodes = {n for n in component.get("component", set()) if n not in set(component.get("dmrs", []))}
    # Define split_genes as those gene nodes that participate in more than one biclique
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
    
    # Add edge traces using the previously computed split_genes
    edge_traces = create_edge_traces(
        edge_classifications,
        node_positions,
        node_labels,
        component["component"],
        split_genes=split_genes,  # Use explicit keyword argument
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

    from backend.app.utils.json_utils import convert_plotly_object
    final_fig = {'data': traces, 'layout': layout}
    
    # Add stats to the visualization
    final_fig["edge_stats"] = stats.get("component", {})
    final_fig["biclique_stats"] = stats.get("bicliques", {})
    
    converted_fig = convert_plotly_object(final_fig)
    if converted_fig is None:
        converted_fig = final_fig
    return converted_fig


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

    # Create edge traces
    edge_traces = create_edge_traces(
        edge_classifications,
        node_positions,
        node_labels,
        component["component"],
        split_genes,
        edge_style={"width": 1, "color": "gray"}
    )

    # Get legend traces from helper function
    from .traces import create_legend_traces
    legend_node_traces, legend_edge_traces = create_legend_traces()

