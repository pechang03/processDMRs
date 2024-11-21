from visualization.node_info import (
    NodeInfo,
)  # Add this line at the top with other imports

import networkx as nx
from typing import List, Dict, Tuple, Set
from biclique_analysis.statistics import calculate_biclique_statistics
from biclique_analysis.edge_classification import classify_edges
from biclique_analysis.statistics import calculate_edge_coverage
from biclique_analysis.statistics import calculate_node_participation
from biclique_analysis.classifier import (
    classify_biclique,
    classify_biclique_types,
    classify_component,  # Add this import
)
from visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    CircularBicliqueLayout,
)


def find_interesting_components(*args, **kwargs):
    """DEPRECATED: Use process_components instead."""
    import warnings
    import traceback
    warnings.warn(
        "find_interesting_components is deprecated and will be removed. Use process_components instead.",
        DeprecationWarning,
        stacklevel=2
    )
    print("Deprecation traceback:")
    traceback.print_stack()
    raise DeprecationWarning("This function is deprecated. Use process_components instead.")


import json


def convert_stats_for_json(stats):
    """Convert dictionary with tuple keys to use string keys for JSON serialization."""
    if isinstance(stats, dict):
        return {
            str(k) if isinstance(k, tuple) else k: convert_stats_for_json(v)
            for k, v in stats.items()
        }
    elif isinstance(stats, list):
        return [convert_stats_for_json(x) for x in stats]
    elif isinstance(stats, set):
        return list(stats)  # Convert sets to lists
    return stats


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


def process_components(
    bipartite_graph: nx.Graph,
    bicliques_result: Dict,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
) -> Tuple[List[Dict], List[Dict], List[Dict], Dict]:
    """Process connected components of the graph."""

    # Create biclique graph for edge classification
    biclique_graph = nx.Graph()
    for component in bicliques_result.get("interesting_components", []):
        for dmr_nodes, gene_nodes in component.get("raw_bicliques", []):
            for dmr in dmr_nodes:
                for gene in gene_nodes:
                    biclique_graph.add_edge(dmr, gene)

    # Calculate edge classifications
    # Get edge_sources from the graph's attributes
    edge_sources = getattr(bipartite_graph, "graph", {}).get("edge_sources", {})
    edge_classifications = classify_edges(bipartite_graph, biclique_graph, edge_sources)

    interesting_components = find_interesting_components(
        bipartite_graph, bicliques_result, dmr_metadata, gene_metadata, gene_id_mapping
    )

    # Only visualize first component initially
    if interesting_components:
        component_data = visualize_component(
            interesting_components[0],
            bipartite_graph,
            dmr_metadata,
            gene_metadata,
            gene_id_mapping,
            edge_classifications,  # Pass edge classifications
        )
        interesting_components[0].update(component_data)

    # Calculate comprehensive statistics using biclique_analysis.statistics
    statistics = calculate_biclique_statistics(
        bicliques_result["bicliques"], bipartite_graph
    )
    # Collect non-simple and complex components
    non_simple_components = [
        comp
        for comp in interesting_components
        if comp["category"] not in ["empty", "simple"]
    ]

    complex_components = [
        comp for comp in interesting_components if comp["category"] == "complex"
    ]

    # Update component stats with counts
    component_stats["components"]["counts"] = {
        "num_interesting_components": len(interesting_components),
        "num_non_simple_components": len(non_simple_components),
        "num_complex_components": len(complex_components),
    }

    return (
        complex_components,
        interesting_components,
        simple_connections,
        non_simple_components,
        component_stats,
        statistics,
    )
