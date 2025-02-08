"""Pure analysis functionality for bicliques."""

from typing import Dict, List, Set, Tuple
import networkx as nx
from backend.app.utils.id_mapping import create_dmr_id
from .classifier import classify_component


def analyze_bicliques(
    original_graph: nx.Graph,
    bicliques: List[Tuple[Set[int], Set[int]]],
    timepoint_id: int,
    split_graph: nx.Graph = None,
) -> Dict:
    """Analyze bicliques and components without database operations."""
    print(f"[DEBUG] analyze_bicliques: timepoint_id = {timepoint_id} (type: {type(timepoint_id)})")
    if split_graph is None:
        split_graph = nx.Graph()

    # Add edges from bicliques to split graph
    for dmr_nodes, gene_nodes in bicliques:
        split_graph.add_nodes_from(dmr_nodes, bipartite=0)
        split_graph.add_nodes_from(gene_nodes, bipartite=1)
        split_graph.add_edges_from((d, g) for d in dmr_nodes for g in gene_nodes)

    # Analyze original graph components
    original_components = []
    for component in nx.connected_components(original_graph):
        comp_subgraph = original_graph.subgraph(component)
        dmr_nodes = {create_dmr_id(n + 1, timepoint_id) for n in component if original_graph.nodes[n]["bipartite"] == 0}
        gene_nodes = {n for n in component if original_graph.nodes[n]["bipartite"] == 1}

        category = classify_component(dmr_nodes, gene_nodes, [])

        original_components.append(
            {
                "nodes": component,
                "dmr_nodes": dmr_nodes,
                "gene_nodes": gene_nodes,
                "category": category.name.lower(),
                "size": len(component),
                "edge_count": len(comp_subgraph.edges()),
                "density": 2
                * len(comp_subgraph.edges())
                / (len(component) * (len(component) - 1)),
            }
        )

    # Analyze split graph components
    split_components = []
    for component in nx.connected_components(split_graph):
        comp_subgraph = split_graph.subgraph(component)
        dmr_nodes = {create_dmr_id(n + 1, timepoint_id) for n in component if split_graph.nodes[n]["bipartite"] == 0}
        gene_nodes = {n for n in component if split_graph.nodes[n]["bipartite"] == 1}

        # Get bicliques for this component and convert DMR IDs
        comp_bicliques = [
            ({create_dmr_id(n + 1, timepoint_id) for n in dmrs}, genes)
            for (dmrs, genes) in bicliques if any(n in component for n in (dmrs | genes))
        ]
        category = classify_component(dmr_nodes, gene_nodes, comp_bicliques)

        split_components.append(
            {
                "nodes": component,
                "dmr_nodes": dmr_nodes,
                "gene_nodes": gene_nodes,
                "category": category.name.lower(),
                "bicliques": comp_bicliques,
                "size": len(component),
                "edge_count": len(comp_subgraph.edges()),
                "density": 2
                * len(comp_subgraph.edges())
                / (len(component) * (len(component) - 1)),
            }
        )

    # Convert DMR IDs in the final bicliques list
    converted_bicliques = [
        ({create_dmr_id(n + 1, timepoint_id) for n in dmrs}, genes)
        for (dmrs, genes) in bicliques
    ]

    return {
        "original_components": original_components,
        "split_components": split_components,
        "bicliques": converted_bicliques,
    }
