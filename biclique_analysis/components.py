from visualization.node_info import NodeInfo  # Add this line at the top with other imports

import networkx as nx
from typing import List, Dict, Tuple, Set
from biclique_analysis.statistics import calculate_biclique_statistics
from visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    CircularBicliqueLayout,
)


def classify_component(dmr_count: int, gene_count: int, bicliques: List) -> str:
    """Classify component based on hierarchy."""
    if dmr_count == 0 or gene_count == 0:
        return "empty"
    if dmr_count == 1 and gene_count == 1:
        return "simple"
        
    # Check if any biclique is interesting
    has_interesting_biclique = any(
        len(dmr_nodes) >= 3 and len(gene_nodes) >= 3 
        for dmr_nodes, gene_nodes in bicliques
    )
    
    if has_interesting_biclique:
        # Check for complexity (multiple interesting bicliques or split genes)
        interesting_biclique_count = sum(
            1 for dmr_nodes, gene_nodes in bicliques 
            if len(dmr_nodes) >= 3 and len(gene_nodes) >= 3
        )
        if interesting_biclique_count > 1:
            return "complex"
        return "interesting"
    
    return "normal"

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
    
    # Initialize counters for each category
    category_counts = {
        "empty": 0,
        "simple": 0,
        "normal": 0,
        "interesting": 0,
        "complex": 0
    }
    
    interesting_components = []
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()} if gene_id_mapping else {}

    for idx, component in enumerate(components):
        subgraph = bipartite_graph.subgraph(component)
        
        # Get unique DMRs and genes
        dmr_nodes = {n for n in component if bipartite_graph.nodes[n]["bipartite"] == 0}
        gene_nodes = {n for n in component if bipartite_graph.nodes[n]["bipartite"] == 1}
        
        # Find all bicliques for this component
        component_bicliques = []
        gene_participation = {}
        
        for biclique_idx, (dmr_nodes_bic, gene_nodes_bic) in enumerate(bicliques_result["bicliques"]):
            dmr_set = {int(d) if isinstance(d, str) else d for d in dmr_nodes_bic}
            gene_set = {int(g) if isinstance(g, str) else g for g in gene_nodes_bic}
            
            if (dmr_set | gene_set) & set(component):
                component_bicliques.append((dmr_set, gene_set))
                for gene_id in gene_set:
                    if gene_id not in gene_participation:
                        gene_participation[gene_id] = set()
                    gene_participation[gene_id].add(biclique_idx)

        # Classify the component
        category = classify_component(len(dmr_nodes), len(gene_nodes), component_bicliques)
        category_counts[category] += 1
        
        # Process genes
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

        component_info = {
            "id": idx + 1,
            "category": category,
            "size": len(component),
            "dmrs": len(dmr_nodes),
            "genes": len(regular_genes),
            "regular_genes": regular_genes,
            "component": component,
            "raw_bicliques": component_bicliques,
            "total_edges": len(subgraph.edges()),
            "split_genes": split_genes,
            "total_genes": len(regular_genes) + len(split_genes),
            "interesting_bicliques": [
                (dmr_nodes, gene_nodes) 
                for dmr_nodes, gene_nodes in component_bicliques
                if len(dmr_nodes) >= 3 and len(gene_nodes) >= 3
            ]
        }
        
        # Keep all components for analysis, but mark interesting ones
        if category in ["interesting", "complex"]:
            interesting_components.append(component_info)

    # Print detailed summary
    print("\nComponent Classification Summary:")
    for category, count in category_counts.items():
        print(f"{category.capitalize()}: {count}")
    
    print("\nInteresting and Complex Components:")
    for comp in interesting_components:
        print(f"\nComponent {comp['id']} ({comp['category']}):")
        print(f"Total: {comp['dmrs']} DMRs, {comp['total_genes']} Genes")
        print(f"Interesting bicliques: {len(comp['interesting_bicliques'])}")
        print(f"Split genes: {len(comp['split_genes'])}")

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
            dmr_nodes={n for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 0},
            regular_genes={n for n, d in bipartite_graph.nodes(data=True) if d["bipartite"] == 1},
            split_genes=set(),
            node_degrees={n: len(list(bipartite_graph.neighbors(n))) for n in bipartite_graph.nodes()},
            min_gene_id=min(results.get("gene_id_mapping", {}).values(), default=0),
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
        bipartite_graph,       # Required positional arg
        subgraph,              # Required positional arg
        dmr_metadata=dmr_metadata,
        gene_metadata=gene_metadata,
        gene_id_mapping=gene_id_mapping
    )

    return {
        "visualization": plotly_graph,
        "bicliques": biclique_data,
        "statistics": statistics,
        "edge_coverage": edge_coverage,
        "node_participation": node_participation,
        "biclique_types": type_counts,
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
    # Get edge_sources from the graph's attributes
    edge_sources = getattr(bipartite_graph, 'graph', {}).get('edge_sources', {})
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
    statistics = calculate_biclique_statistics(bicliques_result["bicliques"], bipartite_graph)

    return interesting_components, [], statistics

