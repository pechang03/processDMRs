"""Core visualization functionality"""

import json
from typing import Dict, List, Set, Tuple
from plotly.utils import PlotlyJSONEncoder

from sqlalchemy.orm import Session
from .graph_layout_biclique import CircularBicliqueLayout
from .graph_original_spring import SpringLogicalLayout
from utils.node_info import NodeInfo
from utils.edge_info import EdgeInfo
from .traces import (
    create_node_traces,
    create_edge_traces,
    create_biclique_boxes,
)
from .layout import create_visual_layout
from database.models import Component, Biclique, DMRTimepointAnnotation, GeneTimepointAnnotation


def generate_biclique_colors(num_bicliques: int) -> List[str]:
    """Generate distinct colors for bicliques"""
    colors = plotly.colors.qualitative.Set3 * (
        num_bicliques // len(plotly.colors.qualitative.Set3) + 1
    )
    return colors[:num_bicliques]


def create_biclique_visualization(
    bicliques: List[Tuple[Set[int], Set[int]]],
    node_labels: Dict[int, str],
    node_positions: Dict[int, Tuple[float, float]],
    node_biclique_map: Dict[int, List[int]],
    edge_classifications: Dict[str, List[EdgeInfo]],
    original_graph: nx.Graph,
    bipartite_graph: nx.Graph,
    original_node_positions: Dict[
        int, Tuple[float, float]
    ] = None,
    false_positive_edges: Set[Tuple[int, int]] = None,
    false_negative_edges: Set[Tuple[int, int]] = None,
    dominating_set: Set[int] = None,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
    edge_classification: Dict[str, Set[Tuple[int, int]]] = None,
) -> str:
    """Create interactive Plotly visualization with colored bicliques."""
    print(f"\nCreating visualization for {len(bicliques)} bicliques")  # Debug logging

    # Preprocess graphs for visualization

    processed_original = preprocess_graph_for_visualization(
        original_graph, remove_isolates=True, remove_bridges=False, keep_dmrs=True
    )

    processed_bipartite = preprocess_graph_for_visualization(
        bipartite_graph, remove_isolates=True, remove_bridges=False, keep_dmrs=True
    )

    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(bicliques))

    traces = []

    # Add biclique boxes first (so they appear behind other elements)
    biclique_box_traces = create_biclique_boxes(
        bicliques, node_positions, biclique_colors
    )
    traces.extend(biclique_box_traces)

    # Determine which node positions to use
    positions = original_node_positions if original_node_positions else node_positions

    # Create edge traces with EdgeInfo using the appropriate positions
    edge_traces = create_edge_traces(
        edge_classifications,
        positions,  # Use the selected positions
        node_labels,  # Add this required argument
        original_graph,  # Add this required argument
        edge_style={"width": 1},
    )
    traces.extend(edge_traces)
    edge_traces = create_edge_traces(
        bicliques,
        positions,  # Use the selected positions
        node_labels,  # Add this required argument
        original_graph,  # Add this required argument
        false_positive_edges,
        false_negative_edges,
        edge_type="biclique",
        edge_style={"color": "black", "width": 1, "dash": "solid"},
    )
    traces.extend(edge_traces)

    # Create NodeInfo object for node categorization
    all_nodes = set().union(
        *[dmr_nodes | gene_nodes for dmr_nodes, gene_nodes in bicliques]
    )
    dmr_nodes = set().union(*[dmr_nodes for dmr_nodes, _ in bicliques])
    gene_nodes = all_nodes - dmr_nodes
    split_genes = {
        node for node in gene_nodes if len(node_biclique_map.get(node, [])) > 1
    }
    regular_genes = gene_nodes - split_genes

    node_info = NodeInfo(
        all_nodes=all_nodes,
        dmr_nodes=dmr_nodes,
        regular_genes=regular_genes,
        split_genes=split_genes,
        node_degrees={node: len(node_biclique_map.get(node, [])) for node in all_nodes},
        min_gene_id=min(gene_nodes, default=0),
    )

    # Add nodes with proper styling
    node_traces = create_node_traces(
        node_info,
        node_positions,
        node_labels,
        node_biclique_map,
        biclique_colors,
        dominating_set,
        dmr_metadata,  # Pass these parameters
        gene_metadata,
    )
    traces.extend(node_traces)

    # Create layout
    layout = create_visual_layout(node_positions, node_info)

    # Create figure and convert to JSON
    fig = {"data": traces, "layout": layout}

    print(f"Created visualization with {len(traces)} traces")  # Debug logging
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def create_component_visualization(
    component_id: int,
    session: Session,
    node_positions: Dict[int, Tuple[float, float]] = None,
    layout_type: str = "circular"
) -> str:
    """Create visualization for a specific component.
    
    Args:
        component_id: Database ID of the component
        session: Database session
        node_positions: Optional pre-calculated node positions
        layout_type: Type of layout to use ('circular' or 'spring')
        
    Returns:
        JSON string containing Plotly visualization data
    """
    from database.models import Component, Biclique, DMRTimepointAnnotation, GeneTimepointAnnotation
    
    # Get component data from database
    component = session.query(Component).get(component_id)
    if not component:
        raise ValueError(f"Component {component_id} not found")
        
    # Get bicliques for this component
    bicliques = session.query(Biclique).filter_by(component_id=component_id).all()
    
    # Create node sets
    dmr_nodes = set()
    gene_nodes = set()
    for biclique in bicliques:
        dmr_nodes.update(biclique.dmr_ids)
        gene_nodes.update(biclique.gene_ids)
        
    # Get node metadata
    dmr_metadata = {}
    gene_metadata = {}
    
    dmr_annotations = session.query(DMRTimepointAnnotation).filter(
        DMRTimepointAnnotation.dmr_id.in_(dmr_nodes),
        DMRTimepointAnnotation.timepoint_id == component.timepoint_id
    ).all()
    
    gene_annotations = session.query(GeneTimepointAnnotation).filter(
        GeneTimepointAnnotation.gene_id.in_(gene_nodes),
        GeneTimepointAnnotation.timepoint_id == component.timepoint_id
    ).all()
    
    # Create node labels
    node_labels = {}
    for dmr in dmr_annotations:
        node_labels[dmr.dmr_id] = f"DMR_{dmr.dmr_id}"
        dmr_metadata[dmr.dmr_id] = {
            "degree": dmr.degree,
            "type": dmr.node_type,
            "bicliques": dmr.biclique_ids
        }
        
    for gene in gene_annotations:
        node_labels[gene.gene_id] = f"Gene_{gene.gene_id}"
        gene_metadata[gene.gene_id] = {
            "degree": gene.degree,
            "type": gene.node_type,
            "gene_type": gene.gene_type,
            "bicliques": gene.biclique_ids
        }
    
    # Create node biclique map
    node_biclique_map = {}
    for idx, biclique in enumerate(bicliques):
        for dmr_id in biclique.dmr_ids:
            if dmr_id not in node_biclique_map:
                node_biclique_map[dmr_id] = []
            node_biclique_map[dmr_id].append(idx)
            
        for gene_id in biclique.gene_ids:
            if gene_id not in node_biclique_map:
                node_biclique_map[gene_id] = []
            node_biclique_map[gene_id].append(idx)
    
    # Calculate positions if not provided
    if not node_positions:
        if layout_type == "circular":
            layout = CircularBicliqueLayout()
        else:
            layout = SpringLogicalLayout()
            
        node_info = NodeInfo(
            all_nodes=dmr_nodes | gene_nodes,
            dmr_nodes=dmr_nodes,
            regular_genes={g for g in gene_nodes if len(node_biclique_map.get(g, [])) <= 1},
            split_genes={g for g in gene_nodes if len(node_biclique_map.get(g, [])) > 1},
            node_degrees={n: len(node_biclique_map.get(n, [])) for n in (dmr_nodes | gene_nodes)},
            min_gene_id=min(gene_nodes) if gene_nodes else 0
        )
        
        node_positions = layout.calculate_positions(
            graph=nx.Graph(),  # Empty graph since we have node sets
            node_info=node_info
        )
    
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(bicliques))
    
    # Create visualization
    return create_biclique_visualization(
        bicliques=[(set(b.dmr_ids), set(b.gene_ids)) for b in bicliques],
        node_labels=node_labels,
        node_positions=node_positions,
        node_biclique_map=node_biclique_map,
        edge_classifications={},  # Add edge classifications if needed
        original_graph=nx.Graph(),  # Add actual graph if needed
        bipartite_graph=nx.Graph(),  # Add actual graph if needed
        dmr_metadata=dmr_metadata,
        gene_metadata=gene_metadata
    )
