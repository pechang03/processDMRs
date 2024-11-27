"""Component visualization functionality"""

from typing import Dict, List, Set, Tuple
import json
from plotly.utils import PlotlyJSONEncoder

from .traces import (
    create_node_traces,
    create_edge_traces,
    create_biclique_boxes
)
from .layout import create_plot_layout
from .core import generate_biclique_colors
from utils.node_info import NodeInfo
from biclique_analysis.classifier import classify_biclique
from biclique_analysis.classifier import classify_biclique

def create_component_visualization(
    component: Dict,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    edge_classifications: Dict[str, List],
    dmr_metadata: Dict = None,
    gene_metadata: Dict = None,
) -> Dict:
    """
    Create visualization data for a component.
    
    Args:
        component: Component data dictionary
        node_positions: Dictionary mapping node IDs to (x,y) coordinates
        node_labels: Dictionary mapping node IDs to display labels
        node_biclique_map: Dictionary mapping nodes to their biclique indices
        edge_classifications: Edge classification results
        dmr_metadata: Optional metadata for DMR nodes
        gene_metadata: Optional metadata for gene nodes
        
    Returns:
        Dictionary containing Plotly visualization data
    """
    # Get nodes from component
    dmr_nodes = {n for n in component["component"] if n in component.get("dmrs", set())}
    gene_nodes = {n for n in component["component"] if n not in dmr_nodes}
    
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(component.get("raw_bicliques", [])))
    
    # Create node traces
    node_traces = create_node_traces(
        dmr_nodes=dmr_nodes,
        gene_nodes=gene_nodes,
        node_positions=node_positions,
        node_labels=node_labels,
        node_biclique_map=node_biclique_map,
        biclique_colors=biclique_colors,
        dmr_metadata=dmr_metadata,
        gene_metadata=gene_metadata
    )
    
    # Create edge traces
    edge_traces = create_edge_traces(
        component["component"],
        node_positions,
        edge_classifications,
        node_biclique_map,
        biclique_colors
    )
    
    # Create biclique box traces if component has raw_bicliques
    box_traces = []
    if "raw_bicliques" in component:
        box_traces = create_biclique_boxes(
            component["raw_bicliques"],
            node_positions,
            biclique_colors
        )
    
    # Combine all traces
    traces = [*node_traces, *edge_traces, *box_traces]
    
    # Create layout
    layout = create_plot_layout(
        title=f"Component {component['id']} Visualization",
        node_positions=node_positions
    )
    
    return {
        "data": traces,
        "layout": layout
    }

def create_component_details(
    component: Dict,
    dmr_metadata: Dict = None,
    gene_metadata: Dict = None
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
                gene_name = next((k for k, v in gene_metadata.items() if v.get('id') == gene), f"Gene_{gene}")
                split_genes.append({
                    "gene_name": gene_name,
                    "description": gene_metadata.get(gene_name, {}).get('description', 'N/A'),
                    "bicliques": [f"Biclique {component['raw_bicliques'].index(b)+1}" for b in bicliques]
                })
    
    return {
        "split_genes": split_genes,
        "total_genes": len(component.get("genes", [])),
        "total_dmrs": len(component.get("dmrs", [])),
        "total_edges": component.get("total_edges", 0)
    }


