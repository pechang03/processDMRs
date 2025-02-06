"""Component visualization functionality"""

from typing import Dict, List, Set, Tuple, Any
from flask import current_app

from .traces import (
    create_edge_traces,
    create_dmr_trace,
    create_unified_gene_trace,
    split_genes,
    create_biclique_boxes,
)
from .layout import create_circular_layout
from .core import generate_biclique_colors
from backend.app.utils.node_info import NodeInfo
from backend.app.biclique_analysis.classifier import classify_biclique
from .traces import (
    create_node_traces,
    create_edge_traces,
    create_legend_traces,
    NODE_SHAPES,
)
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
    dmr_nodes = {
        n
        for n in component.get("component", set())
        if n in set(component.get("dmrs", []))
    }
    gene_nodes = {
        n
        for n in component.get("component", set())
        if n not in set(component.get("dmrs", []))
    }
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

    # Create traces list and get biclique shapes
    traces = []
    biclique_shapes = create_biclique_boxes(
        component.get("raw_bicliques", []),
        node_positions,
        biclique_colors
    )
    
    # Add legend traces
    legend_nodes, legend_edges = create_legend_traces(biclique_colors)
    traces.extend(legend_nodes)
    traces.extend(legend_edges)

    # Log edge_classifications structure and content for debugging
    current_app.logger.debug("Edge Classifications Structure: %s", type(edge_classifications))
    current_app.logger.debug("Edge Classifications Keys: %s", edge_classifications.keys())
    current_app.logger.debug("Edge Classifications Content: %s", edge_classifications)
    current_app.logger.debug("Classifications Content: %s", classifications)
    
    # Add edge traces using the previously computed split_genes
    edge_traces = create_edge_traces(
        classifications,    # Use the extracted 'classifications' dict
        node_positions,
        node_labels,
        component["component"],
        split_genes=split_genes,
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
    # Create layout using the unified layout function and add biclique shapes
    layout = create_circular_layout(node_info)
    layout["shapes"] = biclique_shapes

    from backend.app.utils.json_utils import convert_plotly_object

    current_app.logger.debug("Number of traces: %d", len(traces))
    current_app.logger.debug("Layout content: %s", layout)

    final_fig = {"data": traces, "layout": layout}
    final_fig["edge_stats"] = stats.get("component", {})
    final_fig["biclique_stats"] = stats.get("bicliques", {})
    converted_fig = convert_plotly_object(final_fig)
    if converted_fig is None:
        converted_fig = final_fig
    current_app.logger.debug("Final converted figure: %s", converted_fig)
    return converted_fig

