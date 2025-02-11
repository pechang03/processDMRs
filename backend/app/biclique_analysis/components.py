from typing import List, Dict, Tuple, Set
import networkx as nx
import networkx as nx
import json

from backend.app.utils.node_info import NodeInfo
from backend.app.biclique_analysis.statistics import (
    calculate_biclique_statistics,
    calculate_edge_coverage,
    calculate_node_participation,
    analyze_components,
    calculate_size_distribution,
    calculate_coverage_statistics,
)
from backend.app.utils.json_utils import (
    convert_stats_for_json,
    convert_all_for_json,
    convert_sets_to_lists,
)
from backend.app.biclique_analysis.edge_classification import classify_edges
from backend.app.biclique_analysis.classifier import (
    BicliqueSizeCategory,
    classify_biclique,
    classify_component,
    classify_biclique_types,
)
from backend.app.visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    CircularBicliqueLayout,
)
from .component_analyzer import ComponentAnalyzer
from .triconnected import analyze_triconnected_components


def find_interesting_components(*args, **kwargs):
    """DEPRECATED: Use process_components instead."""
    import warnings
    import traceback

    warnings.warn(
        "find_interesting_components is deprecated and will be removed. Use process_components instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    print("Deprecation traceback:")
    traceback.print_stack()
    raise DeprecationWarning(
        "This function is deprecated. Use process_components instead."
    )


def visualize_component(
    component_info: Dict,
    bipartite_graph: nx.Graph,
    dmr_metadata: Dict[str, Dict],
    gene_metadata: Dict[str, Dict],
    gene_id_mapping: Dict[str, int],
    edge_classification: Dict[str, Set[Tuple[int, int]]] = None,  # Add this parameter
) -> Dict:  # Change return type to Dict to include both visualization and data
    """Create visualization and data summary for a specific component."""

    # Calculate statistics first
    biclique_stats = calculate_biclique_statistics(
        component_info["raw_bicliques"], bipartite_graph
    )
    print("\nBiclique Statistics:")
    print(json.dumps(convert_stats_for_json(biclique_stats), indent=2))

    edge_coverage_stats = calculate_edge_coverage(
        component_info["raw_bicliques"], bipartite_graph
    )
    print("\nEdge Coverage Statistics:")
    print(json.dumps(edge_coverage_stats, indent=2))

    node_participation_stats = calculate_node_participation(
        component_info["raw_bicliques"]
    )
    print("\nNode Participation Statistics:")
    print(json.dumps(node_participation_stats, indent=2))

    biclique_type_stats = classify_biclique_types(component_info["raw_bicliques"])
    print("\nBiclique Type Statistics:")
    print(json.dumps(biclique_type_stats, indent=2))

    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()}
    subgraph = bipartite_graph.subgraph(component_info["component"])

    # Create node labels
    node_labels = {}
    for node in component_info["component"]:
        if bipartite_graph.nodes[node]["bipartite"] == 0:
            # For DMRs, use DMR_1 format
            dmr_label = f"DMR_{node+1}"
            node_labels[node] = dmr_label
        else:
            # For genes, use actual gene name from reverse mapping
            gene_name = reverse_gene_mapping.get(node)
            if gene_name:
                node_labels[node] = gene_name
            else:
                node_labels[node] = f"Gene_{node}"

    # Calculate node positions for the original graph using spring embedding
    original_node_positions = nx.spring_layout(bipartite_graph)

    # Create visualization
    node_biclique_map = create_node_biclique_map(component_info["raw_bicliques"])
    # Use CircularBicliqueLayout for biclique visualization
    layout = CircularBicliqueLayout()
    node_positions = layout.calculate_positions(
        bipartite_graph,
        NodeInfo(
            all_nodes=set(bipartite_graph.nodes()),
            dmr_nodes={
                n for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 0
            },
            regular_genes={
                n for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 1
            },
            split_genes=set(),
            node_degrees={
                n: len(list(bipartite_graph.neighbors(n)))
                for n in bipartite_graph.nodes()
            },
            min_gene_id=min(gene_id_mapping.values(), default=0),
        ),
    )

    # Generate biclique summary data
    biclique_data = []
    for idx, (dmr_nodes, gene_nodes) in enumerate(component_info["raw_bicliques"]):
        # Get DMR details
        dmrs = []
        for dmr_id in sorted(dmr_nodes):
            dmr_label = f"DMR_{dmr_id+1}"
            if dmr_label in dmr_metadata:
                dmrs.append(
                    {
                        "id": dmr_label,
                        "area": dmr_metadata[dmr_label].get("area", "N/A"),
                        "description": dmr_metadata[dmr_label].get(
                            "description", "N/A"
                        ),
                    }
                )

        # Get gene details
        genes = []
        split_genes = []
        for gene_id in sorted(gene_nodes):
            gene_name = reverse_gene_mapping.get(gene_id, f"Gene_{gene_id}")
            gene_info = {
                "name": gene_name,
                "description": gene_metadata.get(gene_name, {}).get(
                    "description", "N/A"
                ),
            }
            # Check if it's a split gene (appears in multiple bicliques)
            if len(node_biclique_map.get(gene_id, [])) > 1:
                split_genes.append(gene_info)
            else:
                genes.append(gene_info)

        biclique_data.append(
            {
                "id": idx + 1,
                "dmrs": dmrs,
                "genes": genes,
                "split_genes": split_genes,
                "size": {
                    "dmrs": len(dmr_nodes),
                    "genes": len(gene_nodes),
                    "split_genes": len(split_genes),
                },
            }
        )

        """
    # Create visualization
    plotly_graph = create_biclique_visualization(
        component_info["raw_bicliques"],
        node_labels,
        node_positions,
        node_biclique_map,  # Required positional arg
        edge_classification,  # Required positional arg
        bipartite_graph,  # Required positional arg
        subgraph,  # Required positional arg
        dmr_metadata=dmr_metadata,
        gene_metadata=gene_metadata,
        gene_id_mapping=gene_id_mapping,
    )

    return {
        "visualization": plotly_graph,
        "bicliques": biclique_data,
        "statistics": biclique_stats,
        "edge_coverage": edge_coverage_stats,
        "node_participation": node_participation_stats,
        "biclique_types": biclique_type_stats,
        "summary": {
            "component_id": component_info["id"],
            "total_nodes": component_info["size"],
            "total_dmrs": component_info["dmrs"],
            "total_genes": component_info["genes"],
            "total_edges": component_info["total_edges"],
            "total_bicliques": len(component_info["raw_bicliques"]),
        },
    }
"""


def analyze_biconnected_components(graph: nx.Graph) -> Tuple[List[Set], Dict]:
    """Find and analyze biconnected components of a graph."""
    # Get biconnected components
    biconn_comps = list(nx.biconnected_components(graph))

    # Use analyze_components from statistics.py
    stats = analyze_components(biconn_comps, graph)

    return biconn_comps, stats


def analyze_connected_components(graph: nx.Graph) -> Tuple[List[Set], Dict]:
    """Find and analyze connected components of a graph."""
    # Get connected components
    conn_comps = list(nx.connected_components(graph))

    # Use analyze_components from statistics.py
    stats = analyze_components(conn_comps, graph)

    return conn_comps, stats


def generate_component_description(
    dmr_nodes: Set[int],
    gene_nodes: Set[int],
    bicliques: List[Tuple[Set[int], Set[int]]],
    category: BicliqueSizeCategory,
) -> str:
    """Generate a human-readable description of the component."""
    if category == BicliqueSizeCategory.EMPTY:
        return "Empty component with no connections"

    if category == BicliqueSizeCategory.SIMPLE:
        return f"Simple component with {len(dmr_nodes)} DMR(s) connected to {len(gene_nodes)} gene(s)"

    if category == BicliqueSizeCategory.INTERESTING:
        return (
            f"Interesting component containing {len(dmr_nodes)} DMRs and {len(gene_nodes)} genes "
            f"forming {len(bicliques)} biclique(s)"
        )

    if category == BicliqueSizeCategory.COMPLEX:
        split_genes = {gene for biclique in bicliques for gene in biclique[1]} - set(
            bicliques[0][1]
        )
        return (
            f"Complex component with {len(dmr_nodes)} DMRs and {len(gene_nodes)} genes, "
            f"including {len(split_genes)} split genes across {len(bicliques)} bicliques"
        )

    return "Unknown component type"


def convert_sets_to_lists(data):
    """Convert any sets in the data structure to lists recursively."""
    if isinstance(data, dict):
        return {k: convert_sets_to_lists(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_sets_to_lists(i) for i in data]
    elif isinstance(data, set):
        return sorted(list(data))
    elif isinstance(data, tuple):
        return list(data)
    return data


def process_components(
    bipartite_graph: nx.Graph,
    bicliques_result: Dict,
    biclique_graph: nx.Graph,  # Now receives the graph to populate
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
    dominating_set: Set[int] = None,
) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], Dict, Dict]:
    """
    Call stack:
    1. process_timepoint
    2. process_bicliques
    3. [process_components] (YOU ARE HERE)
    4. ComponentAnalyzer.analyze_components
    5. enrich_component_metadata (internal)
    6. visualize_component (for first component)
    
    Process connected components of the graph.
    """
    # Initialize component lists
    complex_components = []
    interesting_components = []
    simple_components = []
    non_simple_components = []

    # Process each biclique and add to biclique_graph
    if bicliques_result and "bicliques" in bicliques_result:
        for dmr_nodes, gene_nodes in bicliques_result["bicliques"]:
            # Add nodes and edges to the passed biclique_graph
            biclique_graph.add_nodes_from(dmr_nodes, bipartite=0)
            biclique_graph.add_nodes_from(gene_nodes, bipartite=1)
            biclique_graph.add_edges_from(
                (dmr, gene) for dmr in dmr_nodes for gene in gene_nodes
            )

    # Create analyzer with both graphs
    analyzer = ComponentAnalyzer(bipartite_graph, bicliques_result, biclique_graph)
    component_stats = analyzer.analyze_components(dominating_set)
    
    def enrich_component_metadata(component_info: Dict) -> Dict:
        """Add rich metadata to a component."""
        # Get bicliques for this component
        component_bicliques = [b for b in bicliques_result["bicliques"] if any(node in component_info['component'] for node in b[0] | b[1])]
        
        # Calculate biclique-related statistics
        component_info.update({
            "biclique_stats": {
                "total": len(component_bicliques),
                "size_distribution": calculate_size_distribution(component_bicliques),
                "coverage": calculate_coverage_statistics(component_bicliques, bipartite_graph),
                "edge_coverage": calculate_edge_coverage(component_bicliques, bipartite_graph),
                "node_participation": calculate_node_participation(component_bicliques),
                "types": classify_biclique_types(component_bicliques)
            },
            "split_genes": [
                gene for gene in component_info.get('component', set()) 
                if bipartite_graph.nodes[gene].get('bipartite') == 1 
                and len([b for b in component_bicliques if gene in b[1]]) > 1
            ],
            "edge_classifications": classify_edges(
                bipartite_graph.subgraph(component_info['component']),
                biclique_graph.subgraph(component_info['component']),
                {}  # Add edge sources if available
            )
        })
        
        return component_info

    # Process individual components
    for idx, component_data in enumerate(bicliques_result.get("components", [])):
        if isinstance(component_data, dict):
            interesting_components.append(component_data)
        else:
            # Process raw component data
            dmr_nodes, gene_nodes = component_data
            category = classify_component(
                dmr_nodes, gene_nodes, [(dmr_nodes, gene_nodes)]
            )

            # Generate component description
            description = generate_component_description(
                dmr_nodes, gene_nodes, [(dmr_nodes, gene_nodes)], category
            )

            component_info = {
                "id": idx + 1,
                "component": dmr_nodes | gene_nodes,
                "dmrs": len(dmr_nodes),
                "genes": len(gene_nodes),
                "size": len(dmr_nodes) + len(gene_nodes),
                "total_edges": sum(1 for dmr in dmr_nodes for gene in gene_nodes),
                "raw_bicliques": [(dmr_nodes, gene_nodes)],
                "category": category.name.lower(),
                "description": description,
            }

            # Categorize component
            if category == BicliqueSizeCategory.SIMPLE:
                simple_components.append(component_info)
            elif category == BicliqueSizeCategory.INTERESTING:
                component_info = enrich_component_metadata(component_info)
                interesting_components.append(component_info)
            elif category == BicliqueSizeCategory.COMPLEX:
                component_info = enrich_component_metadata(component_info)
                complex_components.append(component_info)
            
            if category not in [BicliqueSizeCategory.EMPTY, BicliqueSizeCategory.SIMPLE]:
                non_simple_components.append(component_info)

    # Calculate comprehensive statistics
    statistics = calculate_biclique_statistics(
        bicliques_result["bicliques"], bipartite_graph
    )

    # Only visualize first component initially
    if interesting_components:
        component_data = visualize_component(
            interesting_components[0],
            bipartite_graph,
            dmr_metadata,
            gene_metadata,
            gene_id_mapping,
            analyzer.get_edge_classifications(),
        )
        interesting_components[0].update(component_data)

    return (
        complex_components,
        interesting_components,
        simple_components,  # Now properly populated
        non_simple_components,
        component_stats,
        statistics,
    )
