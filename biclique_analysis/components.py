import networkx as nx
from typing import List, Dict, Tuple
from .classifier import is_interesting_component
from visualization import (
    create_node_biclique_map,
    create_biclique_visualization,
    calculate_node_positions
)

def process_components(
    bipartite_graph: nx.Graph, 
    bicliques_result: Dict,
    dmr_metadata: Dict[str, Dict] = None,
    gene_metadata: Dict[str, Dict] = None,
    gene_id_mapping: Dict[str, int] = None
) -> Tuple[List[Dict], List[Dict]]:
    """Process connected components of the graph."""
    
    print("\nProcessing components:")  # Add debug logging
    
    # Initialize variables
    components = list(nx.connected_components(bipartite_graph))
    print(f"Found {len(components)} total components")  # Debug
    
    interesting_components = []
    simple_connections = []
    reverse_gene_mapping = {v: k for k, v in gene_id_mapping.items()} if gene_id_mapping else {}

    for idx, component in enumerate(components):
        print(f"\nProcessing component {idx + 1}:")  # Debug
        subgraph = bipartite_graph.subgraph(component)
        component_bicliques = []
        
        # Get unique DMRs and genes in this component
        dmr_nodes = {n for n in component if bipartite_graph.nodes[n]["bipartite"] == 0}
        gene_nodes = {n for n in component if bipartite_graph.nodes[n]["bipartite"] == 1}
        
        print(f"Component size: {len(component)}")  # Debug
        print(f"DMRs: {len(dmr_nodes)}, Genes: {len(gene_nodes)}")  # Debug

        # Collect component's bicliques
        component_raw_bicliques = []
        for dmr_nodes_bic, gene_nodes_bic in bicliques_result["bicliques"]:
            biclique_nodes = dmr_nodes_bic | gene_nodes_bic
            if biclique_nodes & set(component):
                component_raw_bicliques.append((dmr_nodes_bic, gene_nodes_bic))
        
        # Find split genes in this component
        gene_to_bicliques = {}
        for bidx, (_, gene_nodes_bic) in enumerate(component_raw_bicliques):
            for gene in gene_nodes_bic:
                if gene not in gene_to_bicliques:
                    gene_to_bicliques[gene] = []
                gene_to_bicliques[gene].append(bidx + 1)  # Store 1-based biclique index
        
        split_genes = {
            gene: bicliques 
            for gene, bicliques in gene_to_bicliques.items() 
            if len(bicliques) > 1
        }

        # Process bicliques for this component
        for bidx, (dmr_nodes_bic, gene_nodes_bic) in enumerate(component_raw_bicliques):
            if len(dmr_nodes_bic) >= 3 and len(gene_nodes_bic) >= 3:
                biclique_info = {
                    "dmrs": sorted(list(dmr_nodes_bic)),
                    "genes": sorted(list(gene_nodes_bic)),
                    "size": f"{len(dmr_nodes_bic)}×{len(gene_nodes_bic)}",
                    "details": {
                        "dmrs": [
                            {
                                "id": f"DMR_{dmr+1}",
                                "area": dmr_metadata.get(f"DMR_{dmr+1}", {}).get("area", "N/A"),
                                "description": dmr_metadata.get(f"DMR_{dmr+1}", {}).get("description", "N/A")
                            } 
                            for dmr in dmr_nodes_bic
                        ],
                        "genes": [
                            {
                                "name": reverse_gene_mapping.get(gene, f"Gene_{gene}"),
                                "description": gene_metadata.get(
                                    reverse_gene_mapping.get(gene, f"Gene_{gene}"), 
                                    {}
                                ).get("description", "N/A"),
                                "is_split": gene in split_genes
                            }
                            for gene in gene_nodes_bic
                        ]
                    }
                }
                component_bicliques.append(biclique_info)

        if component_bicliques:
            # Create visualization for the component
            node_biclique_map = create_node_biclique_map(component_raw_bicliques)
            node_positions = calculate_node_positions(component_raw_bicliques, node_biclique_map)
            
            # Create node labels
            node_labels = {}
            for node in component:
                if node in dmr_nodes:
                    node_labels[node] = f"DMR_{node+1}"
                else:
                    node_labels[node] = reverse_gene_mapping.get(node, f"Gene_{node}")
            
            # Generate visualization
            plotly_graph = create_biclique_visualization(
                component_raw_bicliques,
                node_labels,
                node_positions,
                node_biclique_map,
                dmr_metadata=dmr_metadata,
                gene_metadata=gene_metadata,
                gene_id_mapping=gene_id_mapping,
                bipartite_graph=subgraph
            )

            split_genes_info = [
                {
                    "gene_name": reverse_gene_mapping.get(gene, f"Gene_{gene}"),
                    "description": gene_metadata.get(
                        reverse_gene_mapping.get(gene, f"Gene_{gene}"), 
                        {}
                    ).get("description", "N/A"),
                    "bicliques": bicliques
                }
                for gene, bicliques in split_genes.items()
            ]

            component_info = {
                "id": idx + 1,
                "size": len(component),
                "dmrs": len(dmr_nodes),
                "genes": len(gene_nodes),
                "split_genes": split_genes_info,
                "bicliques": component_bicliques,
                "plotly_graph": plotly_graph,
                "total_edges": len(subgraph.edges()),  # Add this
                "raw_bicliques": [(set(bic["dmrs"]), set(bic["genes"])) for bic in component_bicliques]
            }
            interesting_components.append(component_info)
            print(f"Added interesting component with {len(component_bicliques)} bicliques")  # Debug

    print(f"\nTotal interesting components: {len(interesting_components)}")  # Debug
    return interesting_components, simple_connections
