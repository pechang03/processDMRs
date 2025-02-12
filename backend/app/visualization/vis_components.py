"""Component visualization functionality"""

from typing import Dict, List, Set, Tuple, Any
from flask import current_app
from .color_utils import get_rgba_str

from .traces import (
    create_edge_traces,
    create_dmr_trace,
    create_unified_gene_trace,
    # split_genes,
    create_biclique_boxes,
)
from .layout import create_circular_layout
from .core import generate_biclique_colors
from backend.app.utils.node_info import NodeInfo
from backend.app.utils.json_utils import convert_plotly_object
from backend.app.biclique_analysis.classifier import classify_biclique
from .traces import (
    create_edge_traces,
    create_legend_traces,
)


def create_component_visualization(
    component: Dict,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    edge_classifications: Dict[str, Any],
    dmr_metadata: Dict = None,
    gene_metadata: Dict = None,
    timepoint_id: int = 1,
) -> Dict:
    """Create visualization data for a component with centralized shape configuration."""
    """Create visualization data for a component."""

    # Extract classifications and stats from edge_classifications
    if "classifications" in edge_classifications:
        classifications = edge_classifications["classifications"]
    else:
        classifications = edge_classifications
        current_app.logger.debug("Using edge_classifications directly")

    # Get or compute stats
    stats = edge_classifications.get("stats")
    if stats is None:
        current_app.logger.debug("Stats was None")
        stats = {
            "component": {
                "permanent VC": len(classifications.get("permanent", [])),
                "false_positive VC": len(classifications.get("false_positive", [])),
                "false_negative VC": len(classifications.get("false_negative", [])),
            },
            "bicliques": {},
        }

    # Extract nodes from the component data
    dmr_nodes = set(component.get("dmrs", []))
    gene_nodes = set(component.get("genes", []))

    # Define split_genes as those gene nodes that participate in more than one biclique
    split_genes_ids = set(
        {n for n in gene_nodes if len(node_biclique_map.get(n, [])) > 1}
    )
    regular_gene_ids = gene_nodes - split_genes_ids
    #current_app.logger.debug(f"CV point 1 dmrs {dmr_nodes}")
    #current_app.logger.debug(f"CV point 1 genes {gene_nodes}")
    # Create NodeInfo object
    node_info = NodeInfo(
        all_nodes=dmr_nodes | gene_nodes,
        dmr_nodes=dmr_nodes,
        regular_genes=regular_gene_ids,
        split_genes=split_genes_ids,
        node_degrees={
            node: len(node_biclique_map.get(node, []))
            for node in (dmr_nodes | gene_nodes)
        },
        min_gene_id=min(gene_nodes) if gene_nodes else 0,
    )

    #current_app.logger.debug("CV point 2")
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(component.get("raw_bicliques", [])))
    # current_app.logger.debug("Point 3")

    # Create traces list and get biclique shapes
    traces = []
    biclique_shapes = create_biclique_boxes(
        component.get("raw_bicliques", []), node_positions, biclique_colors
    )

    #current_app.logger.debug("CV point 3")
    # Add legend traces
    legend_nodes, legend_edges = create_legend_traces(biclique_colors)
    traces.extend(legend_nodes)
    traces.extend(legend_edges)

    # Log edge_classifications structure and content for debugging
    #current_app.logger.debug(
    #    "Edge Classifications Structure: %s", type(edge_classifications)
    #)
    #current_app.logger.debug(
    #    "Edge Classifications Keys: %s", edge_classifications.keys()
    #)
    #current_app.logger.debug("Edge Classifications Content: %s", edge_classifications)
    #current_app.logger.debug("Classifications Content: %s", classifications)

    # Add edge traces using the previously computed split_genes
    edge_traces = create_edge_traces(
        edge_classifications=classifications,  # Use the extracted classifications dict
        node_positions=node_positions,
        node_labels=node_labels,
        component_nodes=dmr_nodes | gene_nodes,
        split_genes=split_genes_ids,
        edge_style={"width": 1, "color": "gray"},
    )
    traces.extend(edge_traces)

    #current_app.logger.debug("CV point 4")
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

    #current_app.logger.debug(f"Final dominating set: {dominating_set}")

    # Add DMR trace
    dmr_trace = create_dmr_trace(
        dmr_nodes=node_info.dmr_nodes,
        node_positions=node_positions,
        node_labels=node_labels,
        node_biclique_map=node_biclique_map,
        biclique_colors=biclique_colors,
        timepoint_id=timepoint_id,
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

    # Create layout using the unified layout function and add biclique shapes
    layout = create_circular_layout(node_info)
    layout["shapes"] = biclique_shapes

    current_app.logger.debug("Number of traces: %d", len(traces))
    #current_app.logger.debug("Layout content: %s", layout)

    final_fig = {"data": traces, "layout": layout}
    final_fig["edge_stats"] = stats.get("component", {})
    final_fig["biclique_stats"] = stats.get("bicliques", {})
    converted_fig = convert_plotly_object(final_fig)
    if converted_fig is None:
        converted_fig = final_fig
    #current_app.logger.debug("Final converted figure: %s", converted_fig)
    return converted_fig
