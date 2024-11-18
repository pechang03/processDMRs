import networkx as nx
from typing import List, Dict, Tuple, Set
from visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    calculate_node_positions,
)


def find_interesting_components(
    bipartite_graph: nx.Graph,
    bicliques_result: Dict,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None,
) -> List[Dict]:
    """Find and analyze interesting components without visualization."""

    components = list(nx.connected_components(bipartite_graph))
    total_components = len(components)
    print(f"\nFound {total_components} total components")
    print(f"Processing components for analysis...")

    interesting_components = []
    reverse_gene_mapping = (
        {v: k for k, v in gene_id_mapping.items()} if gene_id_mapping else {}
    )

    # Track component statistics
    small_components = 0
    single_node_components = 0
    processed_components = 0

    for idx, component in enumerate(components):
        subgraph = bipartite_graph.subgraph(component)

        # Count single node components
        if len(component) < 2:
            single_node_components += 1
            continue

        # Get unique DMRs and genes
        dmr_nodes = {n for n in component if bipartite_graph.nodes[n]["bipartite"] == 0}
        gene_nodes = {n for n in component if bipartite_graph.nodes[n]["bipartite"] == 1}

        # Consider a component small if:
        # - It has no DMRs or no genes
        # - It has only 1 DMR and 1 gene
        # - It has only 1 DMR or only 1 gene
        if (not dmr_nodes or not gene_nodes or 
            len(dmr_nodes) <= 1 or len(gene_nodes) <= 1):
            small_components += 1
            continue

        processed_components += 1
        if processed_components % 100 == 0:
            print(f"Processed {processed_components} components...")

        component_bicliques = []
        gene_participation = {}

        for biclique_idx, (dmr_nodes_bic, gene_nodes_bic) in enumerate(
            bicliques_result["bicliques"]
        ):
            dmr_set = {int(d) if isinstance(d, str) else d for d in dmr_nodes_bic}
            gene_set = {int(g) if isinstance(g, str) else g for g in gene_nodes_bic}

            if (dmr_set | gene_set) & set(component):
                component_bicliques.append((dmr_set, gene_set))
                for gene_id in gene_set:
                    if gene_id not in gene_participation:
                        gene_participation[gene_id] = set()
                    gene_participation[gene_id].add(biclique_idx)

        regular_genes = []
        split_genes = []

        for gene_id, bicliques in gene_participation.items():
            gene_name = reverse_gene_mapping.get(gene_id, f"Gene_{gene_id}")
            gene_info = {
                "gene_name": gene_name,
                "description": gene_metadata.get(gene_name, {}).get("description", "N/A"),
                "bicliques": sorted(list(bicliques)),
            }

            if len(bicliques) > 1:
                split_genes.append(gene_info)
            else:
                regular_genes.append(gene_info)

        if len(component_bicliques) >= 1:
            component_info = {
                "id": idx + 1,
                "size": len(component),
                "dmrs": len(dmr_nodes),
                "genes": len(regular_genes),
                "regular_genes": regular_genes,
                "component": component,
                "raw_bicliques": component_bicliques,
                "total_edges": len(subgraph.edges()),
                "split_genes": split_genes,
                "total_genes": len(regular_genes) + len(split_genes),
            }
            interesting_components.append(component_info)

    # Print detailed summary statistics
    print(f"\nComponent Analysis Summary:")
    print(f"Total components found: {total_components}")
    print(f"Single node components: {single_node_components}")
    print(f"Small components (≤1 DMR or ≤1 gene): {small_components}")
    print(f"Interesting components (>1 DMR and >1 gene): {len(interesting_components)}")
    
    if interesting_components:
        print("\nInteresting Component Statistics:")
        print(f"Average DMRs per component: {sum(c['dmrs'] for c in interesting_components)/len(interesting_components):.1f}")
        print(f"Average genes per component: {sum(c['total_genes'] for c in interesting_components)/len(interesting_components):.1f}")
        print(f"Components with split genes: {sum(1 for c in interesting_components if c['split_genes'])}")

    return interesting_components


def visualize_component(
    component_info: Dict,
    bipartite_graph: nx.Graph,
    dmr_metadata: Dict[str, Dict],
    gene_metadata: Dict[str, Dict],
    gene_id_mapping: Dict[str, int],
    edge_classification: Dict[str, Set[Tuple[int, int]]] = None,  # Add this parameter
) -> Dict:  # Change return type to Dict to include both visualization and data
    """Create visualization and data summary for a specific component."""

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

    # Create visualization
    node_biclique_map = create_node_biclique_map(component_info["raw_bicliques"])
    node_positions = calculate_node_positions(
        component_info["raw_bicliques"], node_biclique_map
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
        node_biclique_map,
        original_graph=bipartite_graph,  # Original full graph
        bipartite_graph=subgraph,  # Graph from component bicliques
        dmr_metadata=dmr_metadata,
        gene_metadata=gene_metadata,
        gene_id_mapping=gene_id_mapping,
        edge_classification=edge_classification,  # Pass edge classifications
    )

    return {
        "visualization": plotly_graph,
        "bicliques": biclique_data,
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
) -> Tuple[List[Dict], List[Dict], Dict]:
    """Process connected components of the graph."""

    # Create biclique graph for edge classification
    biclique_graph = nx.Graph()
    for component in bicliques_result.get("interesting_components", []):
        for dmr_nodes, gene_nodes in component.get("raw_bicliques", []):
            for dmr in dmr_nodes:
                for gene in gene_nodes:
                    biclique_graph.add_edge(dmr, gene)

    # Calculate edge classifications
    from biclique_analysis.edge_classification import classify_edges
    edge_classifications = classify_edges(bipartite_graph, biclique_graph)

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

    # Calculate detailed component statistics
    components = list(nx.connected_components(bipartite_graph))
    total_components = len(components)
    single_node_components = sum(1 for comp in components if len(comp) == 1)
    small_components = total_components - len(interesting_components) - single_node_components

    statistics = {
        "components": {
            "total": total_components,
            "single_node": single_node_components,
            "small": small_components,
            "interesting": len(interesting_components),
            "avg_dmrs": sum(c['dmrs'] for c in interesting_components) / len(interesting_components) if interesting_components else 0,
            "avg_genes": sum(c['total_genes'] for c in interesting_components) / len(interesting_components) if interesting_components else 0,
            "with_split_genes": sum(1 for c in interesting_components if c.get('split_genes')),
            "total_split_genes": sum(len(c.get('split_genes', [])) for c in interesting_components),
            "total_bicliques": sum(len(c.get('raw_bicliques', [])) for c in interesting_components)
        }
    }

    return interesting_components, [], statistics

