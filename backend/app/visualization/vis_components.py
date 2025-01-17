"""Component visualization functionality"""

from typing import Dict, List, Set, Tuple, Union, Any
import json
from plotly.utils import PlotlyJSONEncoder

from .traces import (
    create_node_traces,
    create_edge_traces,
    create_biclique_boxes,
    create_dmr_trace,
    create_gene_trace,
    create_split_gene_trace
)
from .layout import create_plot_layout
from .core import generate_biclique_colors
from backend.app.utils.node_info import NodeInfo
from backend.app.biclique_analysis.classifier import classify_biclique
from backend.app.biclique_analysis.classifier import classify_biclique

def create_component_visualization(
    component: Dict,
    node_positions: Dict[int, Tuple[float, float]],
    node_labels: Dict[int, str],
    node_biclique_map: Dict[int, List[int]],
    edge_classifications: Dict[str, List],
    dmr_metadata: Dict = None,
    gene_metadata: Dict = None,
) -> Dict:
    """Create visualization data for a component."""
    from .traces import create_node_traces, create_edge_traces
    from .layout import create_circular_layout
    
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
        node_degrees={node: len(node_biclique_map.get(node, [])) for node in (dmr_nodes | gene_nodes)},
        min_gene_id=min(gene_nodes) if gene_nodes else 0
    )
    
    # Generate colors for bicliques
    biclique_colors = generate_biclique_colors(len(component.get("raw_bicliques", [])))
    
    # Create traces using the unified trace creation functions
    traces = []
    
    # Create traces using the centralized trace creation functions
    traces = []
    
    # Get dominating set from component metadata
    dominating_set = set()
    if dmr_metadata:
        dominating_set = {
            int(dmr_id) for dmr_id, info in dmr_metadata.items() 
            if info.get('is_hub', False)
        }
    
    # Add DMR trace
    dmr_trace = create_dmr_trace(
        dmr_nodes=node_info.dmr_nodes,
        node_positions=node_positions,
        node_labels=node_labels,
        node_biclique_map=node_biclique_map,
        biclique_colors=biclique_colors,
        dominating_set=dominating_set,
        dmr_metadata=dmr_metadata
    )
    if dmr_trace:
        traces.append(dmr_trace)
    
    # Add gene traces
    gene_trace = create_gene_trace(
        gene_nodes=node_info.regular_genes,
        node_positions=node_positions,
        node_labels=node_labels,
        node_biclique_map=node_biclique_map,
        biclique_colors=biclique_colors,
        gene_metadata=gene_metadata
    )
    if gene_trace:
        traces.append(gene_trace)
        
    # Add split gene trace
    split_gene_trace = create_split_gene_trace(
        split_genes=node_info.split_genes,
        node_positions=node_positions,
        node_labels=node_labels,
        node_biclique_map=node_biclique_map,
        biclique_colors=biclique_colors,
        gene_metadata=gene_metadata
    )
    if split_gene_trace:
        traces.append(split_gene_trace)
    
    # Add edge traces
    edge_traces = create_edge_traces(
        edge_classifications,
        node_positions,
        node_labels,
        component["component"],
        edge_style={"width": 1, "color": "gray"}
    )
    traces.extend(edge_traces)
    
    # Create layout using the unified layout function
    layout = create_circular_layout(node_info)
    
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


